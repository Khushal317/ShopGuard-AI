import re

from sqlmodel import Session

from app.schemas.order import OrderAction, RefundRequest, ToolCallRequest, ToolCallResult
from app.services.order_actions import cancel_order, missing_required_fields, request_refund, track_order

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
ORDER_ID_PATTERN = re.compile(r"(?:order\s*#?|#)\s*([A-Za-z0-9-]+)", re.IGNORECASE)


def detect_order_tool(message: str) -> ToolCallRequest | None:
    lowered = message.lower()
    if not any(keyword in lowered for keyword in ["order", "tracking", "track", "cancel", "refund"]):
        return None

    if "cancel" in lowered:
        tool_name = OrderAction.cancel_order
    elif "refund" in lowered or "return my order" in lowered:
        tool_name = OrderAction.request_refund
    else:
        tool_name = OrderAction.track_order

    email_match = EMAIL_PATTERN.search(message)
    order_match = ORDER_ID_PATTERN.search(message)

    return ToolCallRequest(
        tool_name=tool_name,
        order_id=order_match.group(1) if order_match else None,
        email=email_match.group(0) if email_match else None,
        reason=_extract_reason(message) if tool_name == OrderAction.request_refund else None,
    )


def execute_tool_call(
    session: Session,
    tool_call: ToolCallRequest,
    interaction_log_id: int | None = None,
) -> ToolCallResult:
    tool_args = tool_call.model_dump(mode="json", exclude_none=True)
    if not tool_call.order_id or not tool_call.email:
        return missing_required_fields(tool_call.tool_name, tool_args)

    if tool_call.tool_name == OrderAction.track_order:
        return track_order(
            session=session,
            order_id=tool_call.order_id,
            email=str(tool_call.email),
            interaction_log_id=interaction_log_id,
        )

    if tool_call.tool_name == OrderAction.cancel_order:
        return cancel_order(
            session=session,
            order_id=tool_call.order_id,
            email=str(tool_call.email),
            interaction_log_id=interaction_log_id,
        )

    return request_refund(
        session=session,
        request=RefundRequest(
            order_id=tool_call.order_id,
            email=tool_call.email,
            reason=tool_call.reason,
        ),
        interaction_log_id=interaction_log_id,
    )


def _extract_reason(message: str) -> str | None:
    reason_match = re.search(r"\b(?:because|reason:)\s*(.+)$", message, flags=re.IGNORECASE)
    if not reason_match:
        return None
    return reason_match.group(1).strip()
