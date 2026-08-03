import asyncio
from pathlib import Path

import asyncpg

from app.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


async def run_migrations():
    conn = await asyncpg.connect(
        host=settings.db_host,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        port=settings.db_port,
    )

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    applied = {r["filename"] for r in await conn.fetch("SELECT filename FROM schema_migrations")}

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    for file in files:
        if file.name in applied:
            continue

        sql = file.read_text(encoding="utf-8")
        await conn.execute(sql)
        await conn.execute(
            "INSERT INTO schema_migrations (filename) VALUES ($1)",
            file.name,
        )
        print(f"Применена миграция: {file.name}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())