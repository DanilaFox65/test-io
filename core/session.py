from functools import lru_cache
from typing import AsyncGenerator

from databases import Database
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.settings import AppSettings


@lru_cache()
def get_settings():
    return AppSettings()


if get_settings().debug:
    import logging

    logging.basicConfig()
    logging.getLogger('databases').setLevel(logging.DEBUG)

database = Database(get_settings().database_url, ssl=False, min_size=5, max_size=20)

engine = create_async_engine(
    get_settings().async_database_url(),
    future=True,
    echo=True,
)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# Dependency
async def get_db() -> AsyncGenerator:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as sql_ex:
            await session.rollback()
            raise sql_ex
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
