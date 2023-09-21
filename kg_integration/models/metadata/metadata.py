# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import uuid4

from sqlalchemy import TIMESTAMP
from sqlalchemy import UUID
from sqlalchemy import Column
from sqlalchemy import func

from kg_integration.config import get_settings
from kg_integration.models import DBModel

settings = get_settings()


class Metadata(DBModel):
    __tablename__ = 'metadata'
    __table_args__ = {'schema': settings.RDS_SCHEMA_DEFAULT}
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    metadata_id = Column(UUID(as_uuid=True))
    kg_instance_id = Column(UUID(as_uuid=True))
    uploaded_at = Column(TIMESTAMP(timezone=True), default=func.now(), nullable=False)
