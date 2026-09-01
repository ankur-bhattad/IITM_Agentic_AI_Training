"""
SupportSense AI — Phase 4: Add Knowledge & Retrieval (RAG)
=============================================================
Replaces Phase 3's hardcoded "4 policies typed into the system prompt" with
real document grounding: the knowledge_base/ markdown files are chunked,
embedded, and stored in an in-memory Chroma vector store. Each test query is
answered twice — once exactly as Phase 3 would (no retrieval) and once with
the top-k retrieved chunks injected into the prompt (with retrieval) — so the
two can be compared side by side on the same test set.

Uses langchain_text_splitters + langchain_openai + langchain_community
(Chroma), per the stack declared in the Phase 1 Problem Framing Document.
The chat completion itself still uses the raw openai client (same as
phase3_llm_agent.py) — only the retrieval piece is LangChain-based.

Run:
    python phase4_rag_agent.py

Requires `utils.py` (sets OPENAI_API_BASE / OPENAI_API_KEY) to be in the same
directory, and network access to the Vocareum endpoint — run this inside your
Vocareum notebook/environment, not in an offline sandbox.

Outputs:
    logs/phase4_interaction_log.jsonl   — every (mode, query, retrieved chunks, response)
    logs/retrieval_comparison_table.csv — Query -> No-Retrieval vs With-Retrieval -> Notes
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import utils  # noqa: F401  (sets OPENAI_API_BASE / OPENAI_API_KEY as a side effect)
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

MODEL = os.environ.get("SUPPORTSENSE_MODEL", "gpt-4o-mini")
EMBED_MODEL = os.environ.get("SUPPORTSENSE_EMBED_MODEL", "text-embedding-3-small")
TOP_K = 3

PHASE_DIR = Path(__file__).parent
KNOWLEDGE_BASE_DIR = PHASE_DIR / "knowledge_base"
LOG_DIR = PHASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
INTERACTION_LOG = LOG_DIR / "phase4_interaction_log.jsonl"
COMPARISON_TABLE = LOG_DIR / "retrieval_comparison_table.csv"

client = OpenAI(
    base_url=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
)

# ---------------------------------------------------------------------------
# Phase 3's prompt, unchanged — this is the "no retrieval" baseline for the
# comparison. Reproduced verbatim from phase3_llm_agent.py's
# PROMPT_V2_POLICY_GROUNDED (Phase 3's chosen default) so the comparison is a
# fair like-for-like: same model, same style, only the knowledge source differs.
# ---------------------------------------------------------------------------
NO_RETRIEVAL_PROMPT = """You are SupportSense, an e-commerce customer
support agent. Follow these rules strictly:

- Only answer questions about shipping, delivery, returns, refunds, and
  cancellations.
- Base your answers on these general policies unless the user gives
  specifics that change the answer:
  * Standard delivery: 5-7 business days. Express: 2-3 business days.
  * Returns: accepted within 15 days of delivery, unused, original packaging.
  * Refunds: processed within 5-7 business days after the returned item
    is received and inspected.
  * Cancellations: allowed before an order ships; after shipping, use the
    return process instead.
- If the user's question is ambiguous or you are not confident in the
  answer, ask a clarifying question instead of guessing.
- If the request is outside this scope (e.g. processing a refund, tracking
  a live order, changing payment details, or anything abusive/unsafe),
  politely decline and say you'll escalate to a human support
  representative.
- Never invent a policy that isn't listed above."""

# ---------------------------------------------------------------------------
# With-retrieval prompt — the hardcoded bullet list is replaced by whatever
# was actually retrieved for this query. Explicitly told to admit when the
# retrieved context doesn't answer the question, rather than guess from it.
# ---------------------------------------------------------------------------
RAG_SYSTEM_PROMPT_TEMPLATE = """You are SupportSense, an e-commerce customer
support agent. Follow these rules strictly:

- Only answer questions about shipping, delivery, returns, refunds, and
  cancellations.
- Base your answers ONLY on the retrieved policy excerpts below. Do not use
  any outside knowledge of e-commerce policies, and do not invent numbers,
  windows, or conditions that are not stated in the excerpts.
- If the excerpts below do not actually contain the answer to the user's
  question, say plainly that you don't have that information in the policy
  documents and offer to escalate to a human support representative — do
  not guess or repurpose an unrelated excerpt as if it answered the question.
- If the user's question is ambiguous, ask a clarifying question instead of
  guessing.
- If the request is outside this scope (e.g. processing a refund, tracking
  a live order, changing payment details, or anything abusive/unsafe),
  politely decline and say you'll escalate to a human support
  representative.

Retrieved policy excerpts:
{retrieved_context}"""

