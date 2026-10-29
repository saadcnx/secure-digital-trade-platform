from collections import defaultdict
from time import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.events import audit, client_ctx, publish
from app.models import User
from app.schemas import RegisterIn, TokenOut, UserOut
from app.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

_attempts: dict[str, list[float]] = defaultdict(list)
WINDOW, MAX_TRY = 300, 10


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, request: Request, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    user = User(
        email=email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        region=data.region,
    )
    db.add(user)
    db.flush()
    audit(db, user.id, "auth.register", client_ctx(request), {"role": user.role})
    db.commit()
    return user


@router.post("/login", response_model=TokenOut)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    ctx = client_ctx(request)
    ip = ctx["ip"] or "unknown"
    now = time()
    _attempts[ip] = [t for t in _attempts[ip] if now - t < WINDOW]
    if len(_attempts[ip]) >= MAX_TRY:
        raise HTTPException(429, "Too many login attempts, try later")
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not user.is_active or not verify_password(form.password, user.password_hash):
        _attempts[ip].append(now)
        audit(db, user.id if user else None, "auth.login_failed", ctx, {"email": form.username})
        db.commit()
        publish("auth.login_failed", {"email": form.username, **ctx})
        raise HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"})
    audit(db, user.id, "auth.login", ctx)
    db.commit()
    publish("auth.login", {"user_id": user.id, **ctx})
    return TokenOut(access_token=create_token(user.id, user.role))