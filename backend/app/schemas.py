from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Currency = Literal["USD", "EUR", "PKR", "GBP"]
Region = Literal["EU", "US", "UK", "PK", "OTHER"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=120)
    role: Literal["buyer", "seller"] = "buyer"
    region: Region = "OTHER"


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORM):
    id: int
    email: str
    full_name: str
    role: str
    region: str
    consent_marketing: bool
    consent_analytics: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=120)
    region: Optional[Region] = None
    consent_marketing: Optional[bool] = None
    consent_analytics: Optional[bool] = None


class AddressIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    line1: str = Field(min_length=1, max_length=200)
    line2: Optional[str] = Field(None, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=2, max_length=2)
    is_default: bool = False

    @field_validator("country")
    @classmethod
    def upper_country(cls, v):
        return v.upper()


class AddressOut(AddressIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryOut(ORM):
    id: int
    name: str
    slug: str


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    image_url: Optional[str] = Field(None, max_length=500)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Currency = "USD"
    stock: int = Field(ge=0)
    origin_country: str = Field(min_length=2, max_length=2)
    hs_code: Optional[str] = Field(None, max_length=12)
    category_id: Optional[int] = None

    @field_validator("origin_country")
    @classmethod
    def upper_country(cls, v):
        return v.upper()


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    price: Optional[Decimal] = Field(None, gt=0, max_digits=12, decimal_places=2)
    currency: Optional[Currency] = None
    stock: Optional[int] = Field(None, ge=0)
    origin_country: Optional[str] = Field(None, min_length=2, max_length=2)
    hs_code: Optional[str] = Field(None, max_length=12)
    category_id: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator("origin_country")
    @classmethod
    def upper_country(cls, v):
        return v.upper() if v else v


class ProductOut(ORM):
    id: int
    seller_id: int
    seller_name: Optional[str] = None
    category_id: Optional[int] = None
    name: str
    description: str
    image_url: Optional[str] = None
    price: Decimal
    currency: str
    stock: int
    origin_country: str
    hs_code: Optional[str] = None
    is_active: bool
    created_at: datetime
    display_price: Optional[Decimal] = None
    display_currency: Optional[str] = None


class CartAddIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=100)


class CartUpdateIn(BaseModel):
    quantity: int = Field(ge=0, le=100)


class CartLineOut(BaseModel):
    product_id: int
    name: str
    image_url: Optional[str] = None
    seller_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    available: bool


class CartOut(BaseModel):
    currency: str
    items: list[CartLineOut]
    subtotal: Decimal


class CheckoutIn(BaseModel):
    address_id: int
    currency: Currency = "USD"


class OrderItemOut(ORM):
    product_id: int
    name: str
    hs_code: Optional[str] = None
    origin_country: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class PaymentOut(ORM):
    id: int
    order_id: int
    amount: Decimal
    currency: str
    status: str
    provider_ref: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime


class OrderOut(ORM):
    id: int
    buyer_id: int
    status: str
    currency: str
    subtotal: Decimal
    shipping_cost: Decimal
    total: Decimal
    shipping_address: dict
    on_hold: bool
    hold_reason: Optional[str] = None
    compliance_decision: Optional[str] = None
    fraud_decision: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: list[OrderItemOut]
    payments: list[PaymentOut]


class StatusIn(BaseModel):
    status: Literal["packed", "shipped", "delivered", "cancelled", "refunded"]


class HoldIn(BaseModel):
    reason: str = Field(min_length=1, max_length=200)


class CardIn(BaseModel):
    card_number: str = Field(min_length=12, max_length=23)
    exp_month: int = Field(ge=1, le=12)
    exp_year: int = Field(ge=2000, le=2100)
    cvv: str = Field(pattern=r"^\d{3,4}$")
    holder_name: str = Field(min_length=1, max_length=120)


class CardTokenOut(ORM):
    token: str
    brand: str
    last4: str
    exp_month: int
    exp_year: int


class PayIn(BaseModel):
    token: str