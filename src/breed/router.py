from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.session import get_db
from database.models import Breed
from src.breed.schemas import BreedOut, BreedOutList, BreedIn
from src.dependencies.authentication import get_token_payload

router = APIRouter(dependencies=[Depends(get_token_payload)])


@router.get(
    "/breed/{breed_id}",
    response_model=BreedOut,
    description="Получения информации о конкретной породе.",
    summary="Получения информации о конкретной породе.",
    responses={
        200: {"description": "Успешный запрос."},
        404: {
            "description": "Нет породы с таким id",
        },
        500: {
            "description": "Ошибка запроса",
        },
    }
)
async def get_breed(
        breed_id: int,
        db_connect: AsyncSession = Depends(get_db),
):
    breed = (await db_connect.execute(select(Breed).filter(Breed.id == breed_id))).scalar()
    if not breed:
        raise HTTPException(status_code=404, detail="Нет породы с таким id")
    return BreedOut(
        id=breed_id,
        name=breed.name,
        description=breed.description
    )


@router.get(
    "/breed/all/",
    response_model=BreedOutList,
    description="Получения информации о всех породах.",
    summary="Получения информации о всех породах.",
    responses={
        200: {"description": "Успешный запрос."},
        500: {
            "description": "Ошибка запроса",
        },
    }
)
async def get_all_breeds(
        db_connect: AsyncSession = Depends(get_db),
):
    breeds = (
        await db_connect.execute(
            select(Breed)
            .order_by(Breed.id)
        )
    ).scalars().all()
    breed_out_list = [BreedOut(id=breed.id, name=breed.name, description=breed.description) for breed in breeds]
    return BreedOutList(breed=breed_out_list)


@router.post(
    "/breed/create",
    response_model=BreedOut,
    description="Добавление новой породы.",
    summary="Добавление новой породы.",
    responses={
        200: {"description": "Порода создана."},
        500: {
            "description": "Ошибка создания",
        },
    }
)
async def create_breed(
        breed_in: BreedIn,
        db_connect: AsyncSession = Depends(get_db),
):
    breed_data = breed_in.dict()
    breed_add = Breed(
        name=breed_data['name'],
        description=breed_data['description'],
    )
    db_connect.add(breed_add)
    await db_connect.flush()
    await db_connect.refresh(breed_add)
    return BreedOut(
        id=breed_add.id,
        name=breed_add.name,
        description=breed_add.description
    )


