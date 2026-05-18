from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.mistral_client import get_mistral_client
from core.settings import get_settings

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/assistant")
async def assistant(req: ChatRequest):
    settings = get_settings()
    if not settings.mistral_api_key:
        raise HTTPException(
            status_code=500,
            detail="Добавьте MISTRAL_API_KEY в .env",
        )

    try:
        client = get_mistral_client()
        response = client.chat.complete(
            model=settings.mistral_model,
            messages=[
                {
                    "role": "user",
                    "content": req.message,
                }
            ],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка Mistral API: {exc}",
        ) from exc

    return {
        "answer": response.choices[0].message.content,
    }
