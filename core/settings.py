from functools import lru_cache

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    mistral_api_key: str | None = None
    mistral_model: str = "mistral-small-latest"
    root_path: str = ""

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> AppSettings:
    return AppSettings()
