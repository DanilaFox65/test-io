from openai import OpenAI

from core.settings import get_settings


def get_openai_client() -> OpenAI:
    return OpenAI(api_key=get_settings().openai_api_key)
