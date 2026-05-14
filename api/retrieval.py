from langchain_community.vectorstores.faiss import FAISS
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_groq import ChatGroq
from .config import KNOWLEDGE_BASE_PATH, GROQ_API_KEY, GROQ_MODEL, HUGGINGFACE_API_TOKEN
import time
import os
import json
import re
import logging
from typing import List, Optional, Dict, Any, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# OPTIMIZATION 1: Context char cap reduced 25000 → 12000 (~3000 tokens)
MAX_CONTEXT_CHARS = 12000

FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index")

_cached_embeddings = None

# ── Domain knowledge lists ─────────────────────────────────────────────────────

# Short inputs matching any of these are ALWAYS answered directly (never flagged vague)
ALWAYS_ANSWER_TERMS = [
    "preemption", "pre-emption", "mortgage", "tenancy", "easement",
    "adverse possession", "riparian", "nuisance", "covenant", "estoppel",
    "foreclosure", "leasehold", "freehold", "deed", "probate",
    "inheritance", "partition", "mutation", "registry", "lease", "rent",
    "eviction", "injunction", "stay order", "specific performance",
    "title", "possession", "ownership", "transfer", "sale", "purchase",
    "preempt", "khula", "hiba", "waqf", "musha",
]

LEGAL_KEYWORDS = [
    "property", "land", "tenant", "mortgage", "transfer", "deed",
    "possession", "preemption", "ownership", "court", "case", "law",
    "dispute", "title", "lease", "rent", "sale", "purchase", "inheritance",
    "partition", "mutation", "registry", "eviction", "injunction",
    "landlord", "buyer", "seller", "right", "claim", "suit", "decree",
    "judgment", "appeal", "section", "act", "statute", "legal",
]

AMBIGUOUS_PRONOUN_RE = re.compile(
    r'\b(he|she|it|they|them|his|her|its|their|this|that|these|those)\b',
    re.IGNORECASE,
)

# Maps number words/digits → 0-based list index for option resolution
_OPTION_INDEX_MAP = {
    "1": 0, "one": 0, "first": 0, "1st": 0,
    "2": 1, "two": 1, "second": 1, "2nd": 1,
    "3": 2, "three": 2, "third": 2, "3rd": 2,
}


# ── Embeddings & vector DB ─────────────────────────────────────────────────────

def _get_embeddings():
    """Get or create the HuggingFace embeddings instance (free, no daily quota)."""
    global _cached_embeddings
    if _cached_embeddings is None:
        _cached_embeddings = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            task="feature-extraction",
            huggingfacehub_api_token=HUGGINGFACE_API_TOKEN,
        )
    return _cached_embeddings


def _load_documents_from_json(json_path):
    """Load legal cases from the structured JSON dataset.

    OPTIMIZATION 2: Slim metadata header — journal + parties only.
    """
    from langchain_core.documents import Document

    logger.info(f"Loading cases from JSON dataset: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    documents = []
    for case in cases:
        journal = case.get("journal", "").strip()
        parties = case.get("parties", "").strip()
        court   = case.get("court", "").strip()
        header  = f"[{journal} | {parties}]\n"

        chunks = case.get("chunks", [])
        if chunks:
            for chunk in chunks:
                chunk_text = chunk.get("chunk_text", "").strip()
                if chunk_text:
                    documents.append(
                        Document(
                            page_content=header + chunk_text,
                            metadata={"journal": journal, "court": court,
                                      "parties": parties, "source": case.get("file_name", "")},
                        )
                    )
        else:
            judgment = case.get("judgment_text", "").strip()
            if judgment:
                documents.append(
                    Document(
                        page_content=header + judgment,
                        metadata={"journal": journal, "court": court,
                                  "parties": parties, "source": case.get("file_name", "")},
                    )
                )

    logger.info(f"Loaded {len(documents)} document chunks from {len(cases)} cases.")
    return documents


def _get_vector_db():
    """Get or create the FAISS vector database from disk."""
    embeddings = _get_embeddings()

    if os.path.exists(FAISS_INDEX_PATH):
        logger.info("Loading existing FAISS vector database from disk...")
        return FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

    logger.info("FAISS index not found. Building from scratch (first time only)...")
    texts = _load_documents_from_json(KNOWLEDGE_BASE_PATH)
    logger.info(f"Embedding {len(texts)} chunks with HuggingFace...")

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
                    vector_db.merge_from(FAISS.from_documents(batch, embeddings))
                break
            except Exception as e:
                logger.warning(f"Error: {e}. Retrying in 10 seconds...")
                time.sleep(10)
                retries += 1
        time.sleep(1)

    logger.info("Vector database built! Saving to disk...")
    vector_db.save_local(FAISS_INDEX_PATH)
    logger.info("Saved! Future startups will load instantly from disk.")
    return vector_db


# ── Query helpers ──────────────────────────────────────────────────────────────

def _is_context_relevant(context: str, user_input: str) -> bool:
    """Heuristic: is retrieved context likely relevant?"""
    if not context or len(context.strip()) < 100:
        return False
    citation_match = re.search(r'\b(?:19|20)\d{2}\s+[A-Z]+\s+\d+\b', user_input, re.IGNORECASE)
    if citation_match:
        return citation_match.group(0).upper() in context.upper()
    return True


def _format_history_block(chat_history):
    """Format last few exchanges into a compact text block for the prompt."""
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

    exact_docs = []
    if hasattr(vector_db, "docstore") and hasattr(vector_db.docstore, "_dict"):
        for doc in vector_db.docstore._dict.values():
            journal = doc.metadata.get("journal", "").strip().upper()
            if journal and journal in query_upper:
                exact_docs.append(doc)
    exact_docs = exact_docs[:3]

    semantic_docs = vector_db.as_retriever(search_kwargs={"k": 3}).invoke(faiss_query)

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
        docs = list(vector_db.docstore._dict.values())
        random.shuffle(docs)
        for doc in docs:
            journal = doc.metadata.get("journal", "").strip()
            parties = doc.metadata.get("parties", "").strip()
            court   = doc.metadata.get("court", "").strip()
            if not journal or journal in seen_journals:
                continue
            seen_journals.add(journal)
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


# ── Master RAG prompt ──────────────────────────────────────────────────────────

def _run_master_prompt(user_input: str, context: str, chat_history: list, llm) -> str:
    """Run the master RAG prompt and return the final answer string.
    Converts sentinel codes ([UNSAFE] etc.) into human-readable responses.
    """
    history_block = _format_history_block(chat_history)
    master_prompt = f"""You are a Pakistani property law assistant.
Your domain is STRICTLY property law (land, ownership, tenancy, transfer of property, mortgages, preemption, possession disputes, etc.) WITHIN Pakistan.

{history_block}<context>
{context}
</context>

User question: {user_input}

STRICT INSTRUCTIONS: Choose EXACTLY ONE of the following paths based on the user's question:

1. SAFETY FILTER: If the user's question asks for anything harmful, unethical, illegal, or inappropriate, respond with EXACTLY and ONLY this text:
   [UNSAFE]

2. CHIT-CHAT: If the question is pure conversational pleasantry (e.g., "Hi", "Hello", "How are you?"), respond warmly and briefly in character as a legal assistant. Do NOT output any tag or label — just write the response directly.

3. DOMAIN STRICT FILTER: If the user asks a legal question NOT related to property law (e.g., criminal law, family law), respond with EXACTLY and ONLY this text:
   [OUT_OF_DOMAIN]

4. GEOGRAPHIC FILTER (CRITICAL): If the user's question mentions or implies ANY foreign country, foreign city, or foreign jurisdiction (e.g., India, Delhi, USA, UK, Dubai, etc.), respond with EXACTLY and ONLY this text:
   [OUT_OF_COUNTRY]

5. ANSWERING LOGIC (For Pakistani property law ONLY):
   - ANSWER DIRECTLY. DO NOT prepend greetings, pleasantries, or introduce yourself.
   - First, check if the provided <context> contains relevant information. If it does, USE IT as your primary reference and cite the case details provided.
   - If the <context> does NOT contain relevant information, fallback and answer using your own general knowledge of Pakistani property law. Do NOT use Indian, UK, or other foreign laws.
   - Provide a DETAILED and COMPREHENSIVE answer spanning around 2-3 paragraphs.
   - NEVER invent case citations, dates, or non-existent legal statutes.

Answer:"""

    response = llm.invoke(master_prompt)
    answer = response.content.strip()

    # Strip any leaked format tags the LLM may prefix its answer with
    answer = re.sub(r'^\s*\[CHIT-CHAT\]\s*', '', answer, flags=re.IGNORECASE).strip()
    answer = re.sub(r'^\s*\[ANSWER\]\s*', '', answer, flags=re.IGNORECASE).strip()

    if "[UNSAFE]" in answer:
        return "I cannot fulfill that request. Please keep questions respectful, ethical, and within the boundaries of the law."
    if "[OUT_OF_DOMAIN]" in answer:
        return (
            "I'm a **Pakistani property law assistant** and can only help with property-related queries — "
            "land, ownership, tenancy, transfer of property, mortgage, preemption, possession disputes, etc. "
            "For other legal matters like criminal or family law, please consult a relevant specialist."
        )
    if "[OUT_OF_COUNTRY]" in answer:
        return "I am a **Pakistani property law assistant**. I can only provide information and guidance regarding property laws, regulations, and cases within Pakistan. I cannot help with property matters in other countries."

    return answer


# ── Vagueness detection ────────────────────────────────────────────────────────

def _is_domain_short_answer(user_input: str) -> bool:
    """Return True if the input, however short, is a known property law term."""
    normalised = user_input.strip().lower()
    return any(term in normalised for term in ALWAYS_ANSWER_TERMS)


def _classify_vagueness(user_input: str, chat_history: list) -> dict:
    """Classify whether a query is too vague to answer well.

    Returns: { "is_vague": bool, "reason": str | None }

    Rule priority (first match wins):
    1. Domain short answer                        → NOT vague
    2. ≤ 3 words, no history                     → vague  (too_short)
    3. Pronoun + no legal kw + no history         → vague  (ambiguous_pronoun)
    4. No legal kw, < 8 words, no history         → vague  (no_domain_keyword)
    5. Personal situation statement with no       → vague  (situation_statement)
       specific legal question, no history
    6. Anything else                              → NOT vague
    """
    if _is_domain_short_answer(user_input):
        logger.info("Vagueness: domain term → answering directly.")
        return {"is_vague": False, "reason": None}

    words = user_input.strip().split()
    has_history = bool(chat_history)
    has_legal_kw = any(kw in user_input.lower() for kw in LEGAL_KEYWORDS)

    if len(words) <= 3 and not has_history:
        logger.info("Vagueness: too short, no history.")
        return {"is_vague": True, "reason": "too_short"}

    has_pronoun = bool(AMBIGUOUS_PRONOUN_RE.search(user_input))
    if has_pronoun and not has_legal_kw and not has_history:
        logger.info("Vagueness: ambiguous pronoun, no legal keyword, no history.")
        return {"is_vague": True, "reason": "ambiguous_pronoun"}

    if not has_legal_kw and len(words) < 8 and not has_history:
        logger.info("Vagueness: no domain keyword in short query.")
        return {"is_vague": True, "reason": "no_domain_keyword"}

    # Rule 5: Personal situation statement with legal keywords but no specific legal question.
    # e.g. "I have dispute over land", "My property is taken", "We have a problem with tenant"
    # These describe a situation but don't ask what they need legally — must clarify.
    QUESTION_SIGNALS = [
        "how", "what", "when", "where", "who", "which", "why",
        "can i", "could i", "should i", "is it", "are there",
        "do i", "will i", "am i", "please explain", "tell me",
        "explain", "define", "describe",
    ]
    SITUATION_STMT_RE = re.compile(
        r'^\s*(i have|i had|i want|i need|i am|i got|i lost|'
        r'my |we have|we had|we want|we need|our |'
        r'my brother|my father|my mother|my sister|my land|my property)',
        re.IGNORECASE,
    )
    is_situation_stmt = bool(SITUATION_STMT_RE.search(user_input))
    has_question_signal = any(q in user_input.lower() for q in QUESTION_SIGNALS)
    if is_situation_stmt and not has_question_signal and len(words) < 15 and not has_history:
        logger.info("Vagueness: situation statement without specific legal question.")
        return {"is_vague": True, "reason": "situation_statement"}

    return {"is_vague": False, "reason": None}


def _generate_options_via_llm(
    user_input: str,
    chat_history: list,
    reason: str,
    clarification_round: int = 1,
    llm=None,
) -> List[str]:
    """Generate 3 selectable option strings via Groq.

    On round >= 2 (chained vagueness), returns a single simple open question instead.
    """
    if llm is None:
        llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.3, max_tokens=300)

    history_block = _format_history_block(chat_history)

    if clarification_round >= 2:
        prompt = (
            f"You are a Pakistani property law assistant.\n"
            f"The user has been unclear twice. Ask ONE very simple, direct question to understand what they need.\n"
            f"User's latest message: \"{user_input}\"\n"
            f"Output ONLY the question, nothing else."
        )
        response = llm.invoke(prompt)
        return [response.content.strip()]

    prompt = (
        f"You are a Pakistani property law assistant.\n"
        f"The user asked a vague property law question. Vagueness reason: {reason}.\n"
        f"{history_block}"
        f"User's message: \"{user_input}\"\n\n"
        f"Generate EXACTLY 3 specific, short option phrases (NOT questions) that represent the most likely things the user could mean.\n"
        f"Each option must be about a distinct property law topic.\n"
        f"Format: one option per line, plain text only, no numbering, no bullet points, no extra text.\n"
        f"Example format:\n"
        f"Ownership or title dispute over land\n"
        f"Landlord and tenant conflict or eviction\n"
        f"Mortgage or property transfer issue"
    )
    response = llm.invoke(prompt)
    options = [line.strip() for line in response.content.strip().split("\n") if line.strip()][:3]

    if not options:
        options = [
            "Ownership or title dispute over land or property",
            "Landlord-tenant conflict, rent, or eviction",
            "Mortgage, transfer, or property registration issue",
        ]
    return options


