"""
Conversation Orchestrator (Core Services box)
-----------------------------------------------
The single place that wires together: Rate Limiter & Guardrails -> Context
Manager (load history) -> LLM Provider (generate) -> Context Manager
(persist history). Mirrors the "Chat Request" path in the diagram.
"""
from app import context_manager, guardrails
from app.llm_provider import get_llm_provider

# One provider instance reused across requests (Gemini client is stateless per-call anyway)
_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = get_llm_provider()
    return _llm


def handle_chat(username: str, session_id: str, user_message: str) -> str:
    # Rate Limiter & Guardrails
    guardrails.check_rate_limit(username)
    guardrails.check_guardrails(user_message)

    # Context Manager: Load History
    history = context_manager.load_history(session_id)

    # LLM Provider Abstraction Layer: Prompt -> Gemini
    llm = _get_llm()
    reply = llm.generate(history, user_message)

    # Context Manager: Persist History
    context_manager.persist_turn(session_id, username, "user", user_message)
    context_manager.persist_turn(session_id, username, "assistant", reply)

    return reply
