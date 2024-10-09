# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from uuid import UUID

from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import Query
from fastapi import Response

from kg_integration.models import SpacesCRUD
from kg_integration.models import get_spaces_crud
from kg_integration.utils.collab_manager import CollabManager
from kg_integration.utils.collab_manager import get_collab_manager
from kg_integration.utils.dataset_manager import DatasetManager
from kg_integration.utils.dataset_manager import get_dataset_manager
from kg_integration.utils.helpers import HeavyTasksHelper
from kg_integration.utils.helpers import NamespaceHelper
from kg_integration.utils.helpers import get_heavy_tasks_helper
from kg_integration.utils.helpers import get_namespace_helper
from kg_integration.utils.keycloak_manager import KeycloakManager
from kg_integration.utils.keycloak_manager import get_keycloak_manager

router = APIRouter(prefix='/users', tags=['Knowledge Graph users'])


@router.get('/{space}', summary='Get users on the given space')
async def get_user_list(
    space: str,
    role: str = Query(enum=['administrator', 'editor', 'viewer']),
    token: str = Query(default=None, description='Authentication bearer token from HDC Keycloak'),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    namespace: NamespaceHelper = Depends(get_namespace_helper),
    collab_manager: CollabManager = Depends(get_collab_manager),
):
    external_token = await keycloak_manager.exchange_token(token)
    response = await collab_manager.get_user_list(namespace.for_collab(space), role, external_token)
    return response.json()


@router.post('/{project_id}/{username}', summary='Invite user to all project datasets')
async def invite_user(
    project_id: UUID,
    username: str,
    role: str = Query(enum=['administrator', 'editor', 'viewer']),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    spaces_crud: SpacesCRUD = Depends(get_spaces_crud),
    heavy_tasks: HeavyTasksHelper = Depends(get_heavy_tasks_helper),
    background_tasks: BackgroundTasks = BackgroundTasks,
):
    service_account_token = await keycloak_manager.get_service_account_token()
    dataset_codes = await dataset_manager.get_all_project_datasets(project_id=project_id)
    dataset_codes = await spaces_crud.retrieve_only_existing_names(dataset_codes)
    background_tasks.add_task(
        heavy_tasks.add_user_task,
        username=username,
        role=role,
        dataset_codes=dataset_codes,
        service_account_token=service_account_token,
    )
    return Response(status_code=204)


@router.delete('/{project_id}/{username}', summary='Remove user from all project datasets')
async def remove_user(
    project_id: UUID,
    username: str,
    role: str = Query(enum=['administrator', 'editor', 'viewer']),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    spaces_crud: SpacesCRUD = Depends(get_spaces_crud),
    heavy_tasks: HeavyTasksHelper = Depends(get_heavy_tasks_helper),
    background_tasks: BackgroundTasks = BackgroundTasks,
):
    service_account_token = await keycloak_manager.get_service_account_token()
    dataset_codes = await dataset_manager.get_all_project_datasets(project_id=project_id)
    dataset_codes = await spaces_crud.retrieve_only_existing_names(dataset_codes)
    background_tasks.add_task(
        heavy_tasks.remove_user_task,
        username=username,
        role=role,
        dataset_codes=dataset_codes,
        service_account_token=service_account_token,
    )
    return Response(status_code=204)


@router.put('/{project_id}/{username}', summary='Update user permissions')
async def update_user(
    project_id: UUID,
    username: str,
    current_role: str = Query(enum=['administrator', 'editor', 'viewer']),
    new_role: str = Query(enum=['administrator', 'editor', 'viewer']),
    keycloak_manager: KeycloakManager = Depends(get_keycloak_manager),
    dataset_manager: DatasetManager = Depends(get_dataset_manager),
    spaces_crud: SpacesCRUD = Depends(get_spaces_crud),
    heavy_tasks: HeavyTasksHelper = Depends(get_heavy_tasks_helper),
    background_tasks: BackgroundTasks = BackgroundTasks,
):
    service_account_token = await keycloak_manager.get_service_account_token()
    dataset_codes = await dataset_manager.get_all_project_datasets(project_id=project_id)
    dataset_codes = await spaces_crud.retrieve_only_existing_names(dataset_codes)
    background_tasks.add_task(
        heavy_tasks.update_user_task,
        username=username,
        current_role=current_role,
        new_role=new_role,
        dataset_codes=dataset_codes,
        service_account_token=service_account_token,
    )
    return Response(status_code=204)
