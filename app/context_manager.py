"""
Context Manager / Memory Store (AI Components box)
----------------------------------------------------
Responsible for "Load History" and "Persist History" — reading and writing
conversation turns to/from the Storage Layer so the LLM call has context.
"""
from typing import List, Dict

from app import storage

MAX_HISTORY_TURNS = 20


def load_history(session_id: str) -> List[Dict[str, str]]:
    return storage.load_history(session_id, limit=MAX_HISTORY_TURNS)


def persist_turn(session_id: str, username: str, role: str, content: str) -> None:
    storage.append_message(session_id, username, role, content)


def reset_session(session_id: str) -> None:
    storage.clear_session(session_id)
