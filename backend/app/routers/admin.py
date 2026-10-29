from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.currency import convert
from app.database import get_db
from app.deps import require_roles
from app.events import audit, client_ctx, publish
from app.models import AuditLog, Order, Product, Review, User
from app.routers.catalog import to_out
from app.routers.reviews import review_out
from app.schemas import AdminReviewOut, AdminUserOut, AdminUserUpdate, AuditOut, ProductOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def stats(admin: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    by_status = {s: c for s, c in db.execute(select(Order.status, func.count()).group_by(Order.status)).all()}
    rows = db.execute(
        select(Order.total, Order.currency).where(Order.status.in_(("paid", "packed", "shipped", "delivered")))
    ).all()
    revenue = sum((convert(t, c, "USD") for t, c in rows), Decimal("0"))
    return {
        "users": db.scalar(select(func.count(User.id))),
        "products": db.scalar(select(func.count(Product.id))),
        "reviews": db.scalar(select(func.count(Review.id))),
        "orders": sum(by_status.values()),
        "orders_by_status": by_status,
        "on_hold": db.scalar(select(func.count(Order.id)).where(Order.on_hold.is_(True))),
        "revenue_usd": str(revenue.quantize(Decimal("0.01"))),
    }


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    q: Optional[str] = None,
    role: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    stmt = select(User).order_by(User.id)
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%") | User.full_name.ilike(f"%{q}%"))
    if role:
        stmt = stmt.where(User.role == role)
    return db.scalars(stmt.limit(limit).offset(offset)).all()


@router.patch("/users/{user_id}", response_model=AdminUserOut)
def update_user(
    user_id: int,
    data: AdminUserUpdate,
    request: Request,
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    changes = data.model_dump(exclude_none=True)
    if u.id == admin.id and (changes.get("is_active") is False or changes.get("role", "admin") != "admin"):
        raise HTTPException(409, "You cannot demote or deactivate yourself")
    for key, value in changes.items():
        setattr(u, key, value)
    audit(db, admin.id, "admin.user_updated", client_ctx(request), {"user_id": u.id, **changes})
    db.commit()
    publish("admin.user_updated", {"user_id": u.id, **changes})
    return u


@router.get("/products", response_model=list[ProductOut])
def list_products(
    q: Optional[str] = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    stmt = select(Product).options(selectinload(Product.seller)).order_by(Product.id.desc())
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    return [to_out(p) for p in db.scalars(stmt.limit(limit).offset(offset)).all()]


@router.get("/reviews", response_model=list[AdminReviewOut])
def list_reviews(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Review)
        .options(selectinload(Review.user), selectinload(Review.product))
        .order_by(Review.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [AdminReviewOut(**review_out(r).model_dump(), ip=r.ip) for r in rows]


@router.get("/audit", response_model=list[AuditOut])
def audit_logs(
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.id.desc())
    if action:
        stmt = stmt.where(AuditLog.action.ilike(f"{action}%"))
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    return db.scalars(stmt.limit(limit).offset(offset)).all()