def _build_clarification_message(options: List[str], clarification_round: int = 1) -> str:
    """Build the clarification message shown to the user."""
    if clarification_round >= 2 and len(options) == 1:
        return f"I'm still not quite sure what you need. {options[0]}"
    intro = "I want to make sure I give you the right information. Are you asking about:"
    option_lines = "\n".join(f"- **{opt}**" for opt in options)
    outro = "\nJust pick one or tell me in your own words."
    return f"{intro}\n\n{option_lines}\n{outro}"


def _resolve_option_selection(user_reply: str, options_offered: List[str]) -> str:
    """Map a user's selection reply to the actual option text.

    Handles: "2", "second", "two", "2nd" → options_offered[1].
    Falls back to the raw user reply if no index match is found.
    """
    if not options_offered:
        return user_reply

    reply_lower = user_reply.strip().lower()
    for token in reply_lower.split():
        clean = re.sub(r"[^a-z0-9]", "", token)
        if clean in _OPTION_INDEX_MAP:
            idx = _OPTION_INDEX_MAP[clean]
            if idx < len(options_offered):
                resolved = options_offered[idx]
                logger.info(f"Option resolved: '{user_reply}' → '{resolved}'")
                return resolved

    return user_reply


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def retrieval(
    user_input: str,
    chat_history: Optional[List[Dict[str, Any]]] = None,
    clarification_state: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str, List[str], bool]:
    """Property Law Bot — Unified Pipeline.

    Returns:
        (answer, context, options, is_vague)
        - answer:   Text to display to the user.
        - context:  Raw FAISS context (empty string for vague/bypass paths).
        - options:  Selectable option strings (non-empty only when is_vague=True).
        - is_vague: True if the bot asked for clarification; False otherwise.

    MODE 0 — Pending Clarification:
        User replied to a previous clarification. Resolve their selection,
        build an enriched query, and run RAG. Skip vagueness detection.

    MODE 1 — List Cases Bypass:
        User asked for example cases → return listing directly from FAISS.

    MODE 2 — Vagueness Gate:
        Query is too vague → generate options and return clarification message.

    MODE 3 — Master RAG Pipeline:
        Standard FAISS lookup + LLM answering.
    """
    if chat_history is None:
        chat_history = []
    if clarification_state is None:
        clarification_state = {}

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.0,
        max_tokens=1000,
    )

    # ── MODE 0: Pending clarification path ────────────────────────────────────
    if clarification_state.get("pending"):
        original_query = clarification_state.get("original_query", "")
        options_offered = clarification_state.get("options_offered", [])
        current_round   = clarification_state.get("round", 1)

        resolved_selection = _resolve_option_selection(user_input, options_offered)

        # Build enriched query: original vague intent + user's resolved selection
        enriched_query = f"{original_query} {resolved_selection}".strip()
        logger.info(f"MODE 0: Pending clarification resolved. Enriched query: {enriched_query}")

        # Check if the user is STILL vague (chained vagueness) and we are within round limit
        vagueness = _classify_vagueness(resolved_selection, chat_history)
        if vagueness["is_vague"] and current_round < 2:
            next_round = current_round + 1
            options = _generate_options_via_llm(
                user_input, chat_history, vagueness["reason"],
                clarification_round=next_round, llm=llm,
            )
            msg = _build_clarification_message(options, clarification_round=next_round)
            logger.info(f"MODE 0→2: User still vague, escalating to round {next_round}.")
            return msg, "", options, True

        # User gave a usable answer — run RAG on enriched query
        docs, context = _faiss_case_lookup(enriched_query)
        answer = _run_master_prompt(enriched_query, context, chat_history, llm)
        return answer, context, [], False

    # ── Build enriched FAISS query for short follow-ups (existing optimisation) ─
    faiss_query = user_input
    if chat_history:
        last_user_msgs = [m.get("message", "") for m in chat_history if m.get("sender") == "User"]
        if last_user_msgs and len(user_input.split()) <= 10:
            faiss_query = last_user_msgs[-1] + " " + user_input
            logger.info(f"Enriched FAISS query: {faiss_query}")

    # ── MODE 1: List cases bypass ──────────────────────────────────────────────
    example_keywords = [
        "example", "examples", "list", "some cases", "show cases", "give case",
        "case title", "what cases", "available cases", "which cases", "any cases",
        "cases available", "cases in", "cases you have", "cases do you have",
    ]
    if any(kw in user_input.lower() for kw in example_keywords):
        logger.info("MODE 1: Listing cases from FAISS docstore...")
        listing = _list_cases_from_faiss(limit=8)
        return listing, "", [], False

    # ── MODE 2: Vagueness gate ─────────────────────────────────────────────────
    vagueness = _classify_vagueness(user_input, chat_history)
    if vagueness["is_vague"]:
        logger.info(f"MODE 2: Vague query detected. Reason: {vagueness['reason']}")
        options = _generate_options_via_llm(
            user_input, chat_history, vagueness["reason"],
            clarification_round=1, llm=llm,
        )
        msg = _build_clarification_message(options, clarification_round=1)
        return msg, "", options, True

    # ── MODE 3: Master RAG pipeline ────────────────────────────────────────────
    logger.info("MODE 3: Searching FAISS and running master prompt...")
    docs, context = _faiss_case_lookup(faiss_query)
    answer = _run_master_prompt(user_input, context, chat_history, llm)
    return answer, context, [], False
