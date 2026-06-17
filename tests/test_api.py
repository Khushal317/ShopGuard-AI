from fastapi.testclient import TestClient

from app.api.chat import chat
from app.api.orders import cancel_order_endpoint, request_refund_endpoint, track_order_endpoint
from app.db.session import get_session
from app.main import app
from app.schemas.chat import ChatRequest
from app.schemas.order import OrderActionRequest, RefundRequest


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint_with_session_override(test_session) -> None:
    response = chat(
        ChatRequest(message="Does the leather jacket come in brown and what is the return policy?"),
        session=test_session,
    )

    assert response.route == "rag"
    assert response.citations
    assert response.retrieved_context
    assert response.evaluation is not None


def test_order_endpoints_with_session_override(test_session) -> None:
    track_response = track_order_endpoint(
        OrderActionRequest(order_id="9982", email="maya@example.com"),
        session=test_session,
    )
    cancel_response = cancel_order_endpoint(
        OrderActionRequest(order_id="10031", email="liam@example.com"),
        session=test_session,
    )
    refund_response = request_refund_endpoint(
        RefundRequest(order_id="10044", email="sofia@example.com", reason="Changed mind"),
        session=test_session,
    )

    assert track_response.result_code == "order_found"
    assert cancel_response.result_code == "cancellation_not_allowed"
    assert refund_response.result_code == "refund_requested"


def test_app_routes_are_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/api/chat" in paths
    assert "/api/orders/track" in paths
    assert "/api/orders/cancel" in paths
    assert "/api/orders/refund" in paths
    assert get_session is not None

