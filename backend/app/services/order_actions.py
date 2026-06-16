from datetime import datetime, timezone

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.models.log import ToolExecutionLog
from app.models.order import Order, OrderStatus, RefundStatus
from app.schemas.order import (
    OrderAction,
    OrderActionResponse,
    OrderActionResultCode,
    RefundRequest,
    ToolCallResult,
)


def track_order(
    session: Session,
    order_id: str,
    email: str,
    interaction_log_id: int | None = None,
) -> ToolCallResult:
    try:
        order = _find_order(session=session, order_id=order_id, email=email)
        if order is None:
            response = OrderActionResponse(
                tool_name=OrderAction.track_order,
                result_code=OrderActionResultCode.order_not_found,
                message="No order matched that order ID and email.",
                order_id=order_id,
            )
        else:
            response = OrderActionResponse(
                tool_name=OrderAction.track_order,
                result_code=OrderActionResultCode.order_found,
                message="Order found.",
                order_id=order.order_id,
                order_status=order.status,
                refund_status=order.refund_status,
                tracking_number=order.tracking_number,
            )
        return _log_and_return(session, response, {"order_id": order_id, "email": email}, interaction_log_id)
    except SQLAlchemyError:
        return _database_unavailable(OrderAction.track_order, {"order_id": order_id, "email": email})


def cancel_order(
    session: Session,
    order_id: str,
    email: str,
    interaction_log_id: int | None = None,
) -> ToolCallResult:
    try:
        order = _find_order(session=session, order_id=order_id, email=email)
        if order is None:
            response = OrderActionResponse(
                tool_name=OrderAction.cancel_order,
                result_code=OrderActionResultCode.order_not_found,
                message="No order matched that order ID and email.",
                order_id=order_id,
            )
            return _log_and_return(session, response, {"order_id": order_id, "email": email}, interaction_log_id)

        if order.status != OrderStatus.processing:
            response = OrderActionResponse(
                tool_name=OrderAction.cancel_order,
                result_code=OrderActionResultCode.cancellation_not_allowed,
                message="This order cannot be cancelled because it is no longer processing.",
                order_id=order.order_id,
                order_status=order.status,
                refund_status=order.refund_status,
                tracking_number=order.tracking_number,
            )
            return _log_and_return(session, response, {"order_id": order_id, "email": email}, interaction_log_id)

        order.status = OrderStatus.cancelled
        order.updated_at = datetime.now(timezone.utc)
        session.add(order)
        response = OrderActionResponse(
            tool_name=OrderAction.cancel_order,
            result_code=OrderActionResultCode.cancellation_succeeded,
            message="Order cancelled.",
            order_id=order.order_id,
            order_status=order.status,
            refund_status=order.refund_status,
            tracking_number=order.tracking_number,
        )
        return _log_and_return(session, response, {"order_id": order_id, "email": email}, interaction_log_id)
    except SQLAlchemyError:
        return _database_unavailable(OrderAction.cancel_order, {"order_id": order_id, "email": email})


def request_refund(
    session: Session,
    request: RefundRequest,
    interaction_log_id: int | None = None,
) -> ToolCallResult:
    tool_args = {
        "order_id": request.order_id,
        "email": str(request.email),
        "reason": request.reason,
    }
    try:
        order = _find_order(session=session, order_id=request.order_id, email=str(request.email))
        if order is None:
            response = OrderActionResponse(
                tool_name=OrderAction.request_refund,
                result_code=OrderActionResultCode.order_not_found,
                message="No order matched that order ID and email.",
                order_id=request.order_id,
            )
            return _log_and_return(session, response, tool_args, interaction_log_id)

        if order.status != OrderStatus.delivered or order.refund_status != RefundStatus.not_requested:
            response = OrderActionResponse(
                tool_name=OrderAction.request_refund,
                result_code=OrderActionResultCode.refund_not_allowed,
                message="A refund request is only available for delivered orders with no existing refund request.",
                order_id=order.order_id,
                order_status=order.status,
                refund_status=order.refund_status,
                tracking_number=order.tracking_number,
            )
            return _log_and_return(session, response, tool_args, interaction_log_id)

        order.refund_status = RefundStatus.requested
        order.updated_at = datetime.now(timezone.utc)
        session.add(order)
        response = OrderActionResponse(
            tool_name=OrderAction.request_refund,
            result_code=OrderActionResultCode.refund_requested,
            message="Refund request created.",
            order_id=order.order_id,
            order_status=order.status,
            refund_status=order.refund_status,
            tracking_number=order.tracking_number,
        )
        return _log_and_return(session, response, tool_args, interaction_log_id)
    except SQLAlchemyError:
        return _database_unavailable(OrderAction.request_refund, tool_args)


def missing_required_fields(tool_name: OrderAction, tool_args: dict) -> ToolCallResult:
    return ToolCallResult(
        tool_name=tool_name,
        tool_args=tool_args,
        result_code=OrderActionResultCode.missing_required_fields,
        message="Order ID and email are required for this order action.",
    )


def _find_order(session: Session, order_id: str, email: str) -> Order | None:
    return session.exec(
        select(Order).where(
            Order.order_id == order_id,
            Order.customer_email == email,
        )
    ).first()


def _log_and_return(
    session: Session,
    response: OrderActionResponse,
    tool_args: dict,
    interaction_log_id: int | None = None,
) -> ToolCallResult:
    log = ToolExecutionLog(
        interaction_log_id=interaction_log_id,
        tool_name=response.tool_name.value,
        tool_args=tool_args,
        result_code=response.result_code.value,
        result_payload=response.model_dump(mode="json"),
    )
    session.add(log)
    session.commit()
    session.refresh(log)

    response_data = response.model_dump()
    response_data["audit_id"] = log.id
    return ToolCallResult(**response_data, tool_args=tool_args)


def _database_unavailable(tool_name: OrderAction, tool_args: dict) -> ToolCallResult:
    return ToolCallResult(
        tool_name=tool_name,
        tool_args=tool_args,
        result_code=OrderActionResultCode.database_unavailable,
        message="The order database is unavailable. Check DATABASE_URL and PostgreSQL credentials.",
    )
