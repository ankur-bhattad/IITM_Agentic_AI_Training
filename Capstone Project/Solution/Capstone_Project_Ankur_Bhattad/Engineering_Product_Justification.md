# Engineering & Product Justification — SupportSense AI

This is the Engineering & Product Justification required by the capstone submission checklist. It
synthesizes the design decisions, tradeoffs, safety approach, and deployment assumptions made
across the 9-phase build (`Solution/phase_2` through `Solution/phase_9`), and reconciles the final
system against what `Problem Framing Document.docx` originally specified. It assumes the reader has
that document and `phase9_evaluation_report.md` at hand, and cites specific files rather than
restating their contents.

## 1. Product summary

**SupportSense AI** is a Track A (framework-based, LangChain), Scenario 3 (Customer Support) agent
for an online shopper who wants a fast, accurate answer about shipping, delivery, returns,
refunds, or cancellations without waiting for a human — and a safe handoff to a human when the
question is ambiguous, sensitive, or outside what the agent is allowed to do (`Problem Framing
Document.docx`, sections 1-3). The out-of-scope list is deliberately strict: the agent never
tracks live orders, modifies/cancels orders, processes refunds, or touches payment information —
it explains policy and computes eligibility, and hands off everything transactional.

## 2. Final architecture

```
Customer message
      |
      v
Retrieval (Chroma, top-3 chunks from shipping/returns/refunds/cancellations/FAQ docs)
      |
      v
LLM call (gpt-4o-mini via Vocareum) with:
  - retrieved policy excerpts
  - known long-term facts from earlier in the conversation
  - adaptation instructions from this session's feedback
  - tool schemas (refund_eligibility_tool, delivery_estimate_tool, escalate_to_human_tool)
      |
      v
Tool-calling loop (max 4 iterations, then forced escalation)
      |
      v
Response  ->  short/long-term memory updated  ->  logged (non-PII operational logs + full-text
                                                    evidence log)
```

Wrapped by, in the final (Phase 8/9) state: a FastAPI HTTP service exposing this as `/chat`,
`/feedback`, `/reset`, `/health`, with request-level tracing and a global exception handler.

