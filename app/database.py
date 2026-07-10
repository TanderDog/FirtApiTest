import asyncpg
 
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
# Сменен потерн : было psycopg2 + курсор + cur.execute
# теперь asyncpg + conn. ((($1 и $2 вместо %s, %d))).
# аналогично освобождаем поток ожиданием await.

 
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
 