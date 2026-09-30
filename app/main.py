"""
API Gateway (FastAPI stands in for FastAPI + Nginx in the diagram)
---------------------------------------------------------------------
Exposes:
  POST /auth/signup   - create a user
  POST /auth/token     - login, get a JWT
  POST /chat           - JWT Verify -> Throttle Check -> Conversation Orchestrator
  DELETE /chat/{session_id} - clear a session's history

Serves the "Client Layer" consumers in the diagram: Web App, Mobile App,
REST API Client, CLI/SDK Consumer -- they all just call this HTTP API.
"""
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel

from app import auth, storage, orchestrator
from app.guardrails import RateLimitExceeded

app = FastAPI(title="Gemini Chatbot API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    storage.init_db()


# ---------- Schemas ----------

class SignupRequest(BaseModel):
    username: str
    password: str


class TokenRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


# ---------- Auth Middleware helper ----------

def get_current_user(authorization: str = Header(...)) -> str:
    """Expects header: Authorization: Bearer <token>. This is the 'JWT Verify' step."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    username = auth.verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username


# ---------- Routes ----------

@app.post("/auth/signup", status_code=201)
def signup(req: SignupRequest):
    try:
        auth.signup(req.username, req.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "created", "username": req.username}


@app.post("/auth/token")
def login(req: TokenRequest):
    if not auth.authenticate(req.username, req.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth.create_access_token(req.username)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, username: str = Depends(get_current_user)):
    try:
        reply = orchestrator.handle_chat(username, req.session_id, req.message)
    except RateLimitExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ValueError as e:
        # guardrail block
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # e.g. missing GEMINI_API_KEY
        raise HTTPException(status_code=500, detail=str(e))
    return ChatResponse(reply=reply)


@app.delete("/chat/{session_id}")
def clear_chat(session_id: str, username: str = Depends(get_current_user)):
    from app import context_manager
    context_manager.reset_session(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.get("/health")
def health():
    return {"status": "ok"}
