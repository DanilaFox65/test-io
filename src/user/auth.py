from datetime import timedelta, datetime
from typing import Optional

from jose import jwt
from fastapi import Depends

from core.session import get_settings
from core.settings import AppSettings
from src.user.schemas import UserTokenPayload


def create_access_token(
        user_id: int,
        expires_delta: Optional[timedelta] = None,
        settings: AppSettings = Depends(get_settings)
):
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.access_token_expire))
    payload = ({"exp": expire, **UserTokenPayload(user_id=user_id).dict()})
    return jwt.encode(payload, settings.jwt_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
        user_id: int,
        expires_delta: Optional[timedelta] = None,
        settings: AppSettings = Depends(get_settings)
):
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.refresh_token_expire))
    payload = ({"exp": expire, **UserTokenPayload(user_id=user_id).dict()})
    return jwt.encode(payload, settings.jwt_key, algorithm=settings.jwt_algorithm)

