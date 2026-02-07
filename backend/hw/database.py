import asyncpg
import os
from typing import Optional

DB_USER = "postgres"
DB_PASSWORD = ' '
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'backend_avito'

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        database_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

        self.pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=10
        )
        print(f"Подключение к БД установлено: {DB_NAME if 'db_name' in locals() else 'из DATABASE_URL'}")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            print("Подключение к БД закрыто")

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

db = Database()