"""
Rate Limiter & Guardrails (Core Services box)
----------------------------------------------
Simple in-memory sliding-window rate limiter per user, plus a basic
input guardrail hook you can extend with real moderation later.
"""
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from app.config import settings

_request_log: Dict[str, Deque[float]] = defaultdict(deque)

# Extend this list (or replace with a moderation API call) as needed.
_BLOCKED_TERMS = {"hack into", "make a bomb", "kill someone"}


class RateLimitExceeded(Exception):
    pass


def check_rate_limit(username: str) -> None:
    now = time.time()
    window = settings.RATE_LIMIT_WINDOW_SECONDS
    max_requests = settings.RATE_LIMIT_MAX_REQUESTS

    log = _request_log[username]
    while log and now - log[0] > window:
        log.popleft()

    if len(log) >= max_requests:
        raise RateLimitExceeded(
            f"Rate limit exceeded: {max_requests} requests per {window}s"
        )
    log.append(now)


def check_guardrails(message: str) -> None:
    lowered = message.lower()
    for term in _BLOCKED_TERMS:
        if term in lowered:
            raise ValueError("Message blocked by content guardrails.")
