from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.order import OrderActionRequest, RefundRequest, ToolCallResult
from app.services.order_actions import cancel_order, request_refund, track_order

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/track", response_model=ToolCallResult)
def track_order_endpoint(request: OrderActionRequest, session: Session = Depends(get_session)) -> ToolCallResult:
    return track_order(session=session, order_id=request.order_id, email=str(request.email))


@router.post("/cancel", response_model=ToolCallResult)
def cancel_order_endpoint(request: OrderActionRequest, session: Session = Depends(get_session)) -> ToolCallResult:
    return cancel_order(session=session, order_id=request.order_id, email=str(request.email))


@router.post("/refund", response_model=ToolCallResult)
def request_refund_endpoint(request: RefundRequest, session: Session = Depends(get_session)) -> ToolCallResult:
    return request_refund(session=session, request=request)

