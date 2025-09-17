# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Response
from starlette.responses import JSONResponse

from kg_integration.core.exceptions import NotFound
from kg_integration.models import MetadataCRUD
from kg_integration.models import get_metadata_crud
from kg_integration.schemas.metadata import MetadataCreateSchema
from kg_integration.schemas.metadata import MetadataKGResponseListSchema
from kg_integration.schemas.metadata import MetadataKGResponseSchema
from kg_integration.schemas.metadata import MetadataListSchema
from kg_integration.schemas.metadata import MetadataQueryListSchema
from kg_integration.utils.dataset_manager import DatasetManager
from kg_integration.utils.dataset_manager import get_dataset_manager
from kg_integration.utils.helpers import NamespaceHelper
from kg_integration.utils.helpers import get_namespace_helper
from kg_integration.utils.keycloak_manager import KeycloakManager
from kg_integration.utils.keycloak_manager import get_keycloak_manager
from kg_integration.utils.kg_manager import KGManager
from kg_integration.utils.kg_manager import get_kg_manager
from kg_integration.utils.spaces_activity_log import KGActivityLog

router = APIRouter(prefix='/metadata', tags=['Knowledge Graph metadata'])


@router.get('/', summary='List uploaded instances for given parameters.')
async def get_metadata(
    space: str,
    type: str,  # noqa: A002
    stage: str = Query(enum=['IN_PROGRESS', 'RELEASED']),
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    kg_manager: KGManager = Depends(get_kg_manager),
) -> MetadataKGResponseListSchema:
    external_token = await keycloak_manager.exchange_token(token)
    data = await kg_manager.get_metadata(namespace.for_kg(space), stage, type, external_token)
    return MetadataKGResponseListSchema.from_kg_response(data)


@router.post('/', summary='Check a list of metadata if they were uploaded.')
async def check_metadata(
    metadata_list: MetadataQueryListSchema,
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
) -> MetadataListSchema:
    result = await metadata_crud.retrieve_by_metadata_ids([metadata.id for metadata in metadata_list.metadata])
    return MetadataListSchema(metadata=result)


@router.get('/{metadata_id}', summary='Get metadata by ID.')
async def get_metadata_by_id(
    metadata_id: UUID,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
) -> JSONResponse:
    external_token = await keycloak_manager.exchange_token(token)
    metadata = await kg_manager.get_metadata_details(
        kg_instance_id=metadata_id, stage='IN_PROGRESS', token=external_token
    )
    return JSONResponse(content=metadata)


@router.get('/upload/{kg_instance_id}/{dataset_id}', summary='Download metadata from KG by ID to specified dataset.')
async def download_metadata_by_id(
    kg_instance_id: UUID,
    dataset_id: UUID,
    uploader: str,
    filename: str | None = Query(default=None),
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
    activity_log: KGActivityLog = Depends(),
) -> JSONResponse:
    external_token = await keycloak_manager.exchange_token(token)
    openminds_schema = await dataset_manager.get_openminds_template()
    metadata_status = await kg_manager.check_metadata_status(kg_instance_id=kg_instance_id, token=external_token)
    stage = 'IN_PROGRESS' if metadata_status == 'UNRELEASED' else 'RELEASED'
    metadata = await kg_manager.get_metadata_details(kg_instance_id=kg_instance_id, stage=stage, token=external_token)
    response = await dataset_manager.upload_new_openminds_schema(
        dataset_id=dataset_id, uploader=uploader, metadata=metadata, filename=filename, template=openminds_schema
    )
    data = response.json()
    await metadata_crud.create(
        MetadataCreateSchema(
            metadata_id=data['result']['geid'], kg_instance_id=kg_instance_id, dataset_id=dataset_id, direction='HDC'
        )
    )
    dataset_code = await dataset_manager.get_dataset_code(dataset_id=dataset_id)
    await activity_log.send_metadata_on_download_event(
        dataset_code=dataset_code, target_name=filename or str(kg_instance_id) + '.jsonld', creator=uploader
    )
    return JSONResponse(content=data['result'])


