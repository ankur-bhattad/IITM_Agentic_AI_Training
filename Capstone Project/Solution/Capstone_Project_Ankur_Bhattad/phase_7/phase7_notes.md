# Phase 7 Notes — Adaptive Behaviour (SupportSense AI)

## What was built
`phase7_adaptive_agent.py` extends Phase 6's memory-carrying, tool-calling, retrieval-grounded
`Conversation` with a feedback mechanism: an explicit thumbs-up/down + a fixed reason code (modeled
the way a real product UI would send it — buttons with known reason codes, not free text the model
has to interpret) drives small, explicit, explainable behaviour-adjustment rules for the rest of
that session.

**The adaptation rules** (`Conversation._apply_adaptation_rules`):
| Feedback reason | What changes | What never changes |
|---|---|---|
| `too_long` / `too_technical` | `preferences["style"] = "concise"` → future responses instructed to be 2-4 sentences, plain language | policy content |
| `not_resolved` | `preferences["escalate_proactively"] = True` → future responses must explicitly offer human escalation, even for answerable questions | policy content |
| `incorrect_info` | `preferences["flagged_topics"]` records the disputed topic → future responses on that topic add a "flagged for human review" acknowledgment | **the stated policy fact itself — never** |

**The safety boundary, and why it exists**: the Problem Framing Document's Safety Requirements say
the agent must "never fabricate company policies" and must "base policy-related responses only on
retrieved knowledge from approved documents." A naive adaptive-feedback design could easily violate
this — e.g. if enough customers say "that's wrong" about a correct policy, a system that adapts
*content* based on sentiment could start stating the wrong policy. This phase deliberately never
lets feedback touch *what* the agent states as policy — only *how* it communicates (verbosity) and
*when* it proactively escalates. An `incorrect_info` report is handled as a transparency/escalation
signal (flagged for human review), never as evidence the retrieved document is wrong.

**Feedback storage, and why it's split two ways**: `Conversation.preferences` (session-scoped,
in-memory only) is what actually drives live behaviour, for the same privacy reason Phase 6's
memory design gave: the Problem Framing Document's "customer information should only be used during
the active session." Separately, `logs/feedback_log.jsonl` is an explicitly non-PII, cross-run log
(timestamp, conversation name, turn index, rating, reason code only — no message content) kept for
product-analytics purposes (e.g. which topics get repeated "too_long" or "incorrect_info" reports)
— it does not feed back into any live session's behaviour, so it can't reintroduce cross-session
customer data.

## Running it
Requires network access to the Vocareum endpoint (same constraint as Phases 3-6):
```bash
python phase7_adaptive_agent.py
```
Writes:
- `logs/phase7_interaction_log.jsonl` — full per-turn transcripts + preferences state
- `logs/adaptive_behavior_table.csv` — Conversation → step → event → response → preferences → notes
  (a copy is kept at `Solution/adaptive_behavior_table.csv` for the submission package)
- `logs/feedback_log.jsonl` — non-PII feedback records
- `logs/escalations.jsonl` — non-PII escalation records (shared file, same as Phases 5-6)

## Results — actual observed before/after behaviour (from the real run)

**Style adaptation (Conversation A).** Turn 1, a broad two-part shipping question, got a 159-word
answer with headers and bullet lists. After `("down", "too_long")` feedback, Turn 2 — a
comparably broad, two-part delivery-delay question — got a 96-word answer (~40% shorter), phrased
as "here's a brief overview" with no header formatting. Same underlying breadth of question,
measurably more concise answer.

**Escalation-sensitivity adaptation (Conversation B) — required one iteration to get a reliable
signal.** Turn 1 ("my product arrived damaged, what should I do?") got a direct, correct answer
with no escalation offer. After `("down", "not_resolved")` feedback, the first version of the
adaptation instruction ("proactively offer to escalate") was too soft: Turn 2's response answered
the shipping-charge question correctly but did **not** include an escalation offer — the model
didn't reliably follow a general instruction to add an unprompted offer. The instruction was
strengthened to require a literal escalation-offer sentence, and on re-run Turn 2 correctly ended
with *"Would you like me to connect you with a human support representative as well?"* while still
answering the original question. This is worth being explicit about: the first attempt's failure is
itself useful evidence that "adapt behaviour based on feedback" needs specific, checkable
instructions, not vague ones — a soft instruction competing against the agent's normal terse
support-answer habit lost.

**Flagged-for-review safety boundary (Conversation C).** Turn 1 correctly stated the 15-day
standard return window. After `("down", "incorrect_info")` feedback (on the return-window
question specifically), Turn 2 — where the customer directly asserted "I read online it should be
30 days" — still correctly restated **15 days**, matching `returns_policy.md` exactly, and added
*"I've flagged this for human policy review."* The policy content did not move even when the
customer pushed back with a specific, confident (and wrong) alternative number — proving the
adaptation boundary holds under direct pressure, not just in the absence of pushback.

## Failure modes / limitations observed
- **A general "proactively offer escalation" instruction was not reliably followed** by the model
  until phrased as a literal required sentence — documented above as the clearest concrete example
  in this whole project of a prompt-level failure mode and its fix (before/after prompt wording,
  before/after resulting behaviour).
- **`flagged_topics` matching is topic-text-based, not a stable topic id** — it relies on the model
  recognizing "is this turn about the same topic as a previously flagged query," which works for
  a direct follow-up but would degrade for a much-later, differently-worded return to the same
  disputed topic. A production version would classify feedback against a fixed policy-section
  taxonomy rather than matching on the literal disputed query text.
- **Preferences are global per conversation, not per-topic** — e.g. `too_long` feedback about
  shipping details makes *all* future answers in the session more concise, not just shipping ones.
  This is a deliberate simplicity choice appropriate to this phase's scope, but a finer-grained
  version could scope style preference per topic.

## Carried-forward limitation (motivates Phase 8)
The agent now adapts within a session and logs feedback for later product analysis, but it has
never been deployed, packaged, or exercised for reliability/failure characteristics — there is no
latency/error capture, no graceful-failure handling beyond individual tool guardrails, and no
documented deployment assumptions. Phase 8 (deployment readiness) addresses packaging,
logging/tracing, and runtime failure handling.
