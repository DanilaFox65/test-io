from fastapi import APIRouter, HTTPException
from openai import APIConnectionError, AuthenticationError, RateLimitError
from pydantic import BaseModel

from core.openai_client import get_openai_client
from core.settings import get_settings
from src.generation.router import router as generation_router
from src.mistral.router import router as mistral_router

api_router = APIRouter()
api_router.include_router(mistral_router, prefix="/mistral", tags=["mistral"])
api_router.include_router(
    generation_router,
    prefix="/generation",
    tags=["generation"],
)


@api_router.get("/healthz")
async def healthz():
    return {"status": "ok"}


class ChatRequest(BaseModel):
    message: str


@api_router.post("/assistant")
async def assistant(req: ChatRequest):
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=500,
            detail="Добавьте OPENAI_API_KEY в .env",
        )

    client = get_openai_client()

    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=req.message,
        )
    except RateLimitError as exc:
        if "insufficient_quota" in str(exc):
            raise HTTPException(
                status_code=402,
                detail=(
                    "На аккаунте OpenAI закончилась квота или не подключена оплата. "
                    "Проверьте Billing: https://platform.openai.com/settings/organization/billing"
                ),
            ) from exc
        raise HTTPException(
            status_code=429,
            detail="Превышен лимит запросов OpenAI. Повторите позже.",
        ) from exc
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail="Неверный OPENAI_API_KEY в .env",
        ) from exc
    except APIConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail="Не удалось подключиться к OpenAI API",
        ) from exc

    return {"answer": response.output_text}
