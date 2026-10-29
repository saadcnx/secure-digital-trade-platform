from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import get_current_user, require_roles
from app.events import client_ctx
from app.models import Order, OrderItem, User
from app.schemas import CheckoutIn, HoldIn, OrderOut, StatusIn
from app.services import change_status, checkout, get_order_for, place_hold, release_hold

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/checkout", response_model=OrderOut, status_code=201)
def do_checkout(
    data: CheckoutIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return checkout(db, user, data.address_id, data.currency, client_ctx(request))


@router.get("", response_model=list[OrderOut])
def list_orders(
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.payments))
        .order_by(Order.id.desc())
    )
    if user.role != "admin":
        stmt = stmt.where(or_(Order.buyer_id == user.id, Order.items.any(OrderItem.seller_id == user.id)))
    if status:
        stmt = stmt.where(Order.status == status)
    return db.scalars(stmt.limit(limit).offset(offset)).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_order_for(db, user, order_id)


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_status(
    order_id: int,
    data: StatusIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_for(db, user, order_id)
    return change_status(db, order, user, data.status, client_ctx(request))


@router.post("/{order_id}/hold", response_model=OrderOut)
def hold_order(
    order_id: int,
    data: HoldIn,
    request: Request,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    order = get_order_for(db, user, order_id)
    return place_hold(db, order, data.reason, user, client_ctx(request))


@router.post("/{order_id}/release", response_model=OrderOut)
def release_order(
    order_id: int,
    request: Request,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    order = get_order_for(db, user, order_id)
    return release_hold(db, order, user, client_ctx(request))