"""Database-level append-only enforcement tests.

These tests verify that PostgreSQL itself rejects UPDATE and DELETE
operations on NETI's append-only audit tables.
"""

import os

import asyncpg
import pytest
import pytest_asyncio


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/neti",
)


@pytest_asyncio.fixture
async def db():
    connection = await asyncpg.connect(DATABASE_URL)

    try:
        yield connection
    finally:
        await connection.close()


@pytest.mark.asyncio
async def test_ceremony_events_rejects_update(db):
    await db.execute(
        """
        INSERT INTO ceremony_events (ceremony_id, event_type, payload)
        VALUES ('PYTEST-UPDATE', 'test', '{"test": true}')
        """
    )

    with pytest.raises(
        asyncpg.exceptions.RaiseError,
        match="append-only",
    ):
        await db.execute(
            """
            UPDATE ceremony_events
            SET event_type = 'changed'
            WHERE ceremony_id = 'PYTEST-UPDATE'
            """
        )


@pytest.mark.asyncio
async def test_ceremony_events_rejects_delete(db):
    await db.execute(
        """
        INSERT INTO ceremony_events (ceremony_id, event_type, payload)
        VALUES ('PYTEST-DELETE', 'test', '{"test": true}')
        """
    )

    with pytest.raises(
        asyncpg.exceptions.RaiseError,
        match="append-only",
    ):
        await db.execute(
            """
            DELETE FROM ceremony_events
            WHERE ceremony_id = 'PYTEST-DELETE'
            """
        )