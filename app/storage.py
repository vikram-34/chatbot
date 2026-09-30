"""
Storage Layer
-------------
In the architecture diagram this box is Redis (sessions) + PostgreSQL (users/messages)
+ ChromaDB (vector/RAG) + File/S3 (logs). For a single-process chatbot, SQLite covers
sessions + message history in one file, with the same read/write interface. Swap this
module out for real Postgres/Redis clients later without touching any other layer.
"""
import sqlite3
import time
import os
from contextlib import contextmanager
from typing import List, Dict, Optional

from app.config import settings

os.makedirs(os.path.dirname(settings.DB_PATH) or ".", exist_ok=True)


@contextmanager
def get_conn():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                username TEXT NOT NULL,
                role TEXT NOT NULL,       -- 'user' or 'assistant'
                content TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id, created_at)
        """)


# ---- Users ----

def create_user(username: str, password_hash: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, time.time()),
        )


def get_user(username: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cur.fetchone()


# ---- Session / message history (Redis "Sessions" + PostgreSQL "Users/Msgs" combined here) ----

def append_message(session_id: str, username: str, role: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (session_id, username, role, content, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, username, role, content, time.time()),
        )


def load_history(session_id: str, limit: int = 20) -> List[Dict]:
    with get_conn() as conn:
        cur = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? "
            "ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
        )
        return [{"role": r["role"], "content": r["content"]} for r in cur.fetchall()]


def clear_session(session_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
