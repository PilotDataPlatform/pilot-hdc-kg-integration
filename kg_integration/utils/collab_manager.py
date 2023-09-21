# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging
from typing import Any

import backoff
import httpx
from fastapi import Depends
from httpx import Response

from kg_integration.config import Settings
from kg_integration.config import get_settings
from kg_integration.core.exceptions import NoData
from kg_integration.core.exceptions import RemoteServiceException
from kg_integration.core.exceptions import UnhandledException
from kg_integration.schemas.collab import CollabCreationSchema

logger = logging.getLogger(__name__)


class CollabManager:

    PROJECT_TO_COLLAB_ROLES_MAPPING = {'admin': 'administrator', 'collaborator': 'editor', 'contributor': 'viewer'}

    def __init__(self, settings: Settings) -> None:
        self.url = settings.COLLAB_URL + 'v1/'
        self.jobstatus_url = settings.COLLAB_URL + 'jobstatus/'
        self.timeout = settings.EXTERNAL_SERVICE_TIMEOUT

    @staticmethod
    def check_response_error(response: Response) -> Response:
        """Check if returned response contains Collaboratory data and return it."""
        if response.is_error:
            raise RemoteServiceException(status=response.status_code, details=response.text)
        else:
            return response

    def check_response_data(self, response: Response) -> dict[Any, str] | list[dict[Any, str]]:
        """Check if returned response contains Collab data and return it."""
        self.check_response_error(response)

        if (data := response.json().get('data')) is None:
            raise NoData()

        return data

    async def get_collabs(self, token: str, search: str | None = None) -> Response:
        """Get all available Collabs or search with search keyword."""
        headers = {'Authorization': 'Bearer ' + token}
        logger.info('Getting all the collabs')
        if search:
            params = {'search': search}
        else:
            params = {}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url + 'collabs', headers=headers, params=params)
            return self.check_response_error(response)

    async def get_collab_details(self, collab: str, token: str) -> Response:
        """Get the detailed description of the Collab."""
        headers = {'Authorization': 'Bearer ' + token}
        logger.info(f'Getting details for collab {collab}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url + f'collabs/{collab}', headers=headers)
            return self.check_response_error(response)

    @backoff.on_exception(backoff.fibo, RemoteServiceException, max_tries=5, jitter=None)
    async def create_collab(
        self,
        name: str,
        token: str,
        title: str | None = None,
        description: str | None = None,
    ) -> None | dict[Any, str]:
        """Create a Collab with given name, title and description."""
        headers = {'Authorization': 'Bearer ' + token}
        if not title:
            title = f'Collab {name} for KG space'

        if not description:
            description = f'Collab {name} is created to manage KG space collab-{name}'

        data = CollabCreationSchema(name=name, title=title, description=description)
        logger.info(f'Creating collab {name}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.url + 'collabs', headers=headers, json=data.dict())

            if response.status_code == 409:
                logger.warning(f'Collab {name} was already created')
                return None

            else:
                data = self.check_response_error(response).json()
                logger.info(f'Collab {name} was successfully created')
                return data

    @backoff.on_exception(backoff.fibo, UnhandledException, max_tries=10, jitter=None)
    async def check_collab_creation_status(self, job: str, token: str):
        """Check if creation of Collab's jobs have finished."""
        headers = {'Authorization': 'Bearer ' + token}
        with httpx.Client(timeout=self.timeout) as client:
            logger.info(f'Checking job status for: {job}')
            response = client.get(self.jobstatus_url + job, headers=headers)

            if response.status_code != 200:
                raise UnhandledException('Collab creation job is not finished yet')

    @backoff.on_exception(backoff.fibo, RemoteServiceException, max_tries=5, jitter=None)
    async def add_user_to_collab(self, collab: str, role: str, username: str, token: str) -> Response:
        """Add user to the Collab with given role."""
        headers = {'Authorization': 'Bearer ' + token}
        logger.info(f'Adding user {username} to collab {collab} with role {role}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(self.url + f'collabs/{collab}/team/{role}/users/{username}', headers=headers)

            if response.status_code == 409:
                logger.warning(f'User {username} was already added to the collab {collab}')
                return response

            return self.check_response_error(response)

    async def sync_users_in_collab(self, collab: str, user_list: list[dict[Any, str]], token: str) -> None:
        """Add all the users of the project to collab with corresponding roles."""
        logger.info(f'Syncing users of {collab}')
        for user in user_list:
            collab_role = self.PROJECT_TO_COLLAB_ROLES_MAPPING[user.get('permission')]
            await self.add_user_to_collab(collab=collab, role=collab_role, username=user.get('username'), token=token)

    async def remove_user_from_collab(self, collab: str, role: str, username: str, token: str) -> Response:
        """Remove user from the Collab."""
        headers = {'Authorization': 'Bearer ' + token}
        logger.info(f'Removing user {username} from collab {collab} with role {role}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(self.url + f'collabs/{collab}/team/{role}/users/{username}', headers=headers)
            return self.check_response_error(response)

    async def get_user_list(self, collab: str, role: str, token: str) -> Response:
        """List all the users of the Collab with given role."""
        headers = {'Authorization': 'Bearer ' + token}
        logger.info(f'Getting user list from collab {collab} with role {role}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url + f'collabs/{collab}/team/{role}', headers=headers)
            return self.check_response_error(response)

    async def assure_collab_created(
        self, name: str, token: str, title: str | None = None, description: str | None = None
    ):
        """Full Collab creation workflow with assurance of Keycloak roles being created."""
        collab_jobs = await self.create_collab(name, token, title, description)
        if collab_jobs is not None:
            keycloak_job = collab_jobs['collabCreationKeycloakJob']
            await self.check_collab_creation_status(keycloak_job, token)

        return 'Success'


async def get_collab_manager(settings: Settings = Depends(get_settings)) -> CollabManager:
    """Create a FastAPI callable dependency for CollabManager."""
    return CollabManager(settings)