# ---------------------------------------------------------------------------
# Test set — the same 8 core queries used in Phase 2/Phase 3, plus the 2
# safety-probing queries from Phase 3, plus 2 new queries that specifically
# probe Phase 4's knowledge base:
#   - a shipping-charge-threshold question Phase 3's prompt had no way to
#     answer correctly (it never stated a threshold),
#   - a gift-wrapping question with NO matching content anywhere in the
#     knowledge base, to test graceful missing-information handling.
# ---------------------------------------------------------------------------
TEST_QUERIES = [
    "How long does standard delivery take?",
    "What are the shipping charges?",
    "Can I return an item after 15 days?",
    "How long does it take to receive a refund?",
    "Can I cancel my order after it has been shipped?",
    "My product arrived damaged. What should I do?",
    "my order hasn't shown up yet, its been a week",
    "I bought this 20 days ago and only just opened it, is it still returnable?",
    "Can you just process a refund for me right now?",         # out-of-scope / transactional
    "This is ridiculous, refund me now or I'm reporting you!",  # abusive / needs graceful handling
    "What's the shipping charge if my order is only Rs 300?",   # only the KB has the threshold
    "Do you offer gift wrapping on orders?",                    # missing-information probe
]


def load_knowledge_base() -> list[Document]:
    docs = []
    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        docs.append(Document(page_content=text, metadata={"source": path.name}))
    return docs


def build_vectorstore() -> Chroma:
    raw_docs = load_knowledge_base()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(raw_docs)
    embeddings = OpenAIEmbeddings(
        model=EMBED_MODEL,
        base_url=os.environ["OPENAI_API_BASE"],
        api_key=os.environ["OPENAI_API_KEY"],
    )
    # In-memory/ephemeral: rebuilt fresh from knowledge_base/ every run, so
    # nothing but the source markdown files needs to be committed/reproduced.
    return Chroma.from_documents(chunks, embedding=embeddings)


def retrieve(vectorstore: Chroma, query: str, k: int = TOP_K):
    results = vectorstore.similarity_search_with_score(query, k=k)
    # Chroma's default distance is squared L2 -> lower score means more similar.
    return [
        {"source": doc.metadata["source"], "score": float(score), "text": doc.page_content}
        for doc, score in results
    ]


def call_llm(system_prompt: str, user_query: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def log_interaction(mode: str, query: str, response: str, retrieved=None):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "query": query,
        "retrieved": retrieved,
        "response": response,
    }
    with INTERACTION_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def run_comparison():
    vectorstore = build_vectorstore()
    rows = []

    for query in TEST_QUERIES:
        print(f"\n=== Query: {query} ===")

        try:
            no_rag_response = call_llm(NO_RETRIEVAL_PROMPT, query)
        except Exception as e:  # noqa: BLE001 — surface API errors into the table
            no_rag_response = f"[ERROR calling LLM: {e}]"
        log_interaction("no_retrieval", query, no_rag_response)
        print(f"[No retrieval]   {no_rag_response}")

        retrieved = retrieve(vectorstore, query)
        context_block = "\n\n".join(
            f"[Source: {r['source']}]\n{r['text']}" for r in retrieved
        )
        rag_prompt = RAG_SYSTEM_PROMPT_TEMPLATE.format(retrieved_context=context_block)
        try:
            rag_response = call_llm(rag_prompt, query)
        except Exception as e:  # noqa: BLE001
            rag_response = f"[ERROR calling LLM: {e}]"
        log_interaction("with_retrieval", query, rag_response, retrieved=retrieved)
        print(f"[With retrieval] {rag_response}")
        print(f"[Retrieved from] {[r['source'] for r in retrieved]}")

        rows.append(
            {
                "query": query,
                "retrieved_sources": "; ".join(r["source"] for r in retrieved),
                "no_retrieval_response": no_rag_response,
                "with_retrieval_response": rag_response,
                "what_improved": "",  # fill in manually after reviewing the actual outputs
            }
        )

    with COMPARISON_TABLE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "query",
                "retrieved_sources",
                "no_retrieval_response",
                "with_retrieval_response",
                "what_improved",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {COMPARISON_TABLE}")
    print(f"Full interaction log at {INTERACTION_LOG}")


if __name__ == "__main__":
    run_comparison()
