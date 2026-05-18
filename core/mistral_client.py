from mistralai import Mistral

from core.settings import get_settings


def get_mistral_client() -> Mistral:
    settings = get_settings()
    if not settings.mistral_api_key:
        raise ValueError("MISTRAL_API_KEY не задан в .env")
    return Mistral(api_key=settings.mistral_api_key)
