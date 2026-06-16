from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


class OrderStatus(str, Enum):
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


class RefundStatus(str, Enum):
    not_requested = "not_requested"
    requested = "requested"
    approved = "approved"
    rejected = "rejected"


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: int | None = Field(default=None, primary_key=True)
    order_id: str = Field(index=True, unique=True)
    customer_email: str = Field(index=True)
    customer_name: str
    status: OrderStatus = Field(default=OrderStatus.processing)
    refund_status: RefundStatus = Field(default=RefundStatus.not_requested)
    total_amount: Decimal = Field(max_digits=10, decimal_places=2)
    currency: str = "USD"
    tracking_number: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    items: list["OrderItem"] = Relationship(back_populates="order")


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    product_sku: str = Field(index=True)
    variant_sku: str = Field(index=True)
    title: str
    quantity: int
    unit_price: Decimal = Field(max_digits=10, decimal_places=2)

    order: Order = Relationship(back_populates="items")

