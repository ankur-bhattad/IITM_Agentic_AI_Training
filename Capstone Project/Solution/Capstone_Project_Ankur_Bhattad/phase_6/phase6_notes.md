# Phase 6 Notes — Planning, Memory & Context (SupportSense AI)

## What was built
`phase6_memory_agent.py` extends Phase 5's tool-calling + retrieval agent into a multi-turn
`Conversation`, directly resolving Phase 5's stated carried-forward limitation: *"a follow-up like
'what about if it's damaged instead?' after an eligibility answer would require the user to
restate the delivery date from scratch."*

**Memory design:**
- **Short-term memory**: each `Conversation` keeps a running list of `HumanMessage`/`AIMessage`
  pairs (one pair per turn — the user's text and the agent's final answer only, never the
  intermediate tool-call/tool-result messages, so trimming can never split a tool call from its
  result). Before each new turn, this history is windowed with
  `langchain_core.messages.trim_messages(max_tokens=12, token_counter=len, strategy="last",
  start_on="human")`, capping it at ~6 turn-pairs.
- **Long-term (session) memory**: a small `long_term_facts` dict, updated automatically whenever a
  tool call succeeds (e.g. a `refund_eligibility_tool` call records the delivery date used; a
  `delivery_estimate_tool` call records the order date, shipping method, and estimate). This is
  re-injected into the system prompt's "Known context" section every turn, so a fact survives even
  after its originating message would eventually be trimmed out of short-term history.
- **Retention rule**: both stores live only inside one in-process `Conversation` object — nothing
  is written to disk — matching the Problem Framing Document's Privacy & Security constraint that
  *"customer information should only be used during the active session."*
- **Reset rule**: a user phrase containing "start over" / "forget what I told you" / similar clears
  both `short_term` and `long_term_facts` immediately (`Conversation.reset()`), logged as a
  `memory_reset: true` turn.
- **Planning**: the system prompt instructs the model that a compound, multi-part request should
  get a short numbered plan before acting, calling whatever tools each part needs.

**Note on the framing document's declared stack**: Section 16 of the Problem Framing Document
names "LangChain Conversation Memory," referring to `langchain.memory.ConversationBufferMemory`.
A direct check of the installed `venv/` before writing this phase confirmed that class no longer
exists in `langchain_core` 1.6.0 — it was removed upstream in favor of managing message lists
directly plus `trim_messages` for windowing, which is what this phase actually uses.

## Running it
Requires network access to the Vocareum endpoint (same constraint as Phases 3-5):
```bash
python phase6_memory_agent.py
```
Writes:
- `logs/phase6_interaction_log.jsonl` — full per-turn transcripts + memory snapshots
- `logs/multi_turn_conversation_table.csv` — Conversation → Turn → User → Response → Notes
  (a copy is kept at `Solution/multi_turn_conversation_table.csv` for the submission package)
- `logs/escalations.jsonl` — non-PII escalation records (shared file, same as Phase 5)

## Results — actual observed behavior (from the real run, 3 conversations + 1 synthetic test)

**Conversation A proves cross-turn recall, including re-deriving a changed answer.** Turn 1 ("Is
my order delivered on 2026-08-28 eligible for return?") correctly called `refund_eligibility_tool`
and got `eligible: True`. Turn 2 — *"What if it had arrived damaged instead?"* — restated no date
at all. The agent correctly reused `2026-08-28` from `long_term_facts` and re-called the tool with
`is_damaged=True`, correctly flipping the answer to **not eligible** (4 days since delivery > the
2-day damaged-report window). This is the literal scenario Phase 5's notes predicted as the gap
motivating this phase, now demonstrably resolved — and it shows memory isn't just parroting a
cached answer, but correctly re-deriving a *different, tool-computed* answer for a hypothetical
variation.

**Conversation B proves planning/decomposition.** A single compound turn asking about both return
eligibility (delivery 2026-08-10) and a delivery estimate (order 2026-09-01, express) correctly
triggered both `refund_eligibility_tool` and `delivery_estimate_tool` in the same turn, and the
final response addressed both parts as a clearly numbered combined answer (eligibility: not
eligible, 22 days > 15; delivery estimate: 2026-09-03 to 2026-09-04) rather than answering only one
part or conflating the two.

**Conversation C proves the reset rule actually removes data, not just leaves it unused.** Turn 1
established `eligible: True` for 2026-08-28 exactly as in Conversation A. Turn 2 ("forget what I
told you and start over") triggered `Conversation.reset()`; `facts_after_turn` for that row is
`{}`, confirming the clear. Turn 3 — *"Is my item still returnable?"* — gave no date, and critically
the agent asked for the delivery date again instead of quietly reusing the pre-reset 2026-08-28.
This is the important proof: if the agent had answered directly, it would show the reset only
looked like it worked while the model was still implicitly aware of the old context; the actual
clarifying question is direct evidence the fact was really gone.

**The short-term trimming cap needed a direct/synthetic test, same as Phase 5's guardrail
evidence.** None of the 3 real conversations run long enough to trigger `MAX_SHORT_TERM_MESSAGES`
trimming organically (they're 1-3 turns each). `demo_short_term_trimming()` builds a synthetic
20-message (10-turn) history and passes it through the same `trim_messages(...)` call used in
production: exactly 12 messages were retained, correctly starting on a human message (`start_on=
"human"` dropped a would-be orphaned leading AI message), with the oldest 8 messages dropped. This
directly proves the cap engages, independent of whether any given real conversation happens to be
long enough to exercise it — the same pattern used in Phase 5 to prove the loop-guard and
invalid-tool-call paths.

## Failure modes / limitations observed
- **Long-term facts are single-slot, not per-order** — `long_term_facts["last_delivery_date"]` is
  overwritten by the most recent tool call. If a customer asked about two different orders in the
  same conversation, the second `refund_eligibility_tool` call would overwrite the first order's
  remembered date. Acceptable for this phase's single-order-at-a-time demo scope; a production
  version would key facts by order id.
- **Reset detection is a simple substring match** on a short fixed phrase list, not an
  intent-classification step — a differently worded reset request (e.g. "never mind, new topic")
  would not be recognized and memory would persist unintentionally. This is a known, documented
  simplification rather than a hidden gap.
- **Day-granularity date math** (carried over from Phase 5) still applies to the damaged-product
  window.

## Carried-forward limitation (motivates Phase 7)
The agent now remembers facts and can recompute a changed conclusion when a hypothetical changes —
but it has no way to learn from being told it was *wrong*, or to have a customer's explicit
feedback change its future behavior within or across conversations. Every response is generated
fresh from the same fixed system prompt and tools every time; there's no feedback-driven adaptation
yet. Phase 7 (adaptive behaviour) adds a feedback mechanism so the agent's behavior can actually
change based on signals the customer or a reviewer gives it.
