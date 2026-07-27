from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates

from app.database import add_user, get_users_paginated, get_db, init_db, close_db
import app.database as database
from app.schemas import PaginationParams, User, UserResponse
from app.stocks.repository import TicketsRepository
from app.stocks.postgres_repo import PostgresTicketsRepository, init_tickets_tables
from app.stocks.service import get_tickets_page
from app.stocks.api import MoexApiError

TICKERS = ["SBER", "GAZP", "LKOH", "ROSN"]


def get_stocks_repo() -> TicketsRepository:
    return PostgresTicketsRepository(database.connection_pool)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_tickets_tables(database.connection_pool)
    yield
    await close_db()


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root(request: Request, pagination: PaginationParams = Depends(), conn=Depends(get_db)):
    data = await get_users_paginated(conn, pagination.page, pagination.size)
    return templates.TemplateResponse(request, "index.html", data)


@app.post("/user", response_model=UserResponse)
async def create_user(user: User, conn=Depends(get_db)):
    new_id = await add_user(conn, user.name, user.age)
    return UserResponse(message=f"Сохранён {user.name}, id={new_id}")


@app.get("/tikets")
async def tikets_page(
    request: Request,
    extra: str | None = None,
    pagination: PaginationParams = Depends(),
    repo: TicketsRepository = Depends(get_stocks_repo),
):
    tickers = TICKERS.copy()
    if extra:
        extra_upper = extra.upper()
        if extra_upper not in tickers:
            tickers.append(extra_upper)

    try:
        page_data = await get_tickets_page(repo, tickers, pagination.page, pagination.size)
    except MoexApiError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    return templates.TemplateResponse(
        request,
        "tikets.html",
        {**page_data, "extra": extra},
    )
