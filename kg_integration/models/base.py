# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math
from typing import TypeVar

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import conint
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base

from kg_integration.config import get_settings

settings = get_settings()

DBModel = declarative_base(metadata=MetaData(schema=settings.RDS_SCHEMA_DEFAULT))


class Pagination(BaseModel):
    """Base pagination control parameters."""

    page: conint(ge=1) = 1
    page_size: conint(ge=0) = 20

    @property
    def limit(self) -> int:
        return self.page_size

    @property
    def offset(self) -> int:
        return self.page_size * (self.page - 1)

    def is_disabled(self) -> bool:
        return self.page_size == 0


class Page(BaseModel):
    """Represent one page of the response."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    pagination: Pagination
    count: int
    entries: list[DBModel]

    @property
    def number(self) -> int:
        return self.pagination.page

    @property
    def total_pages(self) -> int:
        return math.ceil(self.count / self.pagination.page_size) if self.pagination.page_size else 0


PageType = TypeVar('PageType', bound=Page)
