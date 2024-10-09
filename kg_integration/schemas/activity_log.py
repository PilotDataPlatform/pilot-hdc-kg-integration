# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json
from datetime import datetime
from datetime import timezone
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


def get_current_datetime():
    return datetime.now(timezone.utc)


class BaseSchema(BaseModel):
    """Base class for all available schemas."""

    def to_payload(self) -> dict[str, str]:
        return json.loads(self.model_dump_json(by_alias=True))

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.strftime('%Y-%m-%dT%H:%M:%S'),
        }
    )


class ActivityDetailsSchema(BaseSchema):
    name: str
    targets: list[str]


class ActivitySchema(BaseSchema):
    action: str
    resource: str
    detail: ActivityDetailsSchema

    def get_changes(self) -> list[dict[str, Any]]:
        return [{'property': target.lower() for target in self.detail.targets}]


class BaseActivityLogSchema(BaseModel):
    activity_time: datetime = Field(default_factory=get_current_datetime)
    changes: list[dict[str, Any]] = []
    activity_type: str
    user: str
    container_code: str


class SpaceActivityLogSchema(BaseActivityLogSchema):
    version: str | None = None
    target_name: str | None = None


class MetadataActivityLogSchema(BaseActivityLogSchema):
    version: str | None = None
    target_name: str | None = None
