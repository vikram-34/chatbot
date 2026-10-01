# Python Chatbot

A Python chatbot built on the layered architecture from the diagram:
Client Layer → API Gateway → Core Services → AI Components → LLM Provider / Storage.

Only **Gemini** is wired up as the LLM (OpenAI/Ollama/Claude branches from the
diagram are intentionally skipped, though `app/llm_provider.py` keeps the same
interface if you want to add them later). Storage uses **SQLite** in place of
the diagram's Postgres/Redis/Chroma stack, kept behind the same read/write API.

## Structure

```
chatbot/
├── app/
│   ├── main.py             # API Gateway (FastAPI) - routes, JWT verify, throttle check
│   ├── auth.py              # Auth / JWT Service
│   ├── orchestrator.py      # Conversation Orchestrator
│   ├── guardrails.py        # Rate Limiter & Guardrails
│   ├── context_manager.py   # Context Manager / Memory Store
│   ├── llm_provider.py      # LLM Provider Abstraction Layer (Gemini)
│   ├── storage.py           # Storage Layer (SQLite: sessions + messages)
│   └── config.py            # Settings from .env
├── cli_client.py            # CLI / SDK Consumer (terminal chat client)
├── requirements.txt
└── .env.example
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Get a Gemini API key from https://aistudio.google.com/apikey

3. Copy the env template and fill in your key:
   ```bash
   cp .env.example .env
   # edit .env and set GEMINI_API_KEY=...
   ```

4. Start the API Gateway:
   ```bash
   uvicorn app.main:app --reload
   ```
   This runs on `http://127.0.0.1:8000`. A SQLite DB is created at `./data/chatbot.db`
   on first startup.

5. In a second terminal, run the CLI client:
   ```bash
   python cli_client.py
   ```
   It will sign you up (or log in), then drop you into a chat loop.
   Type `reset` to clear history, `exit` to quit.

## API reference

| Method | Path                | Auth | Description                        |
|--------|---------------------|------|-------------------------------------|
| POST   | `/auth/signup`       | No   | `{username, password}` → create user |
| POST   | `/auth/token`        | No   | `{username, password}` → JWT        |
| POST   | `/chat`              | Yes  | `{session_id, message}` → `{reply}` |
| DELETE | `/chat/{session_id}` | Yes  | Clears that session's history       |
| GET    | `/health`            | No   | Liveness check                      |

Send the JWT as `Authorization: Bearer <token>` on `/chat` calls.

### Example with curl

```bash
curl -X POST http://127.0.0.1:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'

TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -X POST http://127.0.0.1:8000/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "s1", "message": "Hello, who are you?"}'
```

## Notes / where to extend

- **Guardrails**: `app/guardrails.py` has a placeholder blocklist — swap in a real
  moderation API call for production use.
- **Rate limiting**: currently in-memory per-process; move to Redis if you scale to
  multiple workers/instances.
- **Vector search / RAG**: not implemented (the diagram's ChromaDB box). Add a
  `retrieve()` step in `orchestrator.py` before the LLM call if you need it.
- **Multiple LLM providers**: implement another `LLMProvider` subclass in
  `llm_provider.py` and swap what `get_llm_provider()` returns.
