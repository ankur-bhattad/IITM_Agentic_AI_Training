"""
SupportSense AI — Phase 8: Deployment Readiness (FastAPI service)
=====================================================================
The local HTTP deployment of the Phase 7 agent, built on `phase8_agent_core`.

Endpoints:
    GET  /health              liveness check
    POST /chat                {conversation_id, message} -> response + tools + preferences + timing
    POST /feedback             {conversation_id, turn_index, rating, reason, related_query} -> preferences
    POST /reset                {conversation_id} -> clears that conversation

Deployment assumptions (see phase8_notes.md for the full list):
    - Single process, in-memory conversation store keyed by conversation_id.
      Conversation state does NOT survive a server restart -- consistent
      with the Problem Framing Document's "customer info only used during
      the active session," but worth being explicit that this also means
      no persistence layer exists.
    - No authentication, TLS, or rate-limiting -- out of scope for this
      academic submission; documented, not hidden.
    - Local-only in this submission (uvicorn on localhost). The same app
      would run on a cloud host (Render/Railway/etc.) behind a process
      manager without code changes -- that step itself was not exercised.

Run:
    uvicorn app_api:app --reload --port 8000
"""

import time
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import phase8_agent_core as core

app = FastAPI(title="SupportSense AI", version="phase8")

_vectorstore = None
_conversations: dict[str, core.Conversation] = {}


@app.on_event("startup")
def _startup():
    global _vectorstore
    _vectorstore = core.build_vectorstore()


def _get_conversation(conversation_id: str) -> core.Conversation:
    if conversation_id not in _conversations:
        _conversations[conversation_id] = core.Conversation(conversation_id)
    return _conversations[conversation_id]


@app.middleware("http")
async def _trace_requests(request: Request, call_next):
    trace_id = uuid.uuid4().hex[:12]
    started = time.perf_counter()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:  # noqa: BLE001 - last-resort net; the handler below also covers this
        core.log_error("(unknown)", 0, type(exc).__name__, str(exc), recovered=False, action_taken="unhandled request exception", trace_id=trace_id)
        raise
    duration_ms = round((time.perf_counter() - started) * 1000, 1)
    core.log_trace({
        "trace_id": trace_id, "conversation_id": "(http)", "turn_index": None,
        "scenario": f"http {request.method} {request.url.path}",
        "status": status_code, "total_ms": duration_ms,
        "retrieval_ms": None, "llm_call_ms": [], "tool_call_ms": [],
    })
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception):
    trace_id = uuid.uuid4().hex[:12]
    core.log_error("(unknown)", 0, type(exc).__name__, str(exc), recovered=False, action_taken=f"500 returned for {request.url.path}", trace_id=trace_id)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Something went wrong on our side. This has been logged; please try again or contact support.", "trace_id": trace_id},
    )


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


class FeedbackRequest(BaseModel):
    conversation_id: str
    turn_index: int
    rating: str
    reason: str
    related_query: str = ""


class ResetRequest(BaseModel):
    conversation_id: str


@app.get("/health")
def health():
    return {"status": "ok", "vectorstore_loaded": _vectorstore is not None, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/chat")
def chat(req: ChatRequest):
    conversation = _get_conversation(req.conversation_id)
    result = core.run_turn(conversation, _vectorstore, req.message)
    return result


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    conversation = _get_conversation(req.conversation_id)
    preferences = conversation.submit_feedback(req.turn_index, req.rating, req.reason, req.related_query)
    return {"status": "ok", "conversation_id": req.conversation_id, "preferences": preferences}


@app.post("/reset")
def reset(req: ResetRequest):
    conversation = _get_conversation(req.conversation_id)
    conversation.reset()
    return {"status": "ok", "conversation_id": req.conversation_id}
