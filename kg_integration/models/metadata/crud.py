# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Row
from sqlalchemy import Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from kg_integration.core.db import get_db_session
from kg_integration.models.crud import CRUD

from .metadata import Metadata


class MetadataCRUD(CRUD):

    model = Metadata

    async def retrieve_by_metadata_id(self, metadata_id: UUID) -> Metadata:
        statement = self.select_query.where(self.model.metadata_id == metadata_id)

        entry = await self._retrieve_one(statement)

        return entry

    async def retrieve_by_metadata_ids(self, metadata_ids: list[UUID]) -> Sequence[Row]:
        statement = self.select_query.where(self.model.metadata_id.in_(metadata_ids))

        results = await self.scalars(statement)

        return results.all()


def get_metadata_crud(db_session: AsyncSession = Depends(get_db_session)) -> MetadataCRUD:
    """Return an instance of SpacesCRUD as a dependency."""

    return MetadataCRUD(db_session)
