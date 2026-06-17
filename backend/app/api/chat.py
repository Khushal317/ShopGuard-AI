from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_chat import answer_chat

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, session: Session = Depends(get_session)) -> ChatResponse:
    try:
        return answer_chat(message=request.message, top_k=request.top_k, session=session)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="The database is unavailable. Check DATABASE_URL and database credentials.",
        ) from exc
