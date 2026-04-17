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


def _format_history_block(chat_history):
    """Format the last few exchanges into a compact text block for the prompt."""
    if not chat_history:
        return ""
    lines = []
    for msg in chat_history:
        sender = msg.get("sender", "Unknown")
        text = msg.get("message", "").strip()
        if len(text) > 200:
            text = text[:200] + "..."
        lines.append(f"{sender}: {text}")
    return "Previous conversation:\n" + "\n".join(lines) + "\n\n" if lines else ""


def _faiss_case_lookup(faiss_query: str):
    """Search FAISS for a specific case. Returns (docs, context_string)."""
    vector_db = _get_vector_db()
    query_upper = faiss_query.upper()

    # Exact match on journal reference first
    exact_docs = []
    if hasattr(vector_db, "docstore") and hasattr(vector_db.docstore, "_dict"):
        for doc in vector_db.docstore._dict.values():
            journal = doc.metadata.get("journal", "").strip().upper()
            if journal and journal in query_upper:
                exact_docs.append(doc)
    exact_docs = exact_docs[:3]

    # Semantic fallback
    semantic_docs = vector_db.as_retriever(search_kwargs={"k": 3}).invoke(faiss_query)

    # Merge, deduplicate, cap at 4
    seen, all_docs = set(), []
    for doc in exact_docs + semantic_docs:
        if doc.page_content not in seen:
            all_docs.append(doc)
            seen.add(doc.page_content)
    all_docs = all_docs[:4]

    context = "\n\n".join(d.page_content for d in all_docs)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n[Context truncated]"
    return all_docs, context


def _list_cases_from_faiss(limit: int = 8) -> str:
    """Return a formatted list of unique case titles + brief snippets from FAISS."""
    import random
    vector_db = _get_vector_db()
    seen_journals, case_list = set(), []

    if hasattr(vector_db, "docstore") and hasattr(vector_db.docstore, "_dict"):
        # Shuffle documents to provide different examples each time
        docs = list(vector_db.docstore._dict.values())
        random.shuffle(docs)
        
        for doc in docs:
            journal = doc.metadata.get("journal", "").strip()
            parties = doc.metadata.get("parties", "").strip()
            court   = doc.metadata.get("court", "").strip()
            if not journal or journal in seen_journals:
                continue
            seen_journals.add(journal)
            # Grab a brief snippet (skip the header line)
            content_lines = doc.page_content.split("\n")
            snippet_lines = [l for l in content_lines[1:] if l.strip()]
            snippet = " ".join(snippet_lines)[:130]
            if len(snippet) == 130:
                snippet += "..."
            case_list.append((journal, parties, court, snippet))
            if len(case_list) >= limit:
                break

    if not case_list:
        return "I couldn't retrieve case listings right now. Please try asking about a specific citation."

    lines = ["Here are some property law cases available in my knowledge base:\n"]
    for i, (journal, parties, court, snippet) in enumerate(case_list, 1):
        lines.append(f"{i}. **{journal}**")
        if parties:
            lines.append(f"   Parties: {parties}")
        if court:
            lines.append(f"   Court: {court}")
        if snippet:
            lines.append(f"   Summary: {snippet}")
        lines.append("")
    lines.append("Ask me about any of these cases for a detailed explanation.")
    return "\n".join(lines)


def retrieval(user_input, chat_history=None):
    """
    Property Law Bot — Unified Pipeline:

    MODE 1: List Cases Bypass
            → If user asks for examples, return available cases directly from FAISS.

    MODE 2: Master RAG Pipeline
            → Always search FAISS first.
            → Use a Master Prompt to enforce Safety, Domain Restriction, Chit-chat, and Answering logic.
    """
    # ── Build enriched FAISS query for short follow-ups ──────────────────────
    faiss_query = user_input
    if chat_history:
        last_user_msgs = [m.get("message", "") for m in chat_history if m.get("sender") == "User"]
        if last_user_msgs and len(user_input.split()) <= 10:
            faiss_query = last_user_msgs[-1] + " " + user_input
            logger.info(f"Enriched FAISS query: {faiss_query}")

    # ── Detect intent (Mode 1 bypass) ─────────────────────────────────────────
    example_keywords = [
        "example", "examples", "list", "some cases", "show cases", "give case",
        "case title", "what cases", "available cases", "which cases", "any cases",
        "cases available", "cases in", "cases you have", "cases do you have"
    ]
    wants_examples = any(kw in user_input.lower() for kw in example_keywords)

    if wants_examples:
        logger.info("MODE 1: Listing cases from FAISS docstore...")
        listing = _list_cases_from_faiss(limit=8)
        return listing, ""

    # ── Shared resources ──────────────────────────────────────────────────────
    history_block = _format_history_block(chat_history)
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.0,
        max_tokens=1000,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # MODE 2 — Master RAG Pipeline
    # ═══════════════════════════════════════════════════════════════════════════
    logger.info("MODE 2: Always searching FAISS first...")
    docs, context = _faiss_case_lookup(faiss_query)

    master_prompt = f"""You are a Pakistani property law assistant. 
Your domain is STRICTLY property law (land, ownership, tenancy, transfer of property, mortgages, preemption, possession disputes, etc.).

{history_block}<context>
{context}
</context>

User question: {user_input}

STRICT INSTRUCTIONS: Choose EXACTLY ONE of the following paths based on the user's question:

1. SAFETY FILTER: If the user's question asks for anything harmful, unethical, illegal, or inappropriate, respond with EXACTLY and ONLY this text:
   [UNSAFE]

2. CHIT-CHAT: If the question is pure conversational pleasantry (e.g., "Hi", "Hello", "How are you?"), answer politely and briefly in character. Do not provide legal advice here.

3. DOMAIN STRICT FILTER: If the user asks a legal question NOT related to property law (e.g., criminal law, family law), respond with EXACTLY and ONLY this text:
   [OUT_OF_DOMAIN]

4. ANSWERING LOGIC (For property law questions ONLY):
   - ANSWER DIRECTLY. DO NOT prepend greetings, pleasantries, or introduce yourself. Skip phrases like "Assalamu alaikum" or "I am a legal assistant".
   - First, check if the provided <context> contains relevant information. If it does, USE IT as your primary reference and cite the case details provided.
   - If the <context> does NOT contain relevant information, seamlessly fallback and answer using your own general knowledge of Pakistani property law.
   - Provide a DETAILED and COMPREHENSIVE answer. Give full explanations, span around 2-3 paragraphs.
   - NEVER invent case citations, dates, or non-existent legal statutes.

Answer:"""

    logger.info("Calling Groq LLM (Master prompt)...")
    response = llm.invoke(master_prompt)
    answer = response.content.strip()

    # Handle rejection codes
    if "[UNSAFE]" in answer:
        return (
            "I cannot fulfill that request. Please keep questions respectful, ethical, and within the boundaries of the law.",
            ""
        )
    
    if "[OUT_OF_DOMAIN]" in answer:
        return (
            "I'm a **Pakistani property law assistant** and can only help with property-related queries — "
            "land, ownership, tenancy, transfer of property, mortgage, preemption, possession disputes, etc. "
            "For other legal matters like criminal or family law, please consult a relevant specialist.",
            ""
        )

    return answer, context
