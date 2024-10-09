# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

import pytest_asyncio

from kg_integration.models import MetadataCRUD
from kg_integration.schemas.metadata import MetadataCreateSchema
from tests.fixtures.base import BaseFactory


class MetadataFactory(BaseFactory):
    """Create spaces related entries for testing purposes."""

    async def create(self, metadata_id: UUID, kg_instance_id: UUID, dataset_id: UUID, direction: str):
        entry = MetadataCreateSchema(
            metadata_id=metadata_id, kg_instance_id=kg_instance_id, dataset_id=dataset_id, direction=direction
        )
        return await self.crud.create(entry)


@pytest_asyncio.fixture()
def metadata_crud(db_session) -> MetadataCRUD:
    yield MetadataCRUD(db_session)


@pytest_asyncio.fixture()
def metadata_factory(metadata_crud) -> MetadataFactory:
    yield MetadataFactory(metadata_crud)
