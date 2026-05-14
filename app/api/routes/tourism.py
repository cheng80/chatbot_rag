from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_tourism_chat_service
from app.schemas.tourism import TourismChatRequest, TourismChatResponse
from app.services.tourism_chat_service import TourismChatService

router = APIRouter()


@router.post("/chat", response_model=TourismChatResponse)
def tourism_chat(
    request: TourismChatRequest,
    tourism_chat_service: TourismChatService = Depends(get_tourism_chat_service),
) -> TourismChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="message는 비어 있을 수 없습니다.")

    try:
        return tourism_chat_service.answer(
            message=request.message,
            session_id=request.session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