@router.get('/refresh/{metadata_id}', summary='Refresh metadata from KG.')
async def update_metadata_from_kg_to_hdc(
    metadata_id: UUID,
    username: str,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
    activity_log: KGActivityLog = Depends(),
) -> JSONResponse:
    external_token = await keycloak_manager.exchange_token(token)
    uploaded_metadata = await metadata_crud.retrieve_by_metadata_id(metadata_id)
    if not uploaded_metadata:
        raise NotFound()
    else:
        metadata_status = await kg_manager.check_metadata_status(
            kg_instance_id=uploaded_metadata.kg_instance_id, token=external_token
        )
        stage = 'IN_PROGRESS' if metadata_status == 'UNRELEASED' else 'RELEASED'
        current_kg_metadata = await kg_manager.get_metadata_details(
            kg_instance_id=uploaded_metadata.kg_instance_id, stage=stage, token=external_token
        )
        refreshed_metadata = await dataset_manager.update_schema(metadata_id, username, current_kg_metadata)
        await metadata_crud.update_metadata_direction(uploaded_metadata, 'HDC')
        dataset_code = await dataset_manager.get_dataset_code(dataset_id=uploaded_metadata.dataset_id)
        await activity_log.send_metadata_on_refresh_event(
            dataset_code=dataset_code, target_name=refreshed_metadata['result']['name'], creator=username
        )
    return refreshed_metadata['result']


@router.get('/refresh/dataset/{dataset_id}', summary='Bulk refresh metadata from KG for whole dataset.')
async def bulk_update_metadata_from_kg_to_hdc(
    dataset_id: UUID,
    username: str,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
    activity_log: KGActivityLog = Depends(),
) -> JSONResponse:
    external_token = await keycloak_manager.exchange_token(token)
    dataset_metadata = await metadata_crud.retrieve_by_dataset_id(dataset_id)
    refreshed_metadata = []
    for metadata in dataset_metadata:
        metadata_status = await kg_manager.check_metadata_status(
            kg_instance_id=metadata.kg_instance_id, token=external_token
        )
        stage = 'IN_PROGRESS' if metadata_status == 'UNRELEASED' else 'RELEASED'
        current_kg_metadata = await kg_manager.get_metadata_details(
            kg_instance_id=metadata.kg_instance_id, stage=stage, token=external_token
        )
        data = await dataset_manager.update_schema(metadata.metadata_id, username, current_kg_metadata)
        refreshed_metadata.append(data['result'])
        await metadata_crud.update_metadata_direction(metadata, 'HDC')
        dataset_code = await dataset_manager.get_dataset_code(dataset_id=dataset_id)
        await activity_log.send_metadata_on_refresh_event(
            dataset_code=dataset_code, target_name=data['result']['name'], creator=username
        )
    return refreshed_metadata


