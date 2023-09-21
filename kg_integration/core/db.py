# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from kg_integration.config import Settings
from kg_integration.config import get_settings

logger = logging.getLogger(__name__)


class DBEngine:
    """Create a FastAPI callable dependency for SQLAlchemy single AsyncEngine instance."""

    def __init__(self, settings: Settings) -> None:
        self.instance = None
        self.db_uri = settings.RDS_DB_URI

    def __call__(self) -> AsyncEngine:
        """Return an instance of AsyncEngine class."""

        if not self.instance:
            try:
                self.instance = create_async_engine(self.db_uri)
            except SQLAlchemyError:
                logger.exception('Error DB connect')
        return self.instance


async def get_db_engine(settings: Settings = Depends(get_settings)) -> AsyncEngine:
    engine = DBEngine(settings)
    yield engine()


async def get_db_session(engine: AsyncEngine = Depends(get_db_engine)) -> AsyncSession:
    db = AsyncSession(bind=engine, expire_on_commit=False)
    try:
        yield db
        await db.commit()
    finally:
        await db.close()


async def is_db_connected(db: AsyncSession = Depends(get_db_session)) -> bool:
    """Validates DB connection."""

    try:
        connection = await db.connection()
        raw_connection = await connection.get_raw_connection()
        if not raw_connection.is_valid:
            return False
    except SQLAlchemyError:
        logger.exception('DB connection failed, SQLAlchemyError')
        return False
    except Exception:
        logger.exception('DB connection failed, unknown Exception')
        return False
    return True
