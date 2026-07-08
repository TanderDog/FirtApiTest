from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.database import add_user, get_users_paginated, get_db, init_db, close_db
from app.schemas import PaginationParams


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    close_db()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


class User(BaseModel):
    name: str
    age: int


class UserResponse(BaseModel):
    message: str


@app.get("/")
def root(request: Request, pagination: PaginationParams = Depends(),cur=Depends(get_db)):
    data = get_users_paginated(cur, pagination.page, pagination.size)
    return templates.TemplateResponse(request, "index.html", data)


@app.post("/user", response_model=UserResponse)
def create_user(user: User, cur=Depends(get_db)):
    new_id = add_user(cur, user.name, user.age)
    return UserResponse(message=f"Сохранён {user.name}, id={new_id}")
