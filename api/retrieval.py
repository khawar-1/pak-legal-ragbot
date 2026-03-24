from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_groq import ChatGroq
from .config import KNOWLEDGE_BASE_PATH, GROQ_API_KEY, GROQ_MODEL, HUGGINGFACE_API_TOKEN
import time
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Maximum characters for context passed to LLM (~4k tokens)
MAX_CONTEXT_CHARS = 25000

# Path to save the FAISS index locally
FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index")

_cached_embeddings = None

def _get_embeddings():
    """Get or create the HuggingFace embeddings instance (free, no daily quota)."""
    global _cached_embeddings
    if _cached_embeddings is None:
        _cached_embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            task="feature-extraction",
            huggingfacehub_api_token=HUGGINGFACE_API_TOKEN
        )
    return _cached_embeddings

def _load_documents_from_json(json_path):
    """Load legal cases from the structured JSON dataset.
    
    Each case chunk gets a rich metadata header so the LLM always knows
    which case the text belongs to.
    """
    from langchain_core.documents import Document

    logger.info(f"Loading cases from JSON dataset: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    documents = []
    for case in cases:
        # Build a clear metadata header for every chunk
        journal  = case.get("journal", "").strip()
        court    = case.get("court", "").strip()
        date     = case.get("date", "").strip()
        parties  = case.get("parties", "").strip()
        statutes = case.get("statutes", "").strip()
        lawyers  = case.get("lawyers", "").strip()

        header = (
            f"CASE REFERENCE: {journal}\n"
            f"COURT: {court}\n"
            f"DATE: {date}\n"
            f"PARTIES: {parties}\n"
            f"STATUTES: {statutes}\n"
            f"LAWYERS: {lawyers}\n"
            f"---\n"
        )

        # Use the pre-built chunks from the JSON (already ~500 words each)
        chunks = case.get("chunks", [])
        if chunks:
            for chunk in chunks:
                chunk_text = chunk.get("chunk_text", "").strip()
                if chunk_text:
                    content = header + chunk_text
                    documents.append(Document(
                        page_content=content,
                        metadata={
                            "journal": journal,
                            "court": court,
                            "parties": parties,
                            "source": case.get("file_name", ""),
                        }
                    ))
        else:
            # Fallback: use full judgment_text if no chunks present
            judgment = case.get("judgment_text", "").strip()
            if judgment:
                content = header + judgment
                documents.append(Document(
                    page_content=content,
                    metadata={
                        "journal": journal,
                        "court": court,
                        "parties": parties,
                        "source": case.get("file_name", ""),
                    }
                ))

    logger.info(f"Loaded {len(documents)} document chunks from {len(cases)} cases.")
    return documents

def _get_vector_db():
    """Get or create the FAISS vector database from disk."""
    embeddings = _get_embeddings()
    
    # If the index exists on disk, load it instantly (0 API calls).
    if os.path.exists(FAISS_INDEX_PATH):
        logger.info("Loading existing FAISS vector database from disk...")
        return FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    
    logger.info("FAISS index not found on disk. Building from scratch (first time only)...")
    
    # Load documents from the structured JSON
    texts = _load_documents_from_json(KNOWLEDGE_BASE_PATH)
    
    logger.info(f"Embedding {len(texts)} chunks with HuggingFace (free, no quota limits)...")
    
    # Build vector DB in batches
    batch_size = 100
    vector_db = None
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(texts) + batch_size - 1) // batch_size
        logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
        
        retries = 0
        while retries < 5:
            try:
                if vector_db is None:
                    vector_db = FAISS.from_documents(batch, embeddings)
                else:
                    batch_db = FAISS.from_documents(batch, embeddings)
                    vector_db.merge_from(batch_db)
                break
            except Exception as e:
                logger.warning(f"Error: {e}. Retrying in 10 seconds...")
                time.sleep(10)
                retries += 1
        
        # Small delay between batches
        time.sleep(1)
    
    logger.info("Vector database built successfully! Saving to disk...")
    vector_db.save_local(FAISS_INDEX_PATH)
    logger.info("Saved! Future startups will load instantly from disk.")
    return vector_db


def retrieval(user_input):
    logger.info("Getting vector DB (will load from disk if available)...")
    vector_db = _get_vector_db()
    
    logger.info("Retrieving relevant documents for your query...")
    
    # EXACT MATCH HEURISTIC: Find cases where the journal is exactly in the query
    exact_match_docs = []
    query_upper = user_input.upper()
    
    if hasattr(vector_db, "docstore") and hasattr(vector_db.docstore, "_dict"):
        for doc_id, doc in vector_db.docstore._dict.items():
            journal = doc.metadata.get("journal", "").strip().upper()
            
            # If the user query exactly mentions a non-empty journal (e.g. "1996 PLD 149")
            if journal and journal in query_upper:
                exact_match_docs.append(doc)
    
    # Limit exact matches so we don't blow up context
    exact_match_docs = exact_match_docs[:4]
    
    # Semantic Search for conceptually similar chunks
    retriever = vector_db.as_retriever(search_kwargs={"k": 6})
    semantic_docs = retriever.invoke(user_input)
    
    # Combine exact matches and semantic matches, removing duplicates
    all_docs = []
    seen_content = set()
    for doc in exact_match_docs + semantic_docs:
        if doc.page_content not in seen_content:
            all_docs.append(doc)
            seen_content.add(doc.page_content)
    
    # Keep only the top 8 chunks total to avoid LLM token limits
    relevant_docs = all_docs[:8]
    
    # Format context from documents
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n[Context truncated for length]"
    
    # Define the prompt template - STRICT grounding to prevent hallucination
    prompt = f"""You are a strict Pakistan Legal Case Assistant. 
Your ONLY source of knowledge is the XML <context> provided below.

<context>
{context}
</context>

USER QUESTION:
{user_input}

INSTRUCTIONS:
1. You MUST answer the user's question using ONLY the <context> above.
2. If the <context> does not contain the answer, you MUST respond EXACTLY with: "I don't have that information in my knowledge base."
3. NEVER invent, hallucinate, or guess case names, citation numbers (like PLD, MLD, CLC), dates, or legal principles from your outside training data.
4. If the user asks you to list or name cases, ONLY list the `CASE REFERENCE:` and `PARTIES:` blocks that physically appear inside the <context> tags above. DO NOT name any other cases.

ANSWER (using ONLY the <context>):
"""
    
    # Use Groq (free) for the smart answer generation
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.0,
    )
    
    logger.info("Calling Groq LLM for final answer...")
    response = llm.invoke(prompt)
    
    return response.content, context