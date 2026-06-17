from sqlmodel import select

from app.models.log import ToolExecutionLog
from app.models.order import Order, OrderStatus, RefundStatus
from app.schemas.order import RefundRequest
from app.services.order_actions import cancel_order, request_refund, track_order
from app.services.rag_chat import answer_chat


def test_track_order_success_and_invalid_email(test_session) -> None:
    success = track_order(test_session, "9982", "maya@example.com")
    failure = track_order(test_session, "9982", "wrong@example.com")

    assert success.result_code == "order_found"
    assert success.order_status == OrderStatus.processing
    assert failure.result_code == "order_not_found"


def test_cancel_order_allowed_and_denied(test_session) -> None:
    allowed = cancel_order(test_session, "9982", "maya@example.com")
    denied = cancel_order(test_session, "10031", "liam@example.com")
    order = test_session.exec(select(Order).where(Order.order_id == "9982")).first()

    assert allowed.result_code == "cancellation_succeeded"
    assert order.status == OrderStatus.cancelled
    assert denied.result_code == "cancellation_not_allowed"


def test_refund_request_allowed(test_session) -> None:
    response = request_refund(
        test_session,
        RefundRequest(order_id="10044", email="sofia@example.com", reason="Changed mind"),
    )
    order = test_session.exec(select(Order).where(Order.order_id == "10044")).first()

    assert response.result_code == "refund_requested"
    assert order.refund_status == RefundStatus.requested


def test_chat_tool_route_logs_execution(test_session) -> None:
    response = answer_chat("Track order #9982 for maya@example.com", session=test_session)
    logs = test_session.exec(select(ToolExecutionLog)).all()

    assert response.route == "tool"
    assert response.tool_result.result_code == "order_found"
    assert logs
    assert logs[-1].interaction_log_id is not None

