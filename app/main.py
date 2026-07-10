from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.database import add_user, get_users_paginated, get_db, init_db, close_db
from app.schemas import PaginationParams, User, UserResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Добавлен await, переход в event loop на время ожидания 
    await init_db()
    yield
    await close_db()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root(request: Request, pagination: PaginationParams = Depends(), conn=Depends(get_db)):
    # Раньше "def root" блокировал поток ожиданием полного завершения
    # запроса к БД, что снижает производительность при большом
    # количестве пользователей.
    # Теперь мы отдаём управление event loop и можем обрабатывать
    # другие запросы, пока не завершится выполнение текущего.
    data = await get_users_paginated(conn, pagination.page, pagination.size)
    return templates.TemplateResponse(request, "index.html", data)


@app.post("/user", response_model=UserResponse)
async def create_user(user: User, conn=Depends(get_db)):
    # Та же логика что и в root: await передаёт управление event loop
    # на время ожидания ответа от БД, поток не простаивает.
    new_id = await add_user(conn, user.name, user.age)
    return UserResponse(message=f"Сохранён {user.name}, id={new_id}")