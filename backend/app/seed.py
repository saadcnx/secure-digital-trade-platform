from decimal import Decimal

from sqlalchemy import select

from app import models  # noqa: F401
from app.database import Base, SessionLocal, engine
from app.models import Address, Category, Product, User
from app.security import hash_password


def ensure_user(db, email, password, name, role, region):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=name,
            role=role,
            region=region,
        )
        db.add(user)
        db.flush()
    return user


def ensure_category(db, name):
    cat = db.scalar(select(Category).where(Category.name == name))
    if not cat:
        cat = Category(name=name, slug="-".join(name.lower().split()))
        db.add(cat)
        db.flush()
    return cat


def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        ensure_user(db, "admin@tradeshield.test", "Admin@12345", "Platform Admin", "admin", "OTHER")
        seller1 = ensure_user(db, "seller1@tradeshield.test", "Seller@12345", "Karachi Crafts", "seller", "PK")
        seller2 = ensure_user(db, "seller2@tradeshield.test", "Seller@12345", "Berlin Gadgets", "seller", "EU")
        buyer = ensure_user(db, "buyer@tradeshield.test", "Buyer@12345", "Test Buyer", "buyer", "US")

        if not db.scalar(select(Address).where(Address.user_id == buyer.id).limit(1)):
            db.add(
                Address(
                    user_id=buyer.id,
                    full_name="Test Buyer",
                    line1="123 Market Street",
                    city="San Francisco",
                    state="CA",
                    postal_code="94105",
                    country="US",
                    is_default=True,
                )
            )

        textiles = ensure_category(db, "Textiles")
        electronics = ensure_category(db, "Electronics")
        food = ensure_category(db, "Food and Beverages")
        sports = ensure_category(db, "Sports")

        if not db.scalar(select(Product).limit(1)):
            catalog = [
                (seller1, textiles, "Hand-Woven Cotton Scarf", "Soft hand-woven cotton scarf.", "24.00", "USD", 120, "PK"),
                (seller1, textiles, "Embroidered Silk Shawl", "Traditional embroidered silk shawl.", "85.00", "USD", 40, "PK"),
                (seller1, sports, "Hand-Stitched Football", "Match quality stitched football.", "30.00", "USD", 75, "PK"),
                (seller1, food, "Himalayan Pink Salt 1kg", "Natural pink salt.", "6500.00", "PKR", 300, "PK"),
                (seller2, electronics, "Wireless Earbuds", "Bluetooth 5.3 earbuds with case.", "59.00", "EUR", 80, "DE"),
                (seller2, electronics, "USB-C Fast Charger 65W", "Compact GaN charger.", "35.00", "EUR", 150, "DE"),
                (seller2, electronics, "Mechanical Keyboard", "Hot-swappable 75% keyboard.", "99.00", "EUR", 25, "DE"),
                (seller2, food, "Single-Origin Coffee 500g", "Freshly roasted beans.", "18.50", "GBP", 200, "GB"),
            ]
            for seller, cat, name, desc, price, cur, stock, origin in catalog:
                db.add(
                    Product(
                        seller_id=seller.id,
                        category_id=cat.id,
                        name=name,
                        description=desc,
                        image_url="https://picsum.photos/seed/" + "-".join(name.lower().split()) + "/400/300",
                        price=Decimal(price),
                        currency=cur,
                        stock=stock,
                        origin_country=origin,
                        hs_code=None,
                    )
                )
        db.commit()


if __name__ == "__main__":
    main()