import os
import asyncpg
from typing import AsyncGenerator

# Use standard postgres URI format
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/neti")

# Global pool instance
_pool: asyncpg.Pool | None = None

async def init_db_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=10)

async def close_db_pool():
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """FastAPI dependency for injecting DB connections."""
    global _pool
    if _pool is None:
        await init_db_pool()
    
    # We use type ignore or assert because it is initialized above
    assert _pool is not None
    async with _pool.acquire() as connection:
        yield connection
