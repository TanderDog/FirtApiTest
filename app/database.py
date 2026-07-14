import asyncpg
from datetime import date
 
connection_pool = None
 
 
async def init_db():
    global connection_pool
    # Было: pool.ThreadedConnectionPool
    # синхронный пул psycopg2, соединение брали через getconn()/putconn()
    # Сейчас asyncpg соединяемся acquire(),
    # а async with - возвращает автоматом.
    connection_pool = await asyncpg.create_pool(
        host="localhost",
        database="mydb",
        user="postgres",
        password="1234",
        port=5432,
        min_size=1,
        max_size=10,
    )
 
    async with connection_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL
            )
        """)
    # Таблицы акций.        
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
 
# пользователи 
async def close_db():
    if connection_pool:
        await connection_pool.close()
 
 
async def get_db():
    async with connection_pool.acquire() as conn:
        yield conn
 
 
async def add_user(conn, name: str, age: int):
    row = await conn.fetchrow(
        "INSERT INTO users (name, age) VALUES ($1, $2) RETURNING id",
        name, age,
    )
    return row["id"]
 
 
async def get_users(conn):
    rows = await conn.fetch("SELECT id, name, age FROM users")
    return [dict(r) for r in rows]
 
 
async def get_users_paginated(conn, page: int, size: int):
    offset = (page - 1) * size
 
    total = await conn.fetchval("SELECT COUNT(*) FROM users")
 
    rows = await conn.fetch(
        "SELECT id, name, age FROM users ORDER BY id LIMIT $1 OFFSET $2",
        size, offset,
    )
    users = [dict(r) for r in rows]
 
    total_pages = (total + size - 1) // size if total else 1
 
    return {
        "users": users,
        "page": page,
        "size": size,
        "total": total,
        "total_pages": total_pages,
    }
 
 # акции 
async def add_raw(conn, secid: str, price: float):
    row = await conn.fetchrow(
        "INSERT INTO mos_tikets_raw (secid, price) VALUES ($1, $2) RETURNING id, fetched_at",
        secid, price,
    )
    return dict(row)

async def add_daily(conn, secid: str, price: float, target_date: date | None = None):
    await conn.execute(
        """
        INSERT INTO mos_tikets_daily (secid, price, tiket_date)
        VALUES ($1, $2, COALESCE($3, CURRENT_DATE))
        ON CONFLICT (secid, tiket_date) DO UPDATE SET price = EXCLUDED.price
        """,
        secid, price, target_date,
    )

    
async def get_raw(conn, secid: str, date: date | None = None, limit: int = 1):
    if date:
        rows = await conn.fetch(
            "SELECT * FROM mos_tikets_raw WHERE secid=$1 AND fetched_at::date=$2 ORDER BY fetched_at DESC LIMIT $3",
            secid, date, limit,
        )
    else:
        rows = await conn.fetch(
            "SELECT * FROM mos_tikets_raw WHERE secid=$1 ORDER BY fetched_at DESC LIMIT $2",
            secid, limit,
        )
    return [dict(r) for r in rows]    

async def get_daily(conn, secid: str, target_date: date):
    row = await conn.fetchrow(
        "SELECT price FROM mos_tikets_daily WHERE secid=$1 AND tiket_date=$2",
        secid, target_date,
    )
    return float(row["price"]) if row else None

async def get_daily_paginated(conn, page: int, size: int):
    offset = (page - 1) * size
    today = date.today()

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

async def get_price_avg(conn, secid: str, days: int = 7):
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

async def get_price_volatility(conn, secid: str, days: int = 7):
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
