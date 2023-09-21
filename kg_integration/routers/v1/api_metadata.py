# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Response

from kg_integration.core.exceptions import NotFound
from kg_integration.models import MetadataCRUD
from kg_integration.models import get_metadata_crud
from kg_integration.schemas.metadata import MetadataCreateSchema
from kg_integration.schemas.metadata import MetadataKGResponseListSchema
from kg_integration.schemas.metadata import MetadataKGResponseSchema
from kg_integration.schemas.metadata import MetadataListSchema
from kg_integration.schemas.metadata import MetadataQueryListSchema
from kg_integration.schemas.metadata import MetadataSchema
from kg_integration.utils.helpers import NamespaceHelper
from kg_integration.utils.helpers import get_namespace_helper
from kg_integration.utils.keycloak_manager import KeycloakManager
from kg_integration.utils.keycloak_manager import get_keycloak_manager
from kg_integration.utils.kg_manager import KGManager
from kg_integration.utils.kg_manager import get_kg_manager

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


@router.get('/{metadata_id}', summary='Get metadata by ID.', response_model=MetadataSchema)
async def get_metadata_by_id(
    metadata_id: UUID,
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
) -> Response:
    metadata = await metadata_crud.retrieve_by_metadata_id(metadata_id=metadata_id)
    return metadata


@router.post('/upload', summary='Upload metadata to given KG space.', response_model=MetadataKGResponseSchema)
async def upload_metadata(
    space: str,
    metadata: dict,
    metadata_id: UUID,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    kg_manager: KGManager = Depends(get_kg_manager),
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
) -> MetadataKGResponseSchema:
    external_token = await keycloak_manager.exchange_token(token)
    data = await kg_manager.upload_metadata(namespace.for_kg(space), metadata, external_token)
    instance = MetadataKGResponseSchema.from_kg_response(data)
    await metadata_crud.create(MetadataCreateSchema(metadata_id=metadata_id, kg_instance_id=instance.id))
    return instance


@router.put(
    '/update/{metadata_id}', summary='Update metadata upload with given ID.', response_model=MetadataKGResponseSchema
)
async def update_metadata(
    space: str,
    metadata: dict,
    metadata_id: UUID,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    kg_manager: KGManager = Depends(get_kg_manager),
    metadata_crud: MetadataCRUD = Depends(get_metadata_crud),
) -> MetadataKGResponseSchema:
    external_token = await keycloak_manager.exchange_token(token)
    try:
        metadata_upload = await metadata_crud.retrieve_by_metadata_id(metadata_id)
        instance_id = metadata_upload.kg_instance_id
        data = await kg_manager.update_metadata(instance_id=instance_id, data=metadata, token=external_token)
        instance = MetadataKGResponseSchema.from_kg_response(data)
        await metadata_crud.create(MetadataCreateSchema(metadata_id=metadata_id, kg_instance_id=instance.id))
        return instance
    except NotFound:
        data = await kg_manager.upload_metadata(namespace.for_kg(space), metadata, external_token)
        instance = MetadataKGResponseSchema.from_kg_response(data)
        await metadata_crud.create(MetadataCreateSchema(metadata_id=metadata_id, kg_instance_id=instance.id))
        return instance


@router.delete('/{metadata_id}', summary='Delete metadata with given ID.')
async def delete_metadata(
    metadata_id: UUID,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
) -> Response:
    external_token = await keycloak_manager.exchange_token(token)
    await kg_manager.delete_metadata(metadata_id, external_token)
    return Response(status_code=204)
