import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_tourism_chat_service
from app.schemas.tourism import TourismChatRequest, TourismChatResponse
from app.services.tourism_chat_service import TourismChatService

router = APIRouter()
logger = logging.getLogger(__name__)


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
        logger.exception("관광 챗봇 응답 생성 실패")
        raise HTTPException(
            status_code=500,
            detail={
                "code": "TOURISM_CHAT_FAILED",
                "message": "관광 상담 응답을 만드는 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            },
        ) from exc
