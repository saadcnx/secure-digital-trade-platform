from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.currency import convert
from app.database import get_db
from app.deps import get_current_user, require_roles
from app.models import Category, Product, User
from app.schemas import (
    CategoryIn,
    CategoryOut,
    Currency,
    ProductIn,
    ProductOut,
    ProductUpdate,
)

router = APIRouter(tags=["catalog"])


def to_out(p: Product, currency: Optional[str] = None) -> ProductOut:
    out = ProductOut.model_validate(p)
    out.seller_name = p.seller.full_name
    if currency:
        out.display_price = convert(p.price, p.currency, currency)
        out.display_currency = currency
    return out


def _check_category(db: Session, category_id: Optional[int]) -> None:
    if category_id is not None and not db.get(Category, category_id):
        raise HTTPException(422, "Category does not exist")


def _owned_product(db: Session, user: User, product_id: int) -> Product:
    p = db.get(Product, product_id)
    if not p or (user.role != "admin" and p.seller_id != user.id):
        raise HTTPException(404, "Product not found")
    return p


@router.get("/categories", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.name)).all()


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(
    data: CategoryIn,
    user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    slug = "-".join(data.name.lower().split())
    if db.scalar(select(Category).where((Category.name == data.name) | (Category.slug == slug))):
        raise HTTPException(409, "Category already exists")
    category = Category(name=data.name, slug=slug)
    db.add(category)
    db.commit()
    return category


@router.get("/products", response_model=list[ProductOut])
def list_products(
    q: Optional[str] = None,
    category_id: Optional[int] = None,
    seller_id: Optional[int] = None,
    origin_country: Optional[str] = None,
    currency: Optional[Currency] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Product).options(selectinload(Product.seller)).where(Product.is_active.is_(True))
    if q:
        stmt = stmt.where(Product.name.ilike(f"%{q}%"))
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if seller_id is not None:
        stmt = stmt.where(Product.seller_id == seller_id)
    if origin_country:
        stmt = stmt.where(Product.origin_country == origin_country.upper())
    rows = db.scalars(stmt.order_by(Product.id.desc()).limit(limit).offset(offset)).all()
    return [to_out(p, currency) for p in rows]


@router.get("/products/mine", response_model=list[ProductOut])
def my_products(
    user: User = Depends(require_roles("seller", "admin")),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Product)
        .options(selectinload(Product.seller))
        .where(Product.seller_id == user.id)
        .order_by(Product.id.desc())
    ).all()
    return [to_out(p) for p in rows]


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, currency: Optional[Currency] = None, db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p or not p.is_active:
        raise HTTPException(404, "Product not found")
    return to_out(p, currency)


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    data: ProductIn,
    user: User = Depends(require_roles("seller", "admin")),
    db: Session = Depends(get_db),
):
    _check_category(db, data.category_id)
    p = Product(seller_id=user.id, **data.model_dump())
    db.add(p)
    db.commit()
    return to_out(p)


@router.patch("/products/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    data: ProductUpdate,
    user: User = Depends(require_roles("seller", "admin")),
    db: Session = Depends(get_db),
):
    p = _owned_product(db, user, product_id)
    changes = data.model_dump(exclude_unset=True)
    _check_category(db, changes.get("category_id"))
    for key, value in changes.items():
        setattr(p, key, value)
    db.commit()
    return to_out(p)


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    user: User = Depends(require_roles("seller", "admin")),
    db: Session = Depends(get_db),
):
    p = _owned_product(db, user, product_id)
    p.is_active = False
    db.commit()