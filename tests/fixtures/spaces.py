# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from datetime import datetime

import pytest_asyncio

from kg_integration.models import SpacesCRUD
from kg_integration.schemas.space import SpaceSchema
from tests.fixtures.base import BaseFactory


class SpacesFactory(BaseFactory):
    """Create spaces related entries for testing purposes."""

    async def create(self, name: str, creator: str, created_at: datetime | None = None):
        if created_at is None:
            created_at = datetime.now()
        entry = SpaceSchema(name=name, creator=creator, created_at=created_at)
        return await self.crud.create(entry)


@pytest_asyncio.fixture()
def spaces_crud(db_session) -> SpacesCRUD:
    yield SpacesCRUD(db_session)


@pytest_asyncio.fixture()
def spaces_factory(spaces_crud) -> SpacesFactory:
    yield SpacesFactory(spaces_crud)
