from fastapi import APIRouter, Depends, Header, HTTPException

from core.settings import AppSettings, get_settings
from src.generation.schemas import GenerateQuestionsRequest, GenerateQuestionsResponse
from src.generation.service import GenerationError, generate_questions

router = APIRouter()


def verify_internal_token(
    x_internal_token: str | None = Header(default=None),
    settings: AppSettings = Depends(get_settings),
) -> None:
    if not settings.internal_api_token:
        return
    if x_internal_token != settings.internal_api_token:
        raise HTTPException(status_code=401, detail="Неверный X-Internal-Token")


@router.post(
    "/questions/generate",
    response_model=GenerateQuestionsResponse,
    summary="Сгенерировать вопросы для квиза/квеста",
)
async def generate_questions_endpoint(
    body: GenerateQuestionsRequest,
    _: None = Depends(verify_internal_token),
) -> GenerateQuestionsResponse:
    settings = get_settings()
    if not settings.mistral_api_key:
        raise HTTPException(
            status_code=500,
            detail="Добавьте MISTRAL_API_KEY в .env",
        )

    try:
        return generate_questions(body)
    except GenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
