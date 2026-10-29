from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.currency import convert
from app.database import get_db
from app.deps import get_current_user
from app.models import CartItem, Product, User
from app.schemas import CartAddIn, CartLineOut, CartOut, CartUpdateIn, Currency

router = APIRouter(prefix="/cart", tags=["cart"])


def cart_view(db: Session, user: User, currency: str) -> CartOut:
    rows = db.scalars(
        select(CartItem)
        .where(CartItem.user_id == user.id)
        .options(selectinload(CartItem.product).selectinload(Product.seller))
        .order_by(CartItem.id)
    ).all()
    lines = []
    subtotal = Decimal("0.00")
    for r in rows:
        p = r.product
        unit = convert(p.price, p.currency, currency)
        line_total = unit * r.quantity
        subtotal += line_total
        lines.append(
            CartLineOut(
                product_id=p.id,
                name=p.name,
                image_url=p.image_url,
                seller_name=p.seller.full_name,
                unit_price=unit,
                quantity=r.quantity,
                line_total=line_total,
                available=p.is_active and p.stock >= r.quantity,
            )
        )
    return CartOut(currency=currency, items=lines, subtotal=subtotal)


@router.get("", response_model=CartOut)
def get_cart(currency: Currency = "USD", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return cart_view(db, user, currency)


@router.post("/items", response_model=CartOut)
def add_item(
    data: CartAddIn,
    currency: Currency = "USD",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.get(Product, data.product_id)
    if not p or not p.is_active:
        raise HTTPException(404, "Product not found")
    item = db.scalar(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == p.id)
    )
    qty = (item.quantity if item else 0) + data.quantity
    if qty > p.stock:
        raise HTTPException(409, "Not enough stock")
    if item:
        item.quantity = qty
    else:
        db.add(CartItem(user_id=user.id, product_id=p.id, quantity=qty))
    db.commit()
    return cart_view(db, user, currency)


@router.patch("/items/{product_id}", response_model=CartOut)
def update_item(
    product_id: int,
    data: CartUpdateIn,
    currency: Currency = "USD",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.scalar(
        select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)
    )
    if not item:
        raise HTTPException(404, "Item not in cart")
    if data.quantity == 0:
        db.delete(item)
    else:
        p = db.get(Product, product_id)
        if not p or not p.is_active or data.quantity > p.stock:
            raise HTTPException(409, "Not enough stock")
        item.quantity = data.quantity
    db.commit()
    return cart_view(db, user, currency)


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_item(
    product_id: int,
    currency: Currency = "USD",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.execute(delete(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id))
    db.commit()
    return cart_view(db, user, currency)


@router.delete("", response_model=CartOut)
def clear_cart(currency: Currency = "USD", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    db.commit()
    return cart_view(db, user, currency)