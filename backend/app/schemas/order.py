from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.order import OrderStatus, RefundStatus


class OrderItemSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_sku: str
    variant_sku: str
    title: str
    quantity: int
    unit_price: Decimal


class OrderSeed(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    customer_email: EmailStr
    customer_name: str
    status: OrderStatus
    refund_status: RefundStatus = RefundStatus.not_requested
    total_amount: Decimal
    currency: str
    tracking_number: str | None = None
    items: list[OrderItemSeed]


class OrderItemRead(OrderItemSeed):
    id: int
    order_id: int


class OrderRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    order_id: str
    customer_email: EmailStr
    customer_name: str
    status: OrderStatus
    refund_status: RefundStatus
    total_amount: Decimal
    currency: str
    tracking_number: str | None
    items: list[OrderItemRead] = []

