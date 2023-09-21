# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Response
from starlette.status import HTTP_201_CREATED

from kg_integration.core.exceptions import NotFound
from kg_integration.core.exceptions import SpaceAlreadyExists
from kg_integration.models import SpacesCRUD
from kg_integration.models import get_spaces_crud
from kg_integration.schemas.space import SpaceListResponseSchema
from kg_integration.schemas.space import SpaceListSchema
from kg_integration.schemas.space import SpaceSchema
from kg_integration.utils.auth_manager import AuthManager
from kg_integration.utils.auth_manager import get_auth_manager
from kg_integration.utils.collab_manager import CollabManager
from kg_integration.utils.collab_manager import get_collab_manager
from kg_integration.utils.dataset_manager import DatasetManager
from kg_integration.utils.dataset_manager import get_dataset_manager
from kg_integration.utils.helpers import NamespaceHelper
from kg_integration.utils.helpers import get_namespace_helper
from kg_integration.utils.keycloak_manager import KeycloakManager
from kg_integration.utils.keycloak_manager import get_keycloak_manager
from kg_integration.utils.kg_manager import KGManager
from kg_integration.utils.kg_manager import get_kg_manager
from kg_integration.utils.project_manager import ProjectManager
from kg_integration.utils.project_manager import get_project_manager

router = APIRouter(prefix='/spaces', tags=['Knowledge Graph spaces'])


@router.get('/', summary='List all available to user KG spaces.', response_model=SpaceListResponseSchema)
async def list_spaces(
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
) -> SpaceListResponseSchema:
    external_token = await keycloak_manager.exchange_token(token)
    data = await kg_manager.get_spaces(external_token)
    return SpaceListResponseSchema.from_kg_data(data)


@router.post('/', summary='Check a list of spaces if they exist.', response_model=SpaceListSchema)
async def check_spaces(
    spaces: SpaceListResponseSchema,
    kgspaces_crud: SpacesCRUD = Depends(get_spaces_crud),
) -> SpaceListSchema:
    result = await kgspaces_crud.retrieve_by_names([space.name for space in spaces.spaces])
    return SpaceListSchema(spaces=result)


@router.get('/{space}', summary='Get space details by space name.', response_model=SpaceSchema)
async def get_space(
    space: str,
    spaces_crud: SpacesCRUD = Depends(get_spaces_crud),
) -> Response:
    space = await spaces_crud.retrieve_by_name(space)
    return space


@router.post('/create', summary='Create a KG space.', response_model=SpaceSchema, status_code=HTTP_201_CREATED)
async def create_space(
    name: str = Query(description='Name of the space to be created'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    spaces_crud: SpacesCRUD = Depends(get_spaces_crud),
) -> Response:
    service_account_token = await keycloak_manager.get_service_account_token()
    response = await kg_manager.create_space(namespace.for_kg(name), service_account_token)
    if response.is_success:
        space = await spaces_crud.create_space(name, 'service')
        return space
    else:
        return response


@router.post(
    '/create/project/{project_code}',
    summary='Create a KG space for an HDC project.',
    response_model=SpaceSchema,
    status_code=HTTP_201_CREATED,
)
async def create_space_for_project(
    project_code: str,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    collab_manager: CollabManager = Depends(get_collab_manager),
    auth_manager: AuthManager = Depends(get_auth_manager),
    spaces_crud: SpacesCRUD = Depends(get_spaces_crud),
) -> Response:
    try:
        await spaces_crud.retrieve_by_name(project_code)
        raise SpaceAlreadyExists()
    except NotFound:
        pass

    external_token = await keycloak_manager.exchange_token(token)
    service_account_token = await keycloak_manager.get_service_account_token()

    await collab_manager.assure_collab_created(namespace.for_collab(project_code), external_token)

    user_data = await kg_manager.get_user_details(external_token)
    username = user_data.get('http://schema.org/alternateName')
    await collab_manager.add_user_to_collab(
        namespace.for_collab(project_code), 'administrator', username, service_account_token
    )

    users = await auth_manager.get_project_users(project_code)
    await collab_manager.sync_users_in_collab(namespace.for_collab(project_code), users, external_token)

    response = await kg_manager.create_space(namespace.for_kg(project_code), service_account_token)
    if response.is_success:
        space = await spaces_crud.create_space(project_code, username)
        return space
    else:
        return response


@router.post(
    '/create/dataset/{dataset_code}',
    summary='Create a KG space for a dataset.',
    response_model=SpaceSchema,
    status_code=HTTP_201_CREATED,
)
async def create_space_for_dataset(
    dataset_code: str,
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    kg_manager: KGManager = Depends(get_kg_manager),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    collab_manager: CollabManager = Depends(get_collab_manager),
    auth_manager: AuthManager = Depends(get_auth_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    project_manager: ProjectManager = Depends(get_project_manager),
    spaces_crud: SpacesCRUD = Depends(get_spaces_crud),
) -> Response:
    try:
        await spaces_crud.retrieve_by_name(dataset_code)
        raise SpaceAlreadyExists()
    except NotFound:
        pass

    external_token = await keycloak_manager.exchange_token(token)
    service_account_token = await keycloak_manager.get_service_account_token()

    await collab_manager.assure_collab_created(namespace.for_collab(dataset_code), service_account_token)

    user_data = await kg_manager.get_user_details(external_token)
    username = user_data.get('http://schema.org/alternateName')
    await collab_manager.add_user_to_collab(
        namespace.for_collab(dataset_code), 'administrator', username, service_account_token
    )

    project_id = await dataset_manager.get_project_id(dataset_code)
    project_code = await project_manager.get_project_code(project_id)
    users = await auth_manager.get_project_users(project_code)
    await collab_manager.sync_users_in_collab(namespace.for_collab(dataset_code), users, service_account_token)

    response = await kg_manager.create_space(namespace.for_kg(dataset_code), service_account_token)
    if response.is_success:
        space = await spaces_crud.create_space(dataset_code, username)
        return space
    else:
        return response
