from datetime import datetime
from typing import List

from pydantic import BaseModel

from src.breed.schemas import BreedOut


class KittyIn:
    class Create(BaseModel):
        name: str
        color: str
        age: int
        description: str | None
        breed_id: int

    class Update(BaseModel):
        name: str | None
        color: str | None
        age: int | None
        description: str | None
        breed_id: int | None


class KittyOut(BaseModel):
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    id: int
    name: str
    color: str
    age: int
    description: str | None
    breed_id: int


class KittyOutWithBreed(BaseModel):
    kitty: KittyOut
    breed: BreedOut


class KittyOutList(BaseModel):
    kittens: List[KittyOut]
