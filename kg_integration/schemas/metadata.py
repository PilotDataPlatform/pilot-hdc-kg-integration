# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
from datetime import datetime
from typing import Any
from uuid import UUID

from kg_integration.schemas.base import BaseSchema


class MetadataKGResponseSchema(BaseSchema):
    id: UUID
    creator: UUID
    type: list[str]
    space: str
    revision: str
    data: dict

    @classmethod
    def from_kg_response(cls, data: dict[str, Any]) -> 'MetadataKGResponseSchema':
        data.pop('http://schema.org/identifier')
        return cls(
            id=data.pop('@id').removeprefix('https://kg.ebrains.eu/api/instances/'),
            creator=data.pop('https://core.kg.ebrains.eu/vocab/meta/user')['@id'].removeprefix(
                'https://kg.ebrains.eu/api/instances/'
            ),
            type=data.pop('@type'),
            space=data.pop('https://core.kg.ebrains.eu/vocab/meta/space'),
            revision=data.pop('https://core.kg.ebrains.eu/vocab/meta/revision'),
            data=data,
        )


class MetadataKGResponseListSchema(BaseSchema):
    result: list

    @classmethod
    def from_kg_response(cls, data: list[dict[str, Any]]) -> 'MetadataKGResponseListSchema':
        all_metadata = []
        for metadata in data:
            all_metadata.append(MetadataKGResponseSchema.from_kg_response(metadata))
        return cls(result=all_metadata)


class MetadataQuerySchema(BaseSchema):
    id: UUID


class MetadataQueryListSchema(BaseSchema):
    metadata: list[MetadataQuerySchema]

    @classmethod
    def from_list(cls, metadata_list: list[UUID]) -> 'MetadataQueryListSchema':
        metadata = [MetadataQuerySchema(id=metadata_id) for metadata_id in metadata_list]
        return cls(metadata=metadata)


class MetadataSchema(BaseSchema):
    id: UUID
    metadata_id: UUID
    kg_instance_id: UUID
    uploaded_at: datetime

    class Config:
        orm_mode = True


class MetadataListSchema(BaseSchema):
    metadata: list[MetadataSchema]

    class Config:
        orm_mode = True


class MetadataCreateSchema(BaseSchema):
    metadata_id: UUID
    kg_instance_id: UUID
