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


class AuthManager:
    def __init__(self, settings: Settings) -> None:
        self.url = settings.AUTH_SERVICE + '/v1/'
        self.roles = ('admin', 'collaborator', 'contributor')

    async def get_project_users(self, project_code: str) -> list:
        body = {'role_names': [f'{project_code}-{role}' for role in self.roles], 'status': 'active'}
        logger.info(f'Getting all the users and their roles from project {project_code}')
        async with httpx.AsyncClient() as client:
            response = await client.post(self.url + 'admin/roles/users', json=body)
            data = response.json()

        if response.status_code != 200:
            logger.error(f'Could not get users of the project {project_code}')
            raise UnhandledException('Could not get users of the project: ' + response.text)

        return data.get('result', [])


async def get_auth_manager(settings: Settings = Depends(get_settings)) -> AuthManager:
    """Create a FastAPI callable dependency for AuthManager."""
    return AuthManager(settings)
