from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.session import get_db, get_settings
from core.settings import AppSettings
from database.models import User
from src.user.schemas import UserTokenPayload

security = HTTPBearer()


async def get_token_payload(
        authorization: HTTPAuthorizationCredentials = Depends(security),
        settings: AppSettings = Depends(get_settings)
):
    token = authorization.credentials
    try:
        payload = jwt.decode(token, settings.jwt_key, algorithms=settings.jwt_algorithm)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Не валидный токен")
    except JWTError:
        raise HTTPException(status_code=401, detail="Срок жизни токена истек")

    return UserTokenPayload(**payload)


async def get_current_user(token_payload: UserTokenPayload = Depends(get_token_payload),
                           db_connect: AsyncSession = Depends(get_db)) -> User:
    user: User = (await db_connect.execute(
        select(User).filter(User.id == token_payload.user_id))).scalars().unique().one()
    if not user:
        raise HTTPException(status_code=404, detail="Не найдено пользователь по данным из токена")
    return user
