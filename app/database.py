import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

connection_pool = None


def init_db():
    global connection_pool
    connection_pool = pool.ThreadedConnectionPool(
        minconn=1,
        maxconn=10,
        host="localhost",
        database="mydb",
        user="postgres",
        password="1234",
        port=5432,
    )

    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL
                )
            """)
        conn.commit()
    finally:
        connection_pool.putconn(conn)


def close_db():
    if connection_pool:
        connection_pool.closeall()


def get_db():
    conn = connection_pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        connection_pool.putconn(conn)


def add_user(cur, name: str, age: int):
    cur.execute(
        "INSERT INTO users (name, age) VALUES (%s, %s) RETURNING id",
        (name, age),
    )
    return cur.fetchone()["id"]


def get_users(cur):
    cur.execute("SELECT id, name, age FROM users")
    return cur.fetchall()


def get_users_paginated(cur, page: int, size: int):
    offset = (page - 1) * size
 
    cur.execute("SELECT COUNT(*) AS count FROM users")
    total = cur.fetchone()["count"]
 
    cur.execute(
        "SELECT id, name, age FROM users ORDER BY id LIMIT %s OFFSET %s",
        (size, offset),
    )
    users = cur.fetchall()
 
    total_pages = (total + size - 1) // size if total else 1
 
    return {
        "users": users,
        "page": page,
        "size": size,
        "total": total,
        "total_pages": total_pages,
    }
