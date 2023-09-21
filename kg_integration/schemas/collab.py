# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from kg_integration.schemas.base import BaseSchema


class CollabCreationSchema(BaseSchema):
    """Collab creation schema."""

    name: str
    title: str
    description: str
    drive: bool | None = True
    chat: bool | None = True
    public: bool | None = False
