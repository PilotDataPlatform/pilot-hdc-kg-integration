# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import Depends

from kg_integration.config import Settings
from kg_integration.config import get_settings


class NamespaceHelper:
    """Helper class to transform project code to appropriate name for each API."""

    def __init__(self, settings: Settings):
        self.collab_prefix = settings.COLLAB_PREFIX
        self.kg_prefix = settings.KG_PREFIX

    def for_collab(self, name) -> str:
        """Add collab protected namespace prefix."""
        return self.collab_prefix + name

    def for_kg(self, name) -> str:
        """Add KG space protected namespace prefix."""
        if name != 'myspace':
            return self.kg_prefix + self.for_collab(name)
        else:
            return name


async def get_namespace_helper(settings: Settings = Depends(get_settings)) -> NamespaceHelper:
    """Create a FastAPI callable dependency for SpaceNameHelper."""
    return NamespaceHelper(settings)
