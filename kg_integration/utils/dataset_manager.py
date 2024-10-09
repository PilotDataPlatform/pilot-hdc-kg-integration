# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Any
from uuid import UUID

import httpx
from fastapi import Depends

from kg_integration.config import Settings
from kg_integration.config import get_settings
from kg_integration.core.exceptions import NoProject
from kg_integration.core.exceptions import UnhandledException
from kg_integration.logger import logger


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

    async def get_dataset_code(self, dataset_id: UUID) -> str:
        logger.info(f'Getting dataset code from dataset id {dataset_id}')
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url + f'datasets/{dataset_id}')
            data = response.json()

        if response.status_code != 200:
            logger.error('Could not get dataset details from dataset service')
            raise UnhandledException('Could not get dataset details: ' + response.text)

        return data.get('code')

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

    async def get_all_schema_templates(self) -> list[dict[str:Any]]:
        logger.info('Getting all metadata templates')
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url + 'dataset/default/schemaTPL/list',
                params={},
                data={},
            )
            data = response.json()

        if response.status_code != 200:
            logger.error('Could not get schema templates from dataset service')
            raise UnhandledException('Could not get templates: ' + response.text)

        return data

    async def get_openminds_template(self) -> UUID:
        templates = await self.get_all_schema_templates()
        for template in templates['result']:
            if template['name'] == 'Open_minds':
                return template['geid']
        else:
            raise UnhandledException('Cannot find OpenMINDS template for metadata')

    async def upload_new_openminds_schema(
        self, dataset_id: UUID, uploader: str, metadata: dict, filename: str | None, template: UUID
    ):
        logger.info(f'Uploading metadata to dataset {dataset_id}')
        kg_id = metadata['@id'].removeprefix('https://kg.ebrains.eu/api/instances/')
        filename = filename if filename else kg_id + '.jsonld'
        data = {
            'name': filename if filename.endswith('.jsonld') else filename + '.jsonld',
            'dataset_geid': str(dataset_id),
            'tpl_geid': str(template),
            'standard': 'open_minds',
            'system_defined': False,
            'is_draft': False,
            'content': metadata,
            'creator': uploader,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.url + 'schema',
                params={},
                json=data,
            )

        if response.status_code != 200:
            logger.error('Could not upload schema from KG to dataset')
            raise UnhandledException('Could not upload: ' + response.text)

        return response

    async def update_schema(self, metadata_id: UUID, username: str, metadata: dict) -> dict:
        logger.info(f'Updating metadata {metadata_id}')
        data = {
            'username': username,
            'activity': [],
            'content': metadata,
        }
        async with httpx.AsyncClient() as client:
            response = await client.put(
                self.url + f'schema/{metadata_id}',
                params={},
                json=data,
            )

        if response.status_code != 200:
            logger.error('Could not update schema from KG')
            raise UnhandledException('Could not update schema: ' + response.text)

        return response.json()


async def get_dataset_manager(settings: Settings = Depends(get_settings)) -> DatasetManager:
    """Create a FastAPI callable dependency for DatasetManager."""
    return DatasetManager(settings)
