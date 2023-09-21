# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging
from uuid import UUID

import httpx
from fastapi import Depends

from kg_integration.config import Settings
from kg_integration.config import get_settings
from kg_integration.core.exceptions import NoProject
from kg_integration.core.exceptions import UnhandledException

logger = logging.getLogger(__name__)


class DatasetManager:
    def __init__(self, settings: Settings) -> None:
        self.url = settings.DATASET_SERVICE + '/v1/'

    async def get_project_id(self, dataset_code: str) -> str:
        logger.info(f'Getting project id from dataset code {dataset_code}')
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url + f'datasets/{dataset_code}')
            data = response.json()

        if response.status_code != 200:
            logger.error('Could not get dataset details from dataset service')
            raise UnhandledException('Could not get dataset details: ' + response.text)

        if not data.get('project_id'):
            raise NoProject()
        else:
            return data.get('project_id')

    async def get_all_project_datasets(self, project_id: UUID) -> list[str]:
        logger.info(f'Getting all datasets with project id {project_id}')
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.url + 'datasets/', params={'project_id': str(project_id), 'page_size': 10000}
            )
            data = response.json()

        if response.status_code != 200:
            logger.error('Could not get dataset details from dataset service')
            raise UnhandledException('Could not get dataset details: ' + response.text)

        return [dataset['code'] for dataset in data['result']]


async def get_dataset_manager(settings: Settings = Depends(get_settings)) -> DatasetManager:
    """Create a FastAPI callable dependency for DatasetManager."""
    return DatasetManager(settings)
