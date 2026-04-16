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

# OPTIMIZATION 1: Context char cap reduced 25000 → 12000 (~3000 tokens, was ~6200)
MAX_CONTEXT_CHARS = 12000

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

    OPTIMIZATION 2: Slim metadata header — journal + parties only.
    Was 6 fields (journal, court, date, parties, statutes, lawyers).
    Saves ~100-150 tokens per chunk × 4 chunks = ~400-600 tokens per request.
    """
    from langchain_core.documents import Document

    logger.info(f"Loading cases from JSON dataset: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    documents = []
    for case in cases:
        journal  = case.get("journal", "").strip()
        parties  = case.get("parties", "").strip()
        court    = case.get("court", "").strip()

        # Slim header: only the two most identifying fields
        header = f"[{journal} | {parties}]\n"

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


def _is_context_relevant(context: str, user_input: str) -> bool:
    """
    Heuristic check: is the retrieved context likely relevant to the query?
    Returns False if context looks empty or only has generic chunks.
    """
    if not context or len(context.strip()) < 100:
        return False

    # If the query contains a citation-like pattern, check if it appears in the context
    import re
    citation_match = re.search(r'\b(?:19|20)\d{2}\s+[A-Z]+\s+\d+\b', user_input, re.IGNORECASE)
    if citation_match:
        citation = citation_match.group(0).upper()
        return citation in context.upper()

    return True  # For general questions, assume context is relevant


def retrieval(user_input, chat_history=None):
    logger.info("Getting vector DB (will load from disk if available)...")
    vector_db = _get_vector_db()

    logger.info("Retrieving relevant documents for your query...")

    # EXACT MATCH HEURISTIC: Find cases where the journal is exactly in the query
    exact_match_docs = []
    query_upper = user_input.upper()

    if hasattr(vector_db, "docstore") and hasattr(vector_db.docstore, "_dict"):
        for doc_id, doc in vector_db.docstore._dict.items():
            journal = doc.metadata.get("journal", "").strip().upper()
            if journal and journal in query_upper:
                exact_match_docs.append(doc)

    exact_match_docs = exact_match_docs[:2]

    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    semantic_docs = retriever.invoke(user_input)

    # Combine exact matches and semantic matches, removing duplicates
    all_docs = []
    seen_content = set()
    for doc in exact_match_docs + semantic_docs:
        if doc.page_content not in seen_content:
            all_docs.append(doc)
            seen_content.add(doc.page_content)

    relevant_docs = all_docs[:4]

    # Format context from documents
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n[Context truncated]"

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.0,
        max_tokens=400,
    )

    # Format last 2 exchanges (4 messages max) as a concise history block
    history_block = ""
    if chat_history:
        lines = []
        for msg in chat_history:
            sender = msg.get("sender", "Unknown")
            text   = msg.get("message", "").strip()
            # Keep history short: cap each message at 300 chars
            if len(text) > 300:
                text = text[:300] + "..."
            lines.append(f"{sender}: {text}")
        if lines:
            history_block = "Previous conversation (last 2 exchanges):\n" + "\n".join(lines) + "\n\n"

    # STEP 1: Try answering from the FAISS knowledge base first
    rag_prompt = f"""You are a Pakistan legal assistant. Answer ONLY from the context below.

{history_block}<context>
{context}
</context>

Question: {user_input}

Rules:
- Use ONLY the context above.
- You may use the previous conversation to understand follow-up questions.
- If not found, say exactly: "I don't have that information in my knowledge base."
- Never invent case citations, dates, or legal principles.

Answer:"""

    logger.info("Calling Groq LLM (FAISS knowledge base)...")
    response = llm.invoke(rag_prompt)
    answer = response.content.strip()

    # STEP 2: If the FAISS knowledge base didn't have the answer, fall back to
    # the LLM's own general knowledge about Pakistani law, but add a disclaimer.
    NOT_FOUND_PHRASE = "I don't have that information in my knowledge base"
    if NOT_FOUND_PHRASE.lower() in answer.lower():
        logger.info("FAISS had no answer — falling back to LLM general knowledge with disclaimer.")
        fallback_prompt = f"""You are a Pakistan legal assistant. The user asked a question that is not covered in the local legal case files.

{history_block}Answer the question using your own knowledge of Pakistani law. You MUST start your answer with this disclaimer on its own line:
"⚠️ This is not in my case files. Based on general Pakistani legal principles:"

Then provide a helpful, accurate answer. Do not invent specific case citations or dates.

Question: {user_input}

Answer:"""
        fallback_response = llm.invoke(fallback_prompt)
        return fallback_response.content, context

    return answer, context