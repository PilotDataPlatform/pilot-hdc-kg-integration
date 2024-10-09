# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import Sequence
from typing import Any

from fastapi import Depends
from sqlalchemy import Row
from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kg_integration.core.db import get_db_session
from kg_integration.core.exceptions import NotFound
from kg_integration.core.exceptions import SpaceAlreadyExists
from kg_integration.logger import logger
from kg_integration.models.crud import CRUD
from kg_integration.models.spaces.spaces import Spaces
from kg_integration.schemas.space import SpaceCreateSchema


class SpacesCRUD(CRUD):

    model = Spaces

    async def retrieve_by_pk(self, pk: Any) -> Spaces:
        """Get an existing entry by primary key."""

        statement = self.select_query.where(self.model.name == pk)
        entry = await self._retrieve_one(statement)

        return entry

    async def retrieve_by_name(self, name: str) -> Spaces:
        return await self.retrieve_by_pk(name)

    async def retrieve_by_names(self, name_list: list[str]) -> Sequence[Row]:
        statement = self.select_query.where(self.model.name.in_(name_list))

        results = await self.scalars(statement)

        return results.all()

    async def retrieve_only_existing_names(self, name_list: list[str]) -> Sequence[str]:
        statement = select(self.model.name).where(self.model.name.in_(name_list))

        results = await self.scalars(statement)

        return results.all()

    async def create_space(self, name: str, username: str) -> Spaces:
        """Checking if the space entry was already created and create a new one if not."""
        try:
            await self.retrieve_by_name(name)
            logger.error(f'Space {name} was already created')
            raise SpaceAlreadyExists()
        except NotFound:
            schema = SpaceCreateSchema(name=name, creator=username)
            space = await super().create(entry_create=schema)
            return space

    async def delete(self, pk: Any) -> None:
        """Remove an existing entry."""

        statement = delete(self.model).where(self.model.name == pk)

        await self._delete_one(statement)


def get_spaces_crud(db_session: AsyncSession = Depends(get_db_session)) -> SpacesCRUD:
    """Return an instance of SpacesCRUD as a dependency."""

    return SpacesCRUD(db_session)
