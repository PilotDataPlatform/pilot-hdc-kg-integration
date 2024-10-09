# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import Sequence
from typing import Any

from fastapi import Depends

from kg_integration.config import Settings
from kg_integration.config import get_settings
from kg_integration.core.exceptions import RemoteServiceException
from kg_integration.core.exceptions import UnhandledException
from kg_integration.logger import logger
from kg_integration.models import SpacesCRUD
from kg_integration.models import get_spaces_crud
from kg_integration.utils.collab_manager import CollabManager
from kg_integration.utils.collab_manager import get_collab_manager
from kg_integration.utils.kg_manager import KGManager
from kg_integration.utils.kg_manager import get_kg_manager


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


class HeavyTasksHelper:
    """Helper class to put heavy external API requests to background."""

    def __init__(
        self,
        kg_manager: KGManager,
        namespace: NamespaceHelper,
        collab_manager: CollabManager,
        spaces_crud: SpacesCRUD,
    ):
        self.kg_manager = kg_manager
        self.namespace = namespace
        self.collab_manager = collab_manager
        self.spaces_crud = spaces_crud

    async def create_space(
        self,
        space_name: str,
        users: list[dict[Any, str]],
        external_token: str,
        service_account_token: str,
    ):
        try:
            user_data = await self.kg_manager.get_user_details(external_token)
            username = user_data.get('http://schema.org/alternateName')

            await self.collab_manager.assure_collab_created(
                self.namespace.for_collab(space_name), service_account_token
            )
            await self.collab_manager.add_user_to_collab(
                self.namespace.for_collab(space_name), 'administrator', username, service_account_token
            )

            await self.collab_manager.sync_users_in_collab(self.namespace.for_collab(space_name), users, external_token)
            response = await self.kg_manager.create_space(self.namespace.for_kg(space_name), service_account_token)
            if response.is_success:
                logger.info(f'Space {space_name} was successfully created')
            else:
                logger.error(f'Something went wrong with space creation: {response.content}')
        except UnhandledException as e:
            logger.error(f'Could not create a space: {e}')

    async def update_user_task(
        self,
        username: str,
        current_role: str,
        new_role: str,
        dataset_codes: Sequence[str],
        service_account_token: str,
    ):
        try:
            for dataset_code in dataset_codes:
                await self.collab_manager.remove_user_from_collab(
                    self.namespace.for_collab(dataset_code), current_role, username, service_account_token
                )
                await self.collab_manager.add_user_to_collab(
                    self.namespace.for_collab(dataset_code), new_role, username, service_account_token
                )
        except RemoteServiceException as e:
            logger.error(f'Could not update user: {e}')

    async def remove_user_task(
        self,
        username: str,
        role: str,
        dataset_codes: Sequence[str],
        service_account_token: str,
    ):
        try:
            for dataset_code in dataset_codes:
                await self.collab_manager.remove_user_from_collab(
                    self.namespace.for_collab(dataset_code), role, username, service_account_token
                )
        except RemoteServiceException as e:
            logger.error(f'Could not update user: {e}')

    async def add_user_task(
        self,
        username: str,
        role: str,
        dataset_codes: Sequence[str],
        service_account_token: str,
    ):
        try:
            for dataset_code in dataset_codes:
                await self.collab_manager.add_user_to_collab(
                    self.namespace.for_collab(dataset_code), role, username, service_account_token
                )
        except RemoteServiceException as e:
            logger.error(f'Could not update user: {e}')


async def get_namespace_helper(settings: Settings = Depends(get_settings)) -> NamespaceHelper:
    """Create a FastAPI callable dependency for SpaceNameHelper."""
    return NamespaceHelper(settings)


async def get_heavy_tasks_helper(
    kg_manager: KGManager = Depends(get_kg_manager),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    collab_manager: CollabManager = Depends(get_collab_manager),
    spaces_crud: SpacesCRUD = Depends(get_spaces_crud),
) -> HeavyTasksHelper:
    """Create a FastAPI callable dependency for SpaceNameHelper."""
    return HeavyTasksHelper(kg_manager, namespace, collab_manager, spaces_crud)