**Framework usage (Track A).** LangChain provides the RAG plumbing —
`RecursiveCharacterTextSplitter`, `OpenAIEmbeddings`, the `Chroma` vector store, and
`trim_messages` for short-term memory windowing (`phase_4` onward). Tool/function calling and the
agentic loop deliberately use the **raw `openai` client** instead of a LangChain `AgentExecutor` —
this was a considered choice, not an oversight: the manual loop is what makes it possible to add a
hard iteration cap (Phase 5's loop-guard), per-call latency instrumentation, and a narrow
retry-then-escalate failure boundary (Phase 8) exactly where they're needed, without working around
an agent-executor abstraction to get the same control. This mirrors a real industry pattern —
frameworks for the parts with well-established plumbing (retrieval), hand-rolled control flow for
the parts where the reliability/safety requirements are specific to this product.

## 3. Design decisions and tradeoffs

| Decision | Chosen approach | Alternative considered | Why |
|---|---|---|---|
| Vector store lifecycle | In-memory Chroma, rebuilt every run (`phase_4` onward) | Persistent on-disk Chroma | Reproducibility (`phase_4_notes.md` was tested against known-good confirmed content each run) mattered more than the extra ~2-3s startup cost per phase this project incurs; a real deployment would persist it and rebuild only on doc changes. |
| Missing/irrelevant retrieval | Prompt-level instruction ("if excerpts don't answer, say so and escalate") | Similarity-score threshold to reject weak chunks | A threshold would hide the "recognize irrelevant context" behavior being tested; the prompt-level approach forces the model to demonstrate that judgment directly (`phase_4_notes.md`, gift-wrapping test case). |
| Tool/agent orchestration | Raw `openai` client, manual loop with an explicit iteration cap | LangChain `AgentExecutor` | Direct control over the loop-guard, per-call timing, and failure boundaries (see Section 2) — these are safety/reliability requirements specific to this product, not generic agent behavior. |
| Date/eligibility computation | Deterministic Python tools (`refund_eligibility_tool`, `delivery_estimate_tool`), LLM only extracts inputs | Let the LLM compute eligibility from retrieved policy text | Phase 9's own root-cause case study (Section 3 of `phase9_evaluation_report.md`) is direct proof this distinction matters: the agent's prose arithmetic was right by luck, not guarantee, until the tool call was enforced. |
| Conversation memory | `langchain_core.messages.trim_messages` + a hand-rolled `long_term_facts` dict (`phase_6` onward) | `langchain.memory.ConversationBufferMemory`, as originally specified in `Problem Framing Document.docx` §16 | That class no longer exists in the installed `langchain_core` (1.6.0) — verified directly, not assumed, before substituting (`phase6_notes.md`). `trim_messages` is the current LangChain-recommended equivalent for windowing. |
| Feedback/adaptation storage | Session-scoped `preferences` (in-memory) drive live behavior; a separate non-PII `feedback_log.jsonl` persists ratings/reasons only, never message content | A single log that both drives behavior and persists across sessions | Keeps "customer information only used during the active session" (framing doc §9) true even as the system starts persisting *something* about feedback across runs (`phase7_notes.md`). |
| Adaptation scope | Feedback changes tone/verbosity and escalation sensitivity; **never** changes stated policy content, even under direct customer pushback | Let repeated "that's wrong" feedback adjust what the agent states as policy | Directly required by framing doc §14 ("never fabricate... base responses only on retrieved knowledge"); verified under an adversarial test (`phase7_notes.md`, Conversation C: customer insists on 30 days, agent still states 15 and flags for review instead of caving). |
| Local deployment shape | FastAPI HTTP service (`phase_8/app_api.py`) | Streamlit UI, as originally specified in `Problem Framing Document.docx` §16 | Explicit tradeoff, decided when starting Phase 8: FastAPI is independently verifiable end-to-end with `curl`/automated requests (real, reproducible evidence — status codes, latencies, logged traces) without depending on a human driving a browser for screenshots. Documented as a deliberate deviation from the originally-declared stack, not a silent one. |
| Logging | Direct structured JSONL file writes | Python `logging` module or LangSmith, as originally specified in §16 | JSONL keeps every log immediately inspectable/parseable as evidence (this is exactly how every phase's CSV evidence tables were produced) without an external LangSmith account; `logging`-module output would need the same downstream parsing anyway. |
| Evaluation method | Programmatic assertions against independently-recomputed ground truth (`phase_9`) | LLM-as-judge scoring | Keeps pass/fail objective and reproducible — a second LLM call grading the first would add its own failure mode (a judge that's wrong) on top of the one being measured. |

## 4. Safety approach

Mapped to `Problem Framing Document.docx` §14's six safety requirements, each against concrete,
reproducible evidence rather than a narrative claim:

| Requirement | Evidence |
|---|---|
| Refuse unsafe, malicious, or policy-violating requests | `phase_3` safety probes (out-of-scope refund processing) onward; `phase_9`'s `safety/out_of_scope_refund_processing` and `safety/off_topic_investment_advice` (4/4 pass, 2 live repeats each) |
| Never fabricate company policies or unsupported information | `phase_4` retrieval fixed the exact case where the pre-retrieval Phase 3 agent misapplied a policy; `phase_9` groundedness probes 5/5 pass this run |
| Base policy-related responses only on retrieved knowledge | Retrieval-grounded system prompt (`phase_4` onward); the Phase 7 adaptation boundary explicitly forbids feedback from altering stated policy, verified under direct customer pushback |
| Escalate unresolved, ambiguous, or low-confidence cases | `escalate_to_human_tool` (`phase_5` onward); `phase_5`'s loop-guard forces escalation after 4 failed tool-call iterations; `phase_8`'s retry-then-escalate wrapper forces escalation on LLM/retrieval failure; `phase_9`'s `safety/abusive_language_escalation` 2/2 pass |
| Mask or omit PII from application logs | Operational logs (`escalations.jsonl`, `feedback_log.jsonl`, `error_log.jsonl`, `trace_log.jsonl`, `phase_5` onward) write only structured, non-message fields — audited call-site by call-site in `phase9_evaluation_report.md` §4. **Honest exception**: the `*_interaction_log.jsonl` evidence logs used throughout this submission are full-text by design, appropriate for synthetic test queries in an academic submission but explicitly flagged as not production-safe as-is (same report, §4). |
| Clearly communicate uncertainty rather than making assumptions | Missing-info handling (`phase_4`, gift-wrapping case); `phase_8`'s graceful degradation ("I don't want to guess... I've escalated this") when retrieval or the LLM is unavailable, rather than answering anyway |

## 5. Success criteria vs. actual results

`Problem Framing Document.docx` §12 set numeric targets before any code was written. Measured
honestly against `phase_9`'s evaluation run (small sample — 25 live test cases — reported as
directional evidence, not a statistically powered benchmark):

| Metric | Target | Actual | Note |
|---|---|---|---|
| Average response time | < 5 seconds | median 2.31s, avg 2.73s (n=34 timed operations, `phase_9`) | 1 of 25 turns exceeded 5s (6.46s max) — within normal LLM-latency variance, not a systemic miss |
| Policy grounding accuracy | ≥ 95% | 5/5 (100%) groundedness probes | Small sample; consistent with retrieval-grounding design since Phase 4 |
| Correct tool selection | ≥ 95% | 5/7 (71%) tool-correctness probes | Below target as scored; on inspection, one "failure" was a defensible non-eligibility procedural query and one was one-off sampling variance confirmed non-reproducible on 3 immediate retries (`phase9_evaluation_report.md` §3) — genuine reliability nonetheless worth the roadmap item it generated |
| Human escalation accuracy | ≥ 95% | 6/6 (100%) safety probes | Small sample |
| Hallucination rate | < 5% | Not formally instrumented as a standalone metric | No hallucination observed in any logged test run post-Phase-4; would need a larger, adversarial-specific test set to claim a rate with confidence |
| Retrieval accuracy (top-3) | ≥ 90% | Not formally instrumented as a standalone metric | No labeled relevance dataset was built; groundedness probes are a proxy but not the same measurement |
| Customer query resolution | ≥ 80% | Not formally instrumented as a standalone metric | No end-to-end "was this actually resolved" label exists separate from the per-category pass/fail checks above |
| Intent classification accuracy | ≥ 90% | Not applicable to this architecture | There is no separate intent-classification stage — a single LLM call handles routing, retrieval use, and tool selection together, so this metric doesn't map onto the system as built |

Reporting the three unmeasured/not-applicable rows explicitly, rather than omitting them, is a
deliberate choice: claiming compliance with a metric that was never actually instrumented would be
exactly the kind of unsupported claim this project's own safety requirements (§14, "never
fabricate... clearly communicate uncertainty") argue against.

## 6. Reliability and failure handling

- **Tool-call loop guard** (`phase_5` onward): hard cap at 4 tool-call iterations per turn, then a
  forced `escalate_to_human_tool` call — proven with a direct synthetic drive of the iteration
  logic (`demo_loop_guard`), since a live model rarely loops on demand.
- **Invalid-input guardrails** (`phase_5` onward): every tool returns a structured
  `{"status": "error", ...}` on bad input rather than raising — proven with direct calls
  (`demo_invalid_tool_calls`) after the organic test query didn't reliably trigger a failed call.
- **LLM/retrieval failure handling** (`phase_8` onward): one retry with backoff, then a narrow
  `AgentUnavailableError` caught by `run_turn`, which forces an escalation and returns a safe
  fallback response — a turn always completes with a normal response, never an unhandled
  exception. Proven with forced fault injection (a monkeypatched client, a broken vectorstore) and
  confirmed the failure was isolated (a follow-up turn on the same conversation succeeded normally
  after the real client was restored) — `phase8_notes.md`.
- **Latency/error observability** (`phase_8` onward): every turn's retrieval/LLM/tool-call timing
  and every caught error is logged (`trace_log.jsonl`, `error_log.jsonl`), verified against real
  live HTTP traffic via `curl` against a running `uvicorn` instance, not just the offline demo
  script.

## 7. Deployment assumptions and limitations

(Full detail in `phase8_notes.md` and `phase9_evaluation_report.md` §5; summarized here.)

- **Local-only in this submission.** `uvicorn app_api:app` on `localhost`; no cloud hosting was
  used. The same FastAPI app would run on a host like Render/Railway without code changes, but that
  step was not exercised.
- **In-memory, non-persistent conversation store.** Consistent with "customer information only used
  during the active session," but also means state does not survive a server restart — no database
  layer exists.
- **No authentication, TLS, or rate-limiting** on the API — explicitly out of scope for an academic
  submission, named rather than silently absent.
- **Day-granularity date math** for the 48-hour damaged-product window (would need delivery
  timestamps, not just dates, for hour-level precision).
- **Sundays-only exclusion** in business-day delivery estimates — no public-holiday calendar was
  defined for this project.
- **Interaction logs are full-text**, appropriate for this submission's synthetic test queries but
  not production-safe as-is (Section 4 above).

## 8. Engineering judgment in practice

The evaluation checklist weighs "engineering judgment... not academic novelty." Three concrete
moments across this build are the clearest evidence of that, each a real failure found through
testing, diagnosed, fixed, and re-verified — not staged for the write-up:

1. **Phase 5 — a guardrail that needed forcing to prove.** The organically-run "invalid tool call"
   test query didn't actually produce a failed call: the model recognized the invalid input from
   retrieved context and asked a clarifying question instead. Rather than claim the guardrail was
   proven by a test that didn't actually exercise it, `demo_invalid_tool_calls()` was added to
   drive the failure path directly.
2. **Phase 7 — a soft instruction that didn't reliably hold.** The first version of the
   escalation-sensitivity adaptation rule ("proactively offer to escalate") produced no visible
   behavioral change on the live model. Rather than re-run until it happened to work, the failure
   was documented, the instruction was rewritten to require a literal example sentence, and the
   re-run showed a clean, reliable signal — both versions and results are in `phase7_notes.md`.
3. **Phase 9 — a real bug found by the evaluation harness on its first run.** Before any fix, the
   harness scored 19/25 (76%) and isolated every failure to damaged-item eligibility questions
   being answered by model arithmetic instead of the deterministic tool. Root cause diagnosed
   (the prompt's tool-triggering rule didn't explicitly cover this path), fixed, and backported to
   the actually-deployed Phase 8 agent — not left as a known-but-unfixed issue in the "final"
   version. Full before/after evidence in `phase9_evaluation_report.md` §3.

## 9. Improvement roadmap

Prioritized list (full detail and rationale in `phase9_evaluation_report.md` §5):

1. Tool-triggering reliability isn't perfectly deterministic at temperature 0.2 (Phase 9 finding) —
   consider temperature 0 for tool-decision-relevant calls, or a post-hoc validator.
2. Hour-granularity for the 48-hour damaged-product window (Phase 5).
3. Per-order long-term memory, not single-slot (Phase 6).
4. Persistent conversation store for the deployed API (Phase 8).
5. Intent-classified reset/topic-flag matching instead of substring matching (Phases 6-7).
6. Per-topic, not global, style preference (Phase 7).
7. Public-holiday calendar for business-day math (Phase 5).
8. Auth/rate-limiting/TLS for the API (Phase 8).
9. Redact or short-retention the full-text interaction logs before any real customer traffic
   (Phase 9).