@router.post('/upload', summary='Upload metadata to given KG space.', response_model=MetadataKGResponseSchema)
async def upload_metadata(
    space: str,
    metadata: dict,
    metadata_id: UUID,
    dataset_id: UUID,
    uploader: str,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    kg_manager: KGManager = Depends(get_kg_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
    activity_log: KGActivityLog = Depends(),
) -> MetadataKGResponseSchema:
    external_token = await keycloak_manager.exchange_token(token)
    data = await kg_manager.upload_metadata(namespace.for_kg(space), metadata, external_token)
    instance = MetadataKGResponseSchema.from_kg_response(data)
    await metadata_crud.create(
        MetadataCreateSchema(metadata_id=metadata_id, kg_instance_id=instance.id, dataset_id=dataset_id, direction='KG')
    )
    dataset_code = await dataset_manager.get_dataset_code(dataset_id=dataset_id)
    await activity_log.send_metadata_on_upload_event(dataset_code=dataset_code, creator=uploader)
    return instance


@router.put(
    '/update/{metadata_id}', summary='Update metadata upload with given ID.', response_model=MetadataKGResponseSchema
)
async def update_metadata_from_hdc_to_kg(
    space: str,
    metadata: dict,
    filename: str,
    metadata_id: UUID,
    dataset_id: UUID,
    uploader: str,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    kg_manager: KGManager = Depends(get_kg_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
    activity_log: KGActivityLog = Depends(),
) -> MetadataKGResponseSchema:
    external_token = await keycloak_manager.exchange_token(token)
    try:
        metadata_upload = await metadata_crud.retrieve_by_metadata_id(metadata_id)
        instance_id = metadata_upload.kg_instance_id
        data = await kg_manager.update_metadata(instance_id=instance_id, data=metadata, token=external_token)
        instance = MetadataKGResponseSchema.from_kg_response(data)
        await metadata_crud.update_metadata_direction(metadata_upload, 'KG')
        return instance
    except NotFound:
        data = await kg_manager.upload_metadata(namespace.for_kg(space), metadata, external_token)
        instance = MetadataKGResponseSchema.from_kg_response(data)
        await metadata_crud.create(
            MetadataCreateSchema(
                metadata_id=metadata_id, kg_instance_id=instance.id, dataset_id=dataset_id, direction='KG'
            )
        )
        dataset_code = await dataset_manager.get_dataset_code(dataset_id=dataset_id)
        await activity_log.send_metadata_on_upload_event(
            dataset_code=dataset_code, target_name=filename, creator=uploader
        )
        return instance


@router.put(
    '/update/dataset/{dataset_id}',
    summary='Update metadata uploads for the whole dataset',
)
async def bulk_update_metadata_from_hdc_to_kg(
    dataset_id: UUID,
    username: str,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    activity_log: KGActivityLog = Depends(),
) -> JSONResponse:
    external_token = await keycloak_manager.exchange_token(token)
    dataset_code = await dataset_manager.get_dataset_code(dataset_id=dataset_id)
    all_dataset_metadata = await dataset_manager.get_all_dataset_schemas(dataset_id)
    dataset_metadata = {metadata['geid']: metadata['content'] for metadata in all_dataset_metadata['result']}

    updated_metadata = []
    for metadata_id in dataset_metadata:
        try:
            existing_metadata = await metadata_crud.retrieve_by_metadata_id(metadata_id)
            instance_id = existing_metadata.kg_instance_id
            data = await kg_manager.update_metadata(
                instance_id=instance_id, data=dataset_metadata[metadata_id], token=external_token
            )
            await metadata_crud.update_metadata_direction(existing_metadata, 'KG')
        except NotFound:
            data = await kg_manager.upload_metadata(
                namespace.for_kg(dataset_code), dataset_metadata[metadata_id], external_token
            )
            instance_id = data.get('@id').removeprefix('https://kg.ebrains.eu/api/instances/')
            await metadata_crud.create(
                MetadataCreateSchema(
                    metadata_id=metadata_id, kg_instance_id=instance_id, dataset_id=dataset_id, direction='KG'
                )
            )
        updated_metadata.append(data)
        await activity_log.send_metadata_on_upload_event(
            dataset_code=dataset_code, target_name=str(metadata_id), creator=username
        )
    return updated_metadata


@router.delete('/{kg_instance_id}', summary='Delete metadata with given ID.')
async def delete_metadata(
    kg_instance_id: UUID,
    username: str,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
    activity_log: KGActivityLog = Depends(),
) -> Response:
    external_token = await keycloak_manager.exchange_token(token)
    await kg_manager.delete_metadata(kg_instance_id, external_token)
    metadata = await metadata_crud.retrieve_by_kg_instance_id(kg_instance_id)
    await metadata_crud.delete_by_kg_instance_id(kg_instance_id)
    dataset_code = await dataset_manager.get_dataset_code(metadata.dataset_id)
    await activity_log.send_metadata_on_delete_event(
        dataset_code=dataset_code, target_name=str(kg_instance_id), creator=username
    )
    return Response(status_code=204)
