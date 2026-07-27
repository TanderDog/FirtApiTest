from datetime import date

import asyncpg

from app.stocks.repository import TicketsRepository


async def init_tickets_tables(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mos_tikets_raw (
                id SERIAL PRIMARY KEY,
                secid VARCHAR(10) NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                fetched_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_raw_secid_fetched
            ON mos_tikets_raw (secid, fetched_at DESC)
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS mos_tikets_daily (
                id SERIAL PRIMARY KEY,
                secid VARCHAR(10) NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                tiket_date DATE NOT NULL DEFAULT CURRENT_DATE,
                UNIQUE (secid, tiket_date)
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_secid_date
            ON mos_tikets_daily (secid, tiket_date DESC)
        """)


class PostgresTicketsRepository(TicketsRepository):

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def add_raw(self, secid: str, price: float) -> dict:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO mos_tikets_raw (secid, price) VALUES ($1, $2) RETURNING id, fetched_at",
                secid, price,
            )
            return dict(row)

    async def add_daily(self, secid: str, price: float, target_date: date | None = None) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO mos_tikets_daily (secid, price, tiket_date)
                VALUES ($1, $2, COALESCE($3, CURRENT_DATE))
                ON CONFLICT (secid, tiket_date) DO UPDATE SET price = EXCLUDED.price
                """,
                secid, price, target_date,
            )

    async def get_raw(self, secid: str, target_date: date | None = None, limit: int = 1) -> list[dict]:
        async with self.pool.acquire() as conn:
            if target_date:
                rows = await conn.fetch(
                    "SELECT * FROM mos_tikets_raw WHERE secid=$1 AND fetched_at::date=$2 ORDER BY fetched_at DESC LIMIT $3",
                    secid, target_date, limit,
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM mos_tikets_raw WHERE secid=$1 ORDER BY fetched_at DESC LIMIT $2",
                    secid, limit,
                )
            return [dict(r) for r in rows]

    async def get_daily(self, secid: str, target_date: date) -> float | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT price FROM mos_tikets_daily WHERE secid=$1 AND tiket_date=$2",
                secid, target_date,
            )
            return float(row["price"]) if row else None

    async def get_daily_paginated(self, page: int, size: int) -> dict:
        offset = (page - 1) * size
        today = date.today()

        async with self.pool.acquire() as conn:
            total = await conn.fetchval(
                "SELECT COUNT(*) FROM mos_tikets_daily WHERE tiket_date=$1",
                today,
            )

            rows = await conn.fetch(
                """
                SELECT secid, price
                FROM mos_tikets_daily
                WHERE tiket_date=$1
                ORDER BY secid
                LIMIT $2 OFFSET $3
                """,
                today, size, offset,
            )

        records = [{"secid": r["secid"], "price": float(r["price"])} for r in rows]
        total_pages = (total + size - 1) // size if total else 1

        return {
            "records": records,
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
        }

    async def get_price_avg(self, secid: str, days: int = 7) -> float | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT AVG(price) AS avg_price
                FROM mos_tikets_daily
                WHERE secid = $1
                  AND tiket_date < CURRENT_DATE
                  AND tiket_date >= CURRENT_DATE - $2::int
                """,
                secid, days,
            )
            return float(row["avg_price"]) if row and row["avg_price"] is not None else None

    async def get_price_volatility(self, secid: str, days: int = 7) -> float | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT STDDEV(price) AS volatility
                FROM mos_tikets_daily
                WHERE secid = $1
                  AND tiket_date < CURRENT_DATE
                  AND tiket_date >= CURRENT_DATE - $2::int
                """,
                secid, days,
            )
            return float(row["volatility"]) if row and row["volatility"] is not None else None
