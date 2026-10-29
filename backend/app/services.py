import secrets
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import hooks
from app.currency import convert
from app.events import audit, publish
from app.models import (
    Address,
    CartItem,
    Order,
    OrderItem,
    Payment,
    PaymentCard,
    Product,
    User,
)

TRANSITIONS = {
    "created": {"cancelled"},
    "paid": {"packed", "cancelled", "refunded"},
    "packed": {"shipped", "cancelled", "refunded"},
    "shipped": {"delivered", "refunded"},
    "delivered": {"refunded"},
    "cancelled": set(),
    "refunded": set(),
}


def order_event(order: Order) -> dict:
    return {
        "order_id": order.id,
        "buyer_id": order.buyer_id,
        "status": order.status,
        "total": str(order.total),
        "currency": order.currency,
    }


def get_order_for(db: Session, user: User, order_id: int) -> Order:
    order = db.scalar(
        select(Order)
        .options(selectinload(Order.items), selectinload(Order.payments))
        .where(Order.id == order_id)
    )
    if not order:
        raise HTTPException(404, "Order not found")
    if user.role == "admin" or order.buyer_id == user.id or any(i.seller_id == user.id for i in order.items):
        return order
    raise HTTPException(404, "Order not found")


def checkout(db: Session, user: User, address_id: int, currency: str, ctx: dict) -> Order:
    address = db.get(Address, address_id)
    if not address or address.user_id != user.id:
        raise HTTPException(404, "Address not found")
    lines = db.scalars(
        select(CartItem).where(CartItem.user_id == user.id).order_by(CartItem.product_id)
    ).all()
    if not lines:
        raise HTTPException(400, "Cart is empty")
    ids = [line.product_id for line in lines]
    products = {
        p.id: p
        for p in db.scalars(
            select(Product).where(Product.id.in_(ids)).order_by(Product.id).with_for_update()
        )
    }
    items = []
    subtotal = Decimal("0.00")
    for line in lines:
        p = products.get(line.product_id)
        if not p or not p.is_active:
            raise HTTPException(409, f"Product {line.product_id} is unavailable")
        if p.stock < line.quantity:
            raise HTTPException(409, f"Insufficient stock for {p.name}")
        unit = convert(p.price, p.currency, currency)
        subtotal += unit * line.quantity
        items.append((p, line.quantity, unit))
    cross_border = any(p.origin_country != address.country for p, _, _ in items)
    shipping = convert(Decimal("25") if cross_border else Decimal("10"), "USD", currency)
    total = subtotal + shipping
    shipping_address = {
        "full_name": address.full_name,
        "line1": address.line1,
        "line2": address.line2,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
    }
    decision = hooks.compliance_check(
        {
            "user_id": user.id,
            "buyer_region": user.region,
            "ship_to_country": address.country,
            "currency": currency,
            "total": str(total),
            "items": [
                {
                    "product_id": p.id,
                    "name": p.name,
                    "hs_code": p.hs_code,
                    "origin_country": p.origin_country,
                    "quantity": qty,
                    "unit_price": str(unit),
                }
                for p, qty, unit in items
            ],
        }
    )
    verdict = decision.get("decision", "approved")
    if verdict in ("rejected", "blocked"):
        audit(db, user.id, "order.compliance_rejected", ctx, decision)
        db.commit()
        raise HTTPException(
            422, {"message": "Order rejected by compliance", "reasons": decision.get("reasons", [])}
        )
    order = Order(
        buyer_id=user.id,
        status="created",
        currency=currency,
        subtotal=subtotal,
        shipping_cost=shipping,
        total=total,
        shipping_address=shipping_address,
        compliance_decision=verdict,
        on_hold=verdict == "review",
        hold_reason="compliance_review" if verdict == "review" else None,
    )
    order.items = [
        OrderItem(
            product_id=p.id,
            seller_id=p.seller_id,
            name=p.name,
            hs_code=p.hs_code,
            origin_country=p.origin_country,
            unit_price=unit,
            quantity=qty,
        )
        for p, qty, unit in items
    ]
    for p, qty, _ in items:
        p.stock -= qty
    for line in lines:
        db.delete(line)
    db.add(order)
    db.flush()
    audit(db, user.id, "order.created", ctx, {"order_id": order.id, "total": str(total)})
    db.commit()
    publish("order.created", order_event(order))
    return order


def mock_charge(card: PaymentCard):
    if card.last4 == "0002":
        return False, "card_declined"
    if card.last4 == "9995":
        return False, "insufficient_funds"
    return True, "mock_" + secrets.token_hex(8)


