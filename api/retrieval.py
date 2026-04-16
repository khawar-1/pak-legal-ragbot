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
    """Return a formatted list of random/shuffled unique case titles + brief snippets from FAISS."""
    import random
    vector_db = _get_vector_db()
    seen_journals, case_pool = set(), []

    if hasattr(vector_db, "docstore") and hasattr(vector_db.docstore, "_dict"):
        docs = list(vector_db.docstore._dict.values())
        random.shuffle(docs) # Shuffle so users see different cases when they ask for "more"
        
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
            case_pool.append((journal, parties, court, snippet))
            if len(case_pool) >= limit:
                break

    if not case_pool:
        return "I couldn't retrieve case listings right now. Please try asking about a specific citation."

    lines = ["Here are some property law cases available in my knowledge base:\n"]
    for i, (journal, parties, court, snippet) in enumerate(case_pool, 1):
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
    Property Law Bot — three-mode pipeline:

    MODE A  — Specific case lookup (citation detected)
              → Search FAISS, answer from retrieved documents.

    MODE B  — User wants examples / a list of cases
              → Return case titles + snippets directly from FAISS docstore.

    MODE C  — General property law question  (default)
              → Answer from Groq's own knowledge.
              → Reject out-of-domain questions gracefully.
    """
    import re

    # ── Build enriched FAISS query for short follow-ups ──────────────────────
    faiss_query = user_input
    if chat_history:
        last_user_msgs = [m.get("message", "") for m in chat_history if m.get("sender") == "User"]
        if last_user_msgs and len(user_input.split()) <= 10:
            faiss_query = last_user_msgs[-1] + " " + user_input
            logger.info(f"Enriched FAISS query: {faiss_query}")

    # ── Detect intent ─────────────────────────────────────────────────────────
    # Citation pattern: e.g. "2008 CLC 332", "PLD 2005 123", "1998 MLD 45"
    citation_re = re.search(
        r'\b(?:PLD|CLC|MLD|SCMR|PTD|YLR|AIR)\s*\d{4}|\b\d{4}\s+(?:PLD|CLC|MLD|SCMR|PTD|YLR|AIR)\s+\d+',
        faiss_query, re.IGNORECASE
    )
    has_citation = bool(citation_re)

    example_keywords = [
        "example", "examples", "list", "some cases", "show cases", "give case",
        "case title", "what cases", "available cases", "which cases", "any cases",
        "cases available", "cases in", "cases you have", "cases do you have",
        "more cases", "tell me some more", "show me more", "give me more"
    ]
    wants_examples = any(kw in user_input.lower() for kw in example_keywords)

    # ── Shared resources ──────────────────────────────────────────────────────
    history_block = _format_history_block(chat_history)
    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.0,
        max_tokens=700,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # MODE A — Specific case lookup
    # ═══════════════════════════════════════════════════════════════════════════
    if has_citation:
        logger.info("MODE A: Citation detected — looking up case in FAISS knowledge base...")
        docs, context = _faiss_case_lookup(faiss_query)

        if not docs:
            return (
                "This specific case is not in my knowledge base. "
                "You can ask me to list available property cases so you can pick one to explore.",
                ""
            )

        case_prompt = f"""You are a Pakistani property law assistant. Answer ONLY from the case context below.

{history_block}<context>
{context}
</context>

Question: {user_input}

Rules:
- Answer CONCISELY from the context (4-6 sentences max).
- Mention the case reference, court, date, parties, and the key legal principle decided.
- You may use the previous conversation to understand follow-up questions.
- Never invent details not present in the context.

Answer:"""
        response = llm.invoke(case_prompt)
        return response.content.strip(), context

    # ═══════════════════════════════════════════════════════════════════════════
    # MODE B — List available cases from knowledge base
    # ═══════════════════════════════════════════════════════════════════════════
    elif wants_examples:
        logger.info("MODE B: Listing cases from FAISS docstore...")
        listing = _list_cases_from_faiss(limit=8)
        return listing, ""

    # ═══════════════════════════════════════════════════════════════════════════
    # MODE C — General property question: FAISS first, Groq fallback
    # ═══════════════════════════════════════════════════════════════════════════
    else:
        logger.info("MODE C: Semantic FAISS search first, Groq fallback if not relevant...")

        # Step 1: Semantic search in knowledge base
        vector_db = _get_vector_db()
        semantic_docs = vector_db.as_retriever(search_kwargs={"k": 3}).invoke(faiss_query)
        context = "\n\n".join(d.page_content for d in semantic_docs)
        if len(context) > MAX_CONTEXT_CHARS:
            context = context[:MAX_CONTEXT_CHARS] + "\n\n[Context truncated]"

        # Step 2: Ask LLM to answer from FAISS context if relevant,
        # signal NO_RELEVANT_CONTEXT if not, or OUT_OF_DOMAIN if off-topic.
        rag_prompt = f"""You are a Pakistani property law assistant. Your domain is STRICTLY property law.

{history_block}Here is content retrieved from the knowledge base that may be relevant:
<context>
{context}
</context>

User question: {user_input}

STRICT RULES — respond with ONLY ONE of these:
1. If the question is NOT about property law → respond with exactly: OUT_OF_DOMAIN
2. If the context above is clearly relevant to the question → answer using those case(s) as reference.
   - Keep the answer concise (4-6 sentences).
   - Cite the relevant case reference(s) from the context (e.g. "In 2008 CLC 332...").
   - Do NOT invent details not present in the context.
3. If the context is NOT relevant to the question → respond with exactly: NO_RELEVANT_CONTEXT

Answer:"""

        response = llm.invoke(rag_prompt)
        answer = response.content.strip()

        # Domain rejection
        if "OUT_OF_DOMAIN" in answer:
            return (
                "I'm a **Pakistani property law assistant** and can only help with property-related queries — "
                "land, ownership, tenancy, transfer of property, mortgage, preemption, possession disputes, etc. "
                "For other legal matters, please consult a relevant specialist.",
                ""
            )

        # FAISS had nothing relevant → fall back to Groq general knowledge
        if "NO_RELEVANT_CONTEXT" in answer:
            logger.info("FAISS context not relevant — falling back to Groq general knowledge...")
            fallback_prompt = f"""You are a Pakistani property law assistant specializing in Pakistani property law.
Your domain is ONLY property law: land, real estate, ownership, tenancy, rent, transfer of property,
mortgages, easements, preemption, possession disputes, inheritance of property, property registration, etc.

{history_block}Answer the following question using your general knowledge of Pakistani property law.
Be concise (3-5 sentences). Do NOT invent specific case citations or dates.

Question: {user_input}

Answer:"""
            fallback = llm.invoke(fallback_prompt)
            return fallback.content.strip(), ""

        # FAISS had relevant context — return the grounded answer
        return answer, context
