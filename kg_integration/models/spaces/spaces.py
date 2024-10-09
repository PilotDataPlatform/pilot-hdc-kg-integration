# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from sqlalchemy import TIMESTAMP
from sqlalchemy import VARCHAR
from sqlalchemy import Column
from sqlalchemy import func

from kg_integration.config import get_settings
from kg_integration.models import DBModel

settings = get_settings()


class Spaces(DBModel):
    __tablename__ = 'spaces'
    __table_args__ = {'schema': settings.RDS_SCHEMA_DEFAULT}
    name = Column(VARCHAR, primary_key=True)
    creator = Column(VARCHAR, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
