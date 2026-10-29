import hmac
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import SERVICE_API_KEY
from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.events import audit, client_ctx, publish
from app.models import Order, Shipment, ShipmentEvent, User
from app.schemas import ShipmentCreateIn, ShipmentEventIn, ShipmentOut
from app.services import get_order_for, order_event

router = APIRouter(prefix="/shipments", tags=["shipments"])


def _staff_order(db: Session, user: User, order_id: int) -> Order:
    if user.role not in ("admin", "seller"):
        raise HTTPException(403, "Insufficient permissions")
    order = get_order_for(db, user, order_id)
    if user.role != "admin" and not any(i.seller_id == user.id for i in order.items):
        raise HTTPException(403, "Not your order")
    return order


def _load(db: Session, shipment_id: int) -> Shipment:
    s = db.scalar(
        select(Shipment).options(selectinload(Shipment.events)).where(Shipment.id == shipment_id)
    )
    if not s:
        raise HTTPException(404, "Shipment not found")
    return s


@router.post("/orders/{order_id}", response_model=ShipmentOut, status_code=201)
def create_shipment(
    order_id: int,
    data: ShipmentCreateIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = _staff_order(db, user, order_id)
    if order.on_hold:
        raise HTTPException(409, "Order is on hold")
    if order.status not in ("paid", "packed", "shipped"):
        raise HTTPException(409, "Order must be paid before it can be shipped")
    if db.scalar(select(Shipment.id).where(Shipment.order_id == order.id)):
        raise HTTPException(409, "Shipment already exists")
    number = data.tracking_number or "TS" + secrets.token_hex(5).upper()
    if db.scalar(select(Shipment.id).where(Shipment.tracking_number == number)):
        raise HTTPException(409, "Tracking number already used")
    ctx = client_ctx(request)
    shipment = Shipment(
        order_id=order.id,
        carrier=data.carrier,
        tracking_number=number,
        status="label_created",
        created_by=user.id,
    )
    shipment.events.append(
        ShipmentEvent(status="label_created", location=data.origin or "Seller warehouse", source=user.role)
    )
    previous = order.status
    order.status = "shipped"
    db.add(shipment)
    db.flush()
    audit(db, user.id, "shipment.created", ctx, {"order_id": order.id, "shipment_id": shipment.id, "tracking_number": number})
    if previous != "shipped":
        audit(db, user.id, "order.status_changed", ctx, {"order_id": order.id, "from": previous, "to": "shipped"})
    db.commit()
    publish("shipment.created", {"shipment_id": shipment.id, "order_id": order.id, "tracking_number": number, "carrier": data.carrier})
    if previous != "shipped":
        publish("order.status_changed", {**order_event(order), "previous": previous})
    return shipment


@router.get("/orders/{order_id}", response_model=ShipmentOut)
def order_shipment(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = get_order_for(db, user, order_id)
    s = db.scalar(
        select(Shipment).options(selectinload(Shipment.events)).where(Shipment.order_id == order.id)
    )
    if not s:
        raise HTTPException(404, "No shipment yet")
    return s


@router.post("/{shipment_id}/events", response_model=ShipmentOut, status_code=201)
def add_event(
    shipment_id: int,
    data: ShipmentEventIn,
    request: Request,
    x_service_key: Optional[str] = Header(None),
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    s = _load(db, shipment_id)
    from_service = bool(
        SERVICE_API_KEY and x_service_key and hmac.compare_digest(x_service_key, SERVICE_API_KEY)
    )
    if from_service:
        order = db.get(Order, s.order_id)
        actor, source = None, "service"
    else:
        if not user:
            raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
        order = _staff_order(db, user, s.order_id)
        actor, source = user.id, user.role
    if order.status in ("cancelled", "refunded"):
        raise HTTPException(409, "Order is closed")
    ev = ShipmentEvent(
        status=data.status,
        location=data.location,
        latitude=data.latitude,
        longitude=data.longitude,
        temperature=data.temperature,
        note=data.note,
        source=source,
    )
    if data.timestamp:
        ev.created_at = data.timestamp
    s.events.append(ev)
    s.status = data.status
    previous = order.status
    if data.status == "delivered" and order.status == "shipped":
        order.status = "delivered"
    db.flush()
    changed = order.status != previous
    if not from_service:
        audit(
            db,
            actor,
            "shipment.event",
            client_ctx(request),
            {"shipment_id": s.id, "order_id": order.id, "status": data.status, "location": data.location, "temperature": data.temperature},
        )
    if changed:
        audit(db, actor, "order.status_changed", client_ctx(request), {"order_id": order.id, "from": previous, "to": order.status})
    db.commit()
    publish(
        "shipment.updated",
        {
            "shipment_id": s.id,
            "order_id": order.id,
            "status": data.status,
            "location": data.location,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "temperature": data.temperature,
            "source": source,
        },
    )
    if changed:
        publish("order.status_changed", {**order_event(order), "previous": previous})
    return s