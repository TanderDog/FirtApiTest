from datetime import date, timedelta

from app.stocks.repository import TicketsRepository
from app.stocks.api import fetch_prices
from app.calculations import math_prices


async def sync_ticker(repo: TicketsRepository, secid: str, today_price: float, prev_price: float | None):
    await repo.add_raw(secid, today_price)
    await repo.add_daily(secid, today_price)

    yesterday = date.today() - timedelta(days=1)
    yesterday_price = await repo.get_daily(secid, yesterday)

    if yesterday_price is None and prev_price is not None:
        await repo.add_daily(secid, prev_price, yesterday)


async def get_tickets_page(repo: TicketsRepository, tickers: list[str], page: int, size: int):
    prices = await fetch_prices(tickers)

    for secid, (today_price, prev_price) in prices.items():
        await sync_ticker(repo, secid, today_price, prev_price)

    page_data = await repo.get_daily_paginated(page, size)

    cards = []
    for r in page_data["records"]:
        avg_price = await repo.get_price_avg(r["secid"])
        volatility = await repo.get_price_volatility(r["secid"])

        vs_week = math_prices(r["price"], avg_price)

        cards.append({
            "secid": r["secid"],
            "price": r["price"],
            "vs_week": vs_week,
            "volatility": round(volatility, 2) if volatility is not None else None,
        })

    return {
        "cards": cards,
        "page": page_data["page"],
        "size": page_data["size"],
        "total": page_data["total"],
        "total_pages": page_data["total_pages"],
    }
