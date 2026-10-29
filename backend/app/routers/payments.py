import re
import secrets
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.events import client_ctx
from app.models import PaymentCard, User
from app.schemas import CardIn, CardTokenOut, PayIn, PaymentOut
from app.services import get_order_for, pay_order

router = APIRouter(prefix="/payments", tags=["payments"])


def luhn_ok(pan: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(pan)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def card_brand(pan: str) -> str:
    if pan.startswith("4"):
        return "visa"
    if pan[:2] in ("51", "52", "53", "54", "55"):
        return "mastercard"
    if pan[:2] in ("34", "37"):
        return "amex"
    return "card"


@router.post("/tokens", response_model=CardTokenOut, status_code=201)
def create_token(data: CardIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    pan = re.sub(r"[\s-]", "", data.card_number)
    if not pan.isdigit() or not 13 <= len(pan) <= 19 or not luhn_ok(pan):
        raise HTTPException(422, "Invalid card number")
    today = date.today()
    if (data.exp_year, data.exp_month) < (today.year, today.month):
        raise HTTPException(422, "Card expired")
    card = PaymentCard(
        user_id=user.id,
        token="tok_" + secrets.token_urlsafe(24),
        brand=card_brand(pan),
        last4=pan[-4:],
        exp_month=data.exp_month,
        exp_year=data.exp_year,
    )
    db.add(card)
    db.commit()
    return card


@router.get("/tokens", response_model=list[CardTokenOut])
def list_tokens(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(PaymentCard).where(PaymentCard.user_id == user.id).order_by(PaymentCard.id)).all()


@router.delete("/tokens/{token}", status_code=204)
def delete_token(token: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    card = db.scalar(select(PaymentCard).where(PaymentCard.token == token, PaymentCard.user_id == user.id))
    if not card:
        raise HTTPException(404, "Token not found")
    db.delete(card)
    db.commit()


@router.post("/orders/{order_id}/pay", response_model=PaymentOut)
def pay(
    order_id: int,
    data: PayIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = get_order_for(db, user, order_id)
    if order.buyer_id != user.id:
        raise HTTPException(403, "Only the buyer can pay for this order")
    card = db.scalar(select(PaymentCard).where(PaymentCard.token == data.token, PaymentCard.user_id == user.id))
    if not card:
        raise HTTPException(404, "Token not found")
    return pay_order(db, order, card, client_ctx(request))


@router.get("/orders/{order_id}", response_model=list[PaymentOut])
def order_payments(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_order_for(db, user, order_id).payments