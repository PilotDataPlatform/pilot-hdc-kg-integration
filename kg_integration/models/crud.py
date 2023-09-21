# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging
from typing import Any

from sqlalchemy import CursorResult
from sqlalchemy import Executable
from sqlalchemy import Result
from sqlalchemy import ScalarResult
from sqlalchemy import Select
from sqlalchemy import delete
from sqlalchemy import insert
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from kg_integration.core.exceptions import NotFound
from kg_integration.models import DBModel
from kg_integration.schemas.base import BaseSchema

logger = logging.getLogger(__name__)


class CRUD:
    """Base CRUD class for managing database models."""

    session: AsyncSession
    model: type[DBModel]

    def __init__(self, db_session: AsyncSession) -> None:
        self.session = db_session
        self.transaction = None

    async def __aenter__(self) -> 'CRUD':
        """Start a new transaction."""

        self.transaction = self.session.begin_nested()
        await self.transaction.__aenter__()

        return self

    async def __aexit__(self, *args: Any) -> None:
        """Commit an existing transaction."""

        await self.transaction.__aexit__(*args)

        return None

    @property
    def select_query(self) -> Select:
        """Create base select."""
        return select(self.model)

    async def execute(self, statement: Executable, **kwds: Any) -> CursorResult | Result:
        """Execute a statement and return buffered result."""
        return await self.session.execute(statement, **kwds)

    async def scalars(self, statement: Executable, **kwds: Any) -> ScalarResult:
        """Execute a statement and return scalar result."""

        return await self.session.scalars(statement, **kwds)

    async def _create_one(self, statement: Executable) -> DBModel:
        """Execute a statement to create one entry and returns its PK."""
        result = await self.execute(statement)
        return result.inserted_primary_key[0]

    async def _retrieve_one(self, statement: Executable) -> DBModel:
        """Execute a statement to retrieve one entry."""

        result = await self.scalars(statement)
        instance = result.first()

        if instance is None:
            raise NotFound()

        return instance

    async def _delete_one(self, statement: Executable) -> None:
        """Execute a statement to delete one entry."""

        result = await self.execute(statement)

        if result.rowcount == 0:
            raise NotFound()

    async def retrieve_by_pk(self, pk: Any) -> DBModel:
        """Get an existing entry by primary key."""

        statement = self.select_query.where(self.model.id == pk)
        entry = await self._retrieve_one(statement)

        return entry

    async def create(self, entry_create: BaseSchema, **kwds: Any) -> DBModel:
        """Create a new entry."""
        values = entry_create.dict()
        statement = insert(self.model).values(**(values | kwds))
        try:
            entry_pk = await self._create_one(statement)
        except IntegrityError:
            raise IntegrityError

        entry = await self.retrieve_by_pk(entry_pk)

        return entry

    async def delete(self, pk: Any) -> None:
        """Remove an existing entry."""

        statement = delete(self.model).where(self.model.id == pk)

        await self._delete_one(statement)
