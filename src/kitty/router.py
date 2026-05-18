from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.session import get_db
from database.models import Kitty
from src.breed.schemas import BreedOut
from src.dependencies.authentication import get_token_payload
from src.kitty.schemas import KittyOut, KittyIn, KittyOutWithBreed, KittyOutList

router = APIRouter(dependencies=[Depends(get_token_payload)])


@router.post(
    "/kitty/create/",
    response_model=KittyOut,
    description="Добавление нового котенка.",
    summary="Добавление нового котенка.",
    responses={
        200: {"description": "Котенок создана."},
        500: {
            "description": "Ошибка создания",
        },
    }
)
async def create_ketty(
        kitty_in: KittyIn.Create,
        db_connect: AsyncSession = Depends(get_db),
):
    kitty_data = kitty_in.dict()
    kitty_add = Kitty(
        name=kitty_data['name'],
        color=kitty_data['color'],
        age=kitty_data['age'],
        description=kitty_data['description'],
        breed_id=kitty_data['breed_id'],
    )
    db_connect.add(kitty_add)
    await db_connect.flush()
    await db_connect.refresh(kitty_add)
    return KittyOut(
        created_at=kitty_add.created_at,
        updated_at=kitty_add.updated_at,
        deleted_at=kitty_add.deleted_at,
        id=kitty_add.id,
        name=kitty_add.name,
        color=kitty_add.color,
        age=kitty_add.age,
        description=kitty_add.description,
        breed_id=kitty_add.breed_id,
    )


@router.get(
    "/kitty/{kitty_id}",
    response_model=KittyOutWithBreed,
    description="Получения информации о конкретной котенке.",
    summary="Получения информации о конкретной котенке.",
    responses={
        200: {"description": "Успешный запрос."},
        404: {
            "description": "Нет котенка с таким id",
        },
        500: {
            "description": "Ошибка запроса",
        },
    }
)
async def get_kitty(
        kitty_id: int,
        db_connect: AsyncSession = Depends(get_db),
):
    kitty = (
        await db_connect.execute(
            select(Kitty)
            .filter(
                and_(Kitty.id == kitty_id, Kitty.deleted_at == None)
            )
            .options(
                selectinload(Kitty.breed)
            )
        )
    ).scalar()
    if not kitty:
        raise HTTPException(status_code=404, detail="Нет котенка с таким id")
    return KittyOutWithBreed(
        kitty=KittyOut(
            created_at=kitty.created_at,
            updated_at=kitty.updated_at,
            deleted_at=kitty.deleted_at,
            id=kitty.id,
            name=kitty.name,
            color=kitty.color,
            age=kitty.age,
            description=kitty.description,
            breed_id=kitty.breed_id,
        ),
        breed=BreedOut(
            id=kitty.breed.id,
            name=kitty.breed.name,
            description=kitty.breed.description,
        )
    )


@router.get(
    "/kitty/all/",
    response_model=KittyOutList,
    description="Получения информации о всех котятах.",
    summary="Получения информации о всех котятах.",
    responses={
        200: {"description": "Успешный запрос."},
        500: {
            "description": "Ошибка запроса",
        },
    }
)
async def get_all_kitty(
        breed_id: Optional[int] = None,
        db_connect: AsyncSession = Depends(get_db),
):
    query = select(Kitty).filter(Kitty.deleted_at == None)

    if breed_id is not None:
        query = query.filter(Kitty.breed_id == breed_id)

    result = await db_connect.execute(query)
    kittens = result.scalars().all()

    kittens_out_list = [
        KittyOut(
            created_at=kitty.created_at,
            updated_at=kitty.updated_at,
            deleted_at=kitty.deleted_at,
            id=kitty.id,
            name=kitty.name,
            color=kitty.color,
            age=kitty.age,
            description=kitty.description,
            breed_id=kitty.breed_id
        ) for kitty in kittens
    ]

    return KittyOutList(kittens=kittens_out_list)


@router.put(
    "/kitty/update/{kitty_id}",
    response_model=KittyOut,
    description="Изменение информации о котенке.",
    summary="Изменение информации о котенке.",
    responses={
        200: {"description": "Информация изменена."},
        500: {
            "description": "Ошибка редактирования",
        },
        404: {
            "description": "Не найден котенок",
        },
    }
)
async def update_kitty(
        kitty_id: int,
        kitty_in: KittyIn.Update,
        db_connect: AsyncSession = Depends(get_db),
):
    query = select(Kitty).filter(
        and_(Kitty.id == kitty_id, Kitty.deleted_at == None)
    )
    kitty: Kitty = (await db_connect.execute(query)).scalar()

    if not kitty:
        raise HTTPException(status_code=404, detail="Не найден котенок")

    update_data = kitty_in.dict(exclude_unset=True)

    for key, value in update_data.items():
        if value is not None:
            setattr(kitty, key, value)

    kitty.updated_at = datetime.now()

    return KittyOut(
        created_at=kitty.created_at,
        updated_at=kitty.updated_at,
        deleted_at=kitty.deleted_at,
        id=kitty.id,
        name=kitty.name,
        color=kitty.color,
        age=kitty.age,
        description=kitty.description,
        breed_id=kitty.breed_id,
    )


@router.delete(
    "/kitty/soft_removal/{kitty_id}",
    description="Мягкое удаление котенка.",
    summary="Мягкое удаление котенка.",
    responses={
        200: {"description": "Успешное удаление."},
        500: {
            "description": "Ошибка удаленияю",
        },
        404: {
            "description": "Не найден котенок.",
        },
        409: {
            "description": "Котенок уже удален.",
        },
    }
)
async def soft_removal(
        kitty_id: int,
        db_connect: AsyncSession = Depends(get_db),
):
    kitty_data: Kitty = (await db_connect.execute(select(Kitty).filter(Kitty.id == kitty_id))).scalar()

    if not kitty_data:
        raise HTTPException(status_code=404, detail="Не найден котенок.")
    if kitty_data.deleted_at:
        raise HTTPException(status_code=409, detail="Котенок уже удален.")
    kitty_data.deleted_at = datetime.now()
    return f"Котенок {kitty_data.id} - {kitty_data.name} удален"
