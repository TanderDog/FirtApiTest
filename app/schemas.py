from datetime import date

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=3, ge=1)


class User(BaseModel):
    name: str
    age: int


class UserResponse(BaseModel):
    message: str
