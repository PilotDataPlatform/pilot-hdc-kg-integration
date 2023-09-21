# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging

import httpx
from fastapi import Depends

from kg_integration.config import Settings
from kg_integration.config import get_settings
from kg_integration.core.exceptions import UnhandledException

logger = logging.getLogger(__name__)


class ProjectManager:
    def __init__(self, settings: Settings) -> None:
        self.url = settings.PROJECT_SERVICE + '/v1/'

    async def get_project_code(self, project_id: str) -> str:
        logger.info(f'Getting project code from project service {project_id}')
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url + f'projects/{project_id}')
            data = response.json()

        if response.status_code != 200:
            logger.error('Could not get project details from project service')
            raise UnhandledException('Could not get project details: ' + response.text)

        return data.get('code')


async def get_project_manager(settings: Settings = Depends(get_settings)) -> ProjectManager:
    """Create a FastAPI callable dependency for ProjectManager."""
    return ProjectManager(settings)
