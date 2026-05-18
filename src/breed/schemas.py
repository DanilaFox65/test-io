from typing import List

from pydantic import BaseModel


class BreedIn(BaseModel):
    name: str
    description: str | None


class BreedOut(BaseModel):
    id: int
    name: str
    description: str | None


class BreedOutList(BaseModel):
    breed: List[BreedOut]
