from decimal import Decimal
from enum import Enum

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


class OrderAction(str, Enum):
    track_order = "track_order"
    cancel_order = "cancel_order"
    request_refund = "request_refund"


class OrderActionResultCode(str, Enum):
    order_found = "order_found"
    order_not_found = "order_not_found"
    cancellation_succeeded = "cancellation_succeeded"
    cancellation_not_allowed = "cancellation_not_allowed"
    refund_requested = "refund_requested"
    refund_not_allowed = "refund_not_allowed"
    missing_required_fields = "missing_required_fields"
    database_unavailable = "database_unavailable"


class OrderActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str
    email: EmailStr


class RefundRequest(OrderActionRequest):
    reason: str | None = None


class ToolCallRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: OrderAction
    order_id: str | None = None
    email: EmailStr | None = None
    reason: str | None = None


class OrderActionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: OrderAction
    result_code: OrderActionResultCode
    message: str
    order_id: str | None = None
    order_status: OrderStatus | None = None
    refund_status: RefundStatus | None = None
    tracking_number: str | None = None
    audit_id: int | None = None


class ToolCallResult(OrderActionResponse):
    tool_args: dict
