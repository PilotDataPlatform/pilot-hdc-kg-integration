# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from uuid import UUID

import backoff
import httpx
from fastapi import Depends
from httpx import Response

from kg_integration.config import Settings
from kg_integration.config import get_settings
from kg_integration.core.exceptions import NoData
from kg_integration.core.exceptions import RemoteServiceException
from kg_integration.core.exceptions import UnhandledException
from kg_integration.logger import logger


class KGManager:
    """Manager for KG API connection."""

    def __init__(self, settings: Settings) -> None:
        self.url = settings.KG_URL + 'v3/'
        self.timeout = settings.EXTERNAL_SERVICE_TIMEOUT

    @staticmethod
    def check_response_error(response: Response) -> Response:
        """Check if returned response contains errors."""
        if response.is_error:
            raise RemoteServiceException(status=response.status_code, details=response.text)

        return response

    def check_response_data(self, response: Response) -> dict[Any, str] | list[dict[Any, str]] | str:
        """Check if returned response contains KG data and return it."""
        self.check_response_error(response)

        if (data := response.json().get('data')) is None:
            raise NoData()

        return data

    @staticmethod
    def clean_data(data: dict[Any, Any]) -> dict[Any, Any]:
        return {
            k: v
            for k, v in data.items()
            if not isinstance(k, str) or not k.startswith('https://core.kg.ebrains.eu/vocab/meta/')
        }

    async def get_spaces(self, token: str) -> list[dict[Any, str]]:
        """Get all available spaces for user."""
        headers = {'Authorization': 'Bearer ' + token}
        logger.info('Getting all the spaces')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url + 'spaces', headers=headers)
            return self.check_response_data(response)

    async def get_space_details(self, space: str, token: str) -> dict[Any, str]:
        """Get space details by space ID."""
        headers = {'Authorization': 'Bearer ' + token}
        logger.info(f'Getting details for space {space}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url + f'spaces/{space}', headers=headers)
            return self.check_response_data(response)

    @backoff.on_exception(backoff.fibo, UnhandledException, max_tries=5, jitter=None)
    async def create_space(self, name: str, token: str) -> Response:
        """Create space with a given name."""
        headers = {'Authorization': 'Bearer ' + token}
        logger.info(f'Creating a space {name}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(self.url + f'spaces/{name}/specification', headers=headers)
            if response.status_code != 200:
                logger.error(f'Could not create a space {name}')
                raise UnhandledException('Could not create a space: ' + response.text)

            return response

    async def get_metadata(self, space: str, stage: str, _type: str, token: str) -> list[dict[Any, str]]:
        """Get metadata for given parameters."""
        headers = {'Authorization': 'Bearer ' + token}
        params = {'space': space, 'stage': stage, 'type': _type}
        logger.info(f'Getting metadata from space {space}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url + 'instances', params=params, headers=headers)
            return self.check_response_data(response)

    async def get_metadata_details(self, kg_instance_id: UUID, stage: str, token: str) -> dict[Any, str]:
        """Get metadata for given ID."""
        headers = {'Authorization': 'Bearer ' + token}
        params = {'stage': stage}
        logger.info(f'Getting details of metadata {kg_instance_id}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url + f'instances/{kg_instance_id}', params=params, headers=headers)
            return self.check_response_data(response)

    async def check_metadata_status(self, kg_instance_id: UUID, token: str) -> str:
        headers = {'Authorization': 'Bearer ' + token}
        params = {'releaseTreeScope': 'TOP_INSTANCE_ONLY'}
        logger.info(f'Checking status of metadata {kg_instance_id}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                self.url + f'instances/{kg_instance_id}/release/status', params=params, headers=headers
            )
            return self.check_response_data(response)

    async def upload_metadata(self, space: str, data: dict[Any, Any], token: str) -> dict[Any, str]:
        """Upload metadata to given space."""
        headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
        params = {'space': space}
        data = self.clean_data(data)
        logger.info(f'Uploading metadata {data} to space {space}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self.url + 'instances', params=params, json=data, headers=headers)
            return self.check_response_data(response)

    async def update_metadata(self, instance_id: UUID, data: dict[Any, Any], token: str) -> dict[Any, str]:
        """Update given instance in the KG."""
        headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
        data = self.clean_data(data)
        logger.info(f'Updating instance {instance_id} with metadata {data}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(self.url + f'instances/{instance_id}', json=data, headers=headers)
            return self.check_response_data(response)

    async def delete_metadata(self, metadata_id: UUID, token: str) -> Response:
        """Delete metadata with given ID."""
        headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
        logger.info(f'Deleting metadata {metadata_id}')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(self.url + f'instances/{metadata_id}', headers=headers)
            return self.check_response_error(response)

    async def get_user_details(self, token: str) -> dict[Any, str]:
        """Get information about given user's token."""
        headers = {'Authorization': 'Bearer ' + token}
        logger.info('Getting user information')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url + 'users/me', headers=headers)
            return self.check_response_data(response)


async def get_kg_manager(settings: Settings = Depends(get_settings)) -> KGManager:
    """Create a FastAPI callable dependency for KGManager."""
    return KGManager(settings)
