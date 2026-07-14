from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import Depends, FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.database import (
    add_user, get_users_paginated, get_db, init_db, close_db,
    add_raw, add_daily, get_price_avg, get_daily, get_daily_paginated, 
    get_price_volatility,
)
from app.schemas import PaginationParams, User, UserResponse
from app.moex_api import fetch_prices, fetch_one
from app.calculations import math_prices

TICKERS = ["SBER", "GAZP", "LKOH", "ROSN"]


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
    conn=Depends(get_db),
):
    tickers = TICKERS.copy()
    if extra:
        extra_upper = extra.upper()
        if extra_upper not in tickers:
            tickers.append(extra_upper)

    prices = await fetch_prices(tickers)

    for secid, (today_price, prev_price) in prices.items():
        await add_raw(conn, secid, today_price)
        await add_daily(conn, secid, today_price)

        yesterday = date.today() - timedelta(days=1)
        yesterday_price = await get_daily(conn, secid, yesterday)
        if yesterday_price is None and prev_price is not None:
            await add_daily(conn, secid, prev_price, yesterday)

    page_data = await get_daily_paginated(conn, pagination.page, pagination.size)

    cards = []
    for r in page_data["records"]:
        avg_price = await get_price_avg(conn, r["secid"])
        volatility = await get_price_volatility(conn, r["secid"])

        vs_week = math_prices(r["price"], avg_price)

        cards.append({
            "secid": r["secid"],
            "price": r["price"],
            "vs_week": vs_week,
             "volatility": round(volatility, 2) if volatility is not None else None,
        })

    return templates.TemplateResponse(
        request,
        "tikets.html",
        {
            "cards": cards,
            "page": page_data["page"],
            "size": page_data["size"],
            "total": page_data["total"],
            "total_pages": page_data["total_pages"],
            "extra": extra,
        },
    )


async def sync_and_compare(conn, secid: str, today_price: float, prev_price: float | None):
    await add_raw(conn, secid, today_price)
    await add_daily(conn, secid, today_price)

    yesterday = date.today() - timedelta(days=1)
    yesterday_price = await get_daily(conn, secid, yesterday)

    if yesterday_price is None and prev_price is not None:
        await add_daily(conn, secid, prev_price, yesterday)
        yesterday_price = prev_price

    return math_prices(today_price, yesterday_price)
