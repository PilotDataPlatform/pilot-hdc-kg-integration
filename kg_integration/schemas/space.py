# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pydantic import ConfigDict

from kg_integration.schemas.base import BaseSchema


class SpaceSchema(BaseSchema):
    model_config = ConfigDict(from_attributes=True)

    name: str
    creator: str
    created_at: datetime


class SpaceListSchema(BaseSchema):
    model_config = ConfigDict(from_attributes=True)

    spaces: list[SpaceSchema]


class SpaceCreateSchema(BaseSchema):
    """KG Space schema for DB queries."""

    name: str
    creator: str


class SpaceResponseSchema(BaseSchema):
    """Response schema for requests."""

    name: str

    @classmethod
    def from_kg_data(cls, data: dict[str, Any]) -> 'SpaceResponseSchema':
        return cls(name=data['http://schema.org/name'])


class SpaceListResponseSchema(BaseSchema):
    """Default schema for multiple announcements in response."""

    spaces: list[SpaceResponseSchema]

    @classmethod
    def from_kg_data(cls, data: list[dict[str, Any]]) -> 'SpaceListResponseSchema':
        all_spaces = []
        for space in data:
            if (
                space['http://schema.org/name'].startswith('collab-hdc-')
                or space['http://schema.org/name'] == 'myspace'
            ):
                all_spaces.append(SpaceResponseSchema.from_kg_data(space))
        return cls(spaces=all_spaces)

    @classmethod
    def from_list(cls, data: Sequence[str]) -> 'SpaceListResponseSchema':
        spaces = [SpaceResponseSchema(name=name) for name in data]
        return cls(spaces=spaces)
