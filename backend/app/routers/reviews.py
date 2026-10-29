from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import get_current_user
from app.events import audit, client_ctx, publish
from app.models import Order, OrderItem, Product, Review, User
from app.schemas import ReviewIn, ReviewListOut, ReviewOut

router = APIRouter(tags=["reviews"])


def review_out(r: Review) -> ReviewOut:
    return ReviewOut(
        id=r.id,
        product_id=r.product_id,
        product_name=r.product.name if r.product else None,
        user_id=r.user_id,
        reviewer_name=r.user.full_name,
        rating=r.rating,
        title=r.title,
        body=r.body,
        verified_purchase=r.verified_purchase,
        created_at=r.created_at,
    )


@router.get("/products/{product_id}/reviews", response_model=ReviewListOut)
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Review)
        .options(selectinload(Review.user), selectinload(Review.product))
        .where(Review.product_id == product_id)
        .order_by(Review.id.desc())
    ).all()
    count = len(rows)
    average = round(sum(r.rating for r in rows) / count, 2) if count else 0.0
    return ReviewListOut(average=average, count=count, items=[review_out(r) for r in rows])


@router.post("/products/{product_id}/reviews", response_model=ReviewOut, status_code=201)
def create_review(
    product_id: int,
    data: ReviewIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = db.get(Product, product_id)
    if not p or not p.is_active:
        raise HTTPException(404, "Product not found")
    if p.seller_id == user.id:
        raise HTTPException(403, "You cannot review your own product")
    if db.scalar(select(Review.id).where(Review.product_id == product_id, Review.user_id == user.id)):
        raise HTTPException(409, "You already reviewed this product")
    verified = (
        db.scalar(
            select(OrderItem.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                Order.buyer_id == user.id,
                OrderItem.product_id == product_id,
                Order.status.in_(("paid", "packed", "shipped", "delivered")),
            )
            .limit(1)
        )
        is not None
    )
    ctx = client_ctx(request)
    r = Review(
        product_id=product_id,
        user_id=user.id,
        rating=data.rating,
        title=data.title,
        body=data.body,
        verified_purchase=verified,
        ip=ctx["ip"],
        user_agent=ctx["user_agent"],
    )
    db.add(r)
    db.flush()
    audit(db, user.id, "review.created", ctx, {"review_id": r.id, "product_id": product_id, "rating": data.rating, "verified": verified})
    db.commit()
    publish(
        "review.created",
        {"review_id": r.id, "product_id": product_id, "user_id": user.id, "rating": data.rating, "verified": verified, **ctx},
    )
    return review_out(r)


@router.delete("/reviews/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.get(Review, review_id)
    if not r or (user.role != "admin" and r.user_id != user.id):
        raise HTTPException(404, "Review not found")
    audit(db, user.id, "review.deleted", client_ctx(request), {"review_id": r.id, "product_id": r.product_id})
    db.delete(r)
    db.commit()
    publish("review.deleted", {"review_id": review_id})