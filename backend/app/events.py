import json

import redis

from app.config import REDIS_URL
from app.models import AuditLog

STREAM = "tradeshield.events"
_client = None


def publish(event: str, data: dict) -> None:
    global _client
    try:
        if _client is None:
            _client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
        _client.xadd(STREAM, {"event": event, "data": json.dumps(data, default=str)}, maxlen=10000)
    except Exception:
        pass


def client_ctx(request) -> dict:
    return {
        "ip": request.client.host if request.client else None,
        "user_agent": (request.headers.get("user-agent") or "")[:300],
    }


def audit(db, user_id, action: str, ctx: dict = None, detail: dict = None) -> None:
    ctx = ctx or {}
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            ip=ctx.get("ip"),
            user_agent=ctx.get("user_agent"),
            detail=detail,
        )
    )