def capture(db: Session, order: Order, payment: Payment, card: PaymentCard) -> Payment:
    ok, ref = mock_charge(card)
    if ok:
        payment.status = "succeeded"
        payment.provider_ref = ref
        order.status = "paid"
        db.commit()
        publish("payment.completed", {"order_id": order.id, "payment_id": payment.id, "amount": str(payment.amount), "currency": payment.currency})
        publish("order.paid", order_event(order))
        return payment
    payment.status = "failed"
    payment.failure_reason = ref
    db.commit()
    publish("payment.failed", {"order_id": order.id, "payment_id": payment.id, "reason": ref})
    raise HTTPException(402, f"Payment failed: {ref}")


def pay_order(db: Session, order: Order, card: PaymentCard, ctx: dict) -> Payment:
    if order.status != "created":
        raise HTTPException(409, "Order is not payable")
    if order.on_hold:
        raise HTTPException(409, "Order is on hold")
    payment = Payment(
        order_id=order.id,
        card_token=card.token,
        amount=order.total,
        currency=order.currency,
        status="pending",
    )
    db.add(payment)
    db.flush()
    buyer = db.get(User, order.buyer_id)
    result = hooks.fraud_score(
        {
            "order_id": order.id,
            "user_id": order.buyer_id,
            "buyer_region": buyer.region if buyer else None,
            "amount": str(order.total),
            "currency": order.currency,
            "card": {"brand": card.brand, "last4": card.last4},
            "ship_to_country": order.shipping_address.get("country"),
            "ip": ctx.get("ip"),
            "user_agent": ctx.get("user_agent"),
        }
    )
    decision = result.get("decision", "allow")
    order.fraud_decision = decision
    order.fraud_score = result.get("score")
    audit(db, order.buyer_id, "payment.attempt", ctx, {"order_id": order.id, "fraud_decision": decision})
    if decision == "block":
        payment.status = "failed"
        payment.failure_reason = "fraud_blocked"
        db.commit()
        publish("payment.failed", {"order_id": order.id, "payment_id": payment.id, "reason": "fraud_blocked"})
        raise HTTPException(403, "Payment blocked by fraud policy")
    if decision == "review":
        payment.status = "pending_review"
        order.on_hold = True
        order.hold_reason = "fraud_review"
        db.commit()
        publish("payment.review", {"order_id": order.id, "payment_id": payment.id})
        return payment
    return capture(db, order, payment, card)


def place_hold(db: Session, order: Order, reason: str, user: User, ctx: dict) -> Order:
    order.on_hold = True
    order.hold_reason = reason
    audit(db, user.id, "order.hold", ctx, {"order_id": order.id, "reason": reason})
    db.commit()
    publish("order.hold", order_event(order))
    return order


def release_hold(db: Session, order: Order, user: User, ctx: dict) -> Order:
    if not order.on_hold:
        raise HTTPException(409, "Order is not on hold")
    order.on_hold = False
    order.hold_reason = None
    audit(db, user.id, "order.release", ctx, {"order_id": order.id})
    pending = db.scalar(
        select(Payment)
        .where(Payment.order_id == order.id, Payment.status == "pending_review")
        .order_by(Payment.id.desc())
    )
    if not pending:
        db.commit()
        publish("order.released", order_event(order))
        return order
    card = db.scalar(select(PaymentCard).where(PaymentCard.token == pending.card_token))
    if not card:
        pending.status = "failed"
        pending.failure_reason = "token_missing"
        db.commit()
        raise HTTPException(409, "Card token no longer exists")
    capture(db, order, pending, card)
    publish("order.released", order_event(order))
    return order


def change_status(db: Session, order: Order, user: User, target: str, ctx: dict) -> Order:
    if user.role == "admin":
        pass
    elif user.role == "seller" and any(i.seller_id == user.id for i in order.items):
        if target not in ("packed", "shipped", "delivered"):
            raise HTTPException(403, "Sellers can only pack, ship or deliver")
    elif order.buyer_id == user.id:
        if target != "cancelled":
            raise HTTPException(403, "Buyers can only cancel")
    else:
        raise HTTPException(403, "Insufficient permissions")
    if order.on_hold and user.role != "admin":
        raise HTTPException(409, "Order is on hold")
    if user.role != "admin" and order.buyer_id == user.id and target == "cancelled" and order.status not in ("created", "paid"):
        raise HTTPException(409, "Order can no longer be cancelled by the buyer")
    if target not in TRANSITIONS[order.status]:
        raise HTTPException(409, f"Cannot move order from {order.status} to {target}")
    if target == "cancelled":
        for item in order.items:
            p = db.get(Product, item.product_id, with_for_update=True)
            if p:
                p.stock += item.quantity
    if target in ("cancelled", "refunded"):
        for pay in order.payments:
            if pay.status == "succeeded":
                pay.status = "refunded"
            elif pay.status == "pending_review":
                pay.status = "cancelled"
        order.on_hold = False
        order.hold_reason = None
    previous = order.status
    order.status = target
    audit(db, user.id, "order.status_changed", ctx, {"order_id": order.id, "from": previous, "to": target})
    db.commit()
    publish("order.status_changed", {**order_event(order), "previous": previous})
    return order