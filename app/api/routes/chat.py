from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_rag_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message는 비어 있을 수 없습니다.")

    try:
        return rag_service.answer(
            question=request.message,
            session_id=request.session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
