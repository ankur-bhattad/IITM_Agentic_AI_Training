# Phase 8 Notes — Deployment Readiness (SupportSense AI)

## What was built
Every phase from 2 through 7 has been a one-shot CLI script that runs a fixed set of scripted
conversations and exits. Phase 7's own notes named exactly the gap this phase closes: *"it has
never been deployed, packaged, or exercised for reliability/failure characteristics — there is no
latency/error capture, no graceful-failure handling beyond individual tool guardrails, and no
documented deployment assumptions."*

Three pieces close that gap:

- **`phase8_agent_core.py`** — Phase 7's tools, retrieval, and `Conversation` (memory + adaptation
  rules) factored out of a single script into an importable module, unchanged in behaviour but now
  instrumented with per-step latency timing and wrapped so that an LLM-call or retrieval failure
  can never reach the caller as an unhandled exception.
- **`app_api.py`** — a FastAPI service exposing the agent over HTTP (`/health`, `/chat`,
  `/feedback`, `/reset`) — the **local deployment** this phase's "deploy locally or on the cloud"
  requirement asks for. Started with `uvicorn app_api:app`.
- **`phase8_cli_demo.py`** — an offline evidence script (same shape as Phase 7's `run_all()`) that
  exercises the agent core directly against the live Vocareum endpoint, plus two forced
  failure-injection demos.

## Logging / tracing design
Two new non-PII logs, shared by both the API and the CLI script (same file, same schema,
regardless of which entry point produced the record):

- **`logs/trace_log.jsonl`** — one record per turn or HTTP request: `trace_id`, `conversation_id`,
  `turn_index`, `scenario` (or `http METHOD /path` for the request-level record the FastAPI
  middleware adds), `status`, `retrieval_ms`, `llm_call_ms` (list — one entry per LLM call in that
  turn, since a turn can involve more than one when tools are called), `tool_call_ms` (list), and
  `total_ms`.
- **`logs/error_log.jsonl`** — one record per failed attempt: `trace_id`, `conversation_id`,
  `turn_index`, `error_type`, `error_message` (truncated to 200 chars), `recovered` (whether a
  retry followed), `action_taken`.

Both deliberately never record raw user message content — only ids, timings, and error
type/message — the same non-PII rule Phases 5-7 applied to `escalations.jsonl`/
`feedback_log.jsonl`, extended to this phase's new logs.

## Graceful failure handling
`_call_llm()` and `_retrieve_with_fallback()` each retry once (0.5s backoff) on any exception; if
both attempts fail they raise a narrow `AgentUnavailableError` rather than letting the raw
`openai`/Chroma exception escape. `run_turn()` catches that error, logs it, forces an
`escalate_to_human_tool("tool_failure", ...)` call, and returns a normal response object with a
safe fallback message and a real escalation ticket — **a turn always completes with a response,
never an unhandled exception**. The FastAPI layer adds one more net: a global exception handler
that catches anything still unhandled, logs it, and returns a generic HTTP 500 body without ever
leaking a stack trace to the caller.

## Results — actual observed behaviour (from the real run, live Vocareum endpoint)

**Normal operation, with real latency numbers.** `phase8_cli_demo.py`'s two real conversations
(4 turns total, live model calls) all completed with `status: ok`. Total turn latency ranged
3.3s–4.6s, dominated by the two sequential LLM calls a tool-using turn requires (extract →
tool-call → synthesize): retrieval consistently ~0.7-1.3s, each LLM call ~1.2-2.7s. A non-tool turn
(pure policy Q&A) needed only one LLM call and was correspondingly faster.

**Forced retrieval failure — graceful, not a crash.** `demo_forced_retrieval_failure()` passes a
`_BrokenVectorstore` that raises `ConnectionError` on every call directly into `run_turn`. Real
logged result: two failed attempts in `error_log.jsonl` (`recovered: true` then `recovered:
false`), `status: degraded_ok`, response *"I'm having trouble accessing our policy information
right now, so I don't want to guess. I've escalated this to a human agent (ticket
ESC-5D8E4783)."* — the agent explicitly refuses to guess rather than fabricate a policy answer
without grounding, consistent with the Problem Framing Document's "never fabricate policies," and
escalates per "must escalate sensitive or unresolved cases."

**Forced LLM-call failure — graceful, not a crash, and isolated.** `demo_forced_llm_failure()`
monkeypatches `core.client.chat.completions.create` to raise `TimeoutError` unconditionally, runs
one turn (two failed attempts logged, `status: degraded_ok`, fallback + escalation ticket
`ESC-84E8D307`), restores the real client, then runs a second, real turn on the *same*
conversation object. That follow-up turn completed normally (`status: ok`) — proving the failure
was isolated to the injected call and didn't leave the conversation or client in a broken state.

**Live HTTP server verification.** Started `uvicorn app_api:app --port 8000` and drove it with real
`curl` requests: `GET /health` → `200 {"vectorstore_loaded": true}`; two `POST /chat` calls building
a real conversation; `POST /feedback` (`too_long`) → `{"preferences": {"style": "concise"}}`; a
third `/chat` call whose response was visibly shorter/more direct than the pre-feedback answer
(same style-adaptation mechanism verified in Phase 7, now proven to also work end-to-end over
HTTP); `POST /reset`; and a request to an undefined path, which correctly returned `404` rather
than a server error. Every one of these landed a real entry in `trace_log.jsonl` with an accurate
status code and latency — see the log file for the exact records (timestamps ~18:14 UTC in this
run).

## Deployment assumptions and limitations
- **Local only.** This submission runs `uvicorn` on `localhost`; no actual cloud account/hosting
  was used. The same FastAPI app would run unmodified behind a process manager on a host like
  Render or Railway — that specific step was not exercised here and is named as a limitation
  rather than implied.
- **In-memory, non-persistent conversation store.** `app_api.py` keeps a single process-level
  `dict[str, Conversation]` keyed by `conversation_id`. This is consistent with the Problem Framing
  Document's "customer information should only be used during the active session" (same rationale
  as Phase 6/7's memory design), but it also means **conversation state is lost on every server
  restart** — there is no database or persistence layer. Acceptable for this academic submission;
  a production deployment would need a session store (Redis, etc.) if cross-restart continuity
  were required.
- **No authentication, TLS, or rate-limiting.** Any client that can reach the port can call every
  endpoint. Out of scope for this submission, but explicitly named rather than silently absent.
- **Retry policy is fixed and conservative** (one retry, 0.5s backoff, then escalate) — tuned for
  demoability, not for a specific production SLA. A real deployment would tune retry count/backoff
  against the LLM provider's actual failure-rate characteristics.
- **The forced-failure demos are synthetic**, same as Phases 5-7's guardrail evidence
  (`demo_invalid_tool_calls`, `demo_loop_guard`, `demo_short_term_trimming`) — a live Vocareum
  outage wasn't available to test against on demand, so the failure path is proven by direct
  injection (a broken vectorstore object, a monkeypatched client method) rather than waiting for an
  organic outage. This is labeled `[synthetic]` in the CSV and console output, not presented as if
  it happened by chance.

## Running it
Requires network access to the Vocareum endpoint (same constraint as Phases 3-7).

Offline evidence (writes all four log/table files, no server needed):
```bash
python phase8_cli_demo.py
```

Local deployment:
```bash
uvicorn app_api:app --reload --port 8000
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" \
  -d '{"conversation_id":"demo","message":"How long does standard delivery take?"}'
```

Writes:
- `logs/phase8_interaction_log.jsonl` — full per-turn transcripts + timing (CLI demo only)
- `logs/trace_log.jsonl` — latency records (shared by the CLI demo and the live API)
- `logs/error_log.jsonl` — captured errors, real and forced (shared by the CLI demo and the live API)
- `logs/deployment_readiness_table.csv` — scenario → request → status → latency → notes
  (a copy is kept at `Solution/phase_8_deployment_readiness_table.csv` for the submission package)
- `logs/escalations.jsonl`, `logs/feedback_log.jsonl` — non-PII records, same as Phases 5-7

## Carried-forward limitation (motivates Phase 9)
The agent is now a packaged, running service with real latency/error visibility and proven
graceful degradation — but nothing in this project has yet systematically measured response
*quality* (correctness, consistency, groundedness) across a broad test set, or done a structured
root-cause analysis of a real failure with a documented before/after fix, or reviewed safety/ethics
as a distinct exercise. Phase 9 (Evaluation & Engineering Review) adds a test harness, quality
metrics, root-cause analysis, and an improvement roadmap.
