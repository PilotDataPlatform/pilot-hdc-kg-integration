# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_get_user_list(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*collabs/.*/team/.*'),
        status_code=200,
        json={
            'users': [
                {
                    'id': '580597af-7928-4b69-a547-3ebfb9f1b010',
                    'mitreId': '5089721700637136',
                    'username': 'vmoshynskyi',
                    'firstName': 'Vadym',
                    'lastName': 'Moshynskyi',
                    'biography': '',
                    'avatar': '',
                    'active': True,
                }
            ],
            'units': [],
            'groups': [],
        },
    )

    response = await client.get('/v1/users/collab-test', params={'role': 'administrator', 'token': 'access_token'})

    assert response.status_code == 200
    assert '580597af-7928-4b69-a547-3ebfb9f1b010' in response.text


@pytest.mark.asyncio
async def test_get_user_list_not_available(client, keycloak_mock, httpx_mock):
    response = await client.get('/v1/users/collab-test', params={'role': 'administrator', 'token': 'access_token'})

    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


@pytest.mark.asyncio
async def test_get_user_list_remote_service_error(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*collabs/.*/team/.*'),
        status_code=500,
        json={'error': 'test_error_message'},
    )

    response = await client.get('/v1/users/collab-test', params={'role': 'administrator', 'token': 'access_token'})

    assert response.status_code == 500
    assert 'test_error_message' in response.text


@pytest.mark.asyncio
async def test_get_user_list_token_exchange_failed(client, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*collabs/.*/team/.*'),
        status_code=200,
        json={
            'users': [
                {
                    'id': '580597af-7928-4b69-a547-3ebfb9f1b010',
                    'mitreId': '5089721700637136',
                    'username': 'vmoshynskyi',
                    'firstName': 'Vadym',
                    'lastName': 'Moshynskyi',
                    'biography': '',
                    'avatar': '',
                    'active': True,
                }
            ],
            'units': [],
            'groups': [],
        },
    )

    response = await client.get('/v1/users/collab-test', params={'role': 'administrator', 'token': 'access_token'})

    assert httpx_mock.get_requests()
    httpx_mock.reset(False)
    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


@pytest.mark.asyncio
async def test_invite_user(client, external_keycloak_mock, httpx_mock, spaces_factory):
    project_id = uuid4()
    await spaces_factory.create('dataset_test1', 'tester')
    await spaces_factory.create('dataset_test2', 'tester')
    await spaces_factory.create('dataset_test3', 'tester')
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets.*project_id.*'),
        status_code=200,
        json={'result': [{'code': 'dataset_test1'}, {'code': 'dataset_test2'}, {'code': 'dataset_test3'}]},
    )
    httpx_mock.add_response(method='PUT', url=re.compile('.*collabs.*team.*users.*'), status_code=204)

    response = await client.post(
        f'/v1/users/{project_id}/test', params={'role': 'administrator', 'token': 'access_token'}
    )

    assert response.status_code == 204
    assert len(httpx_mock.get_requests(method='PUT', url=re.compile('.*wiki.ebrains.eu/rest/v1/collabs.*'))) == 3


@pytest.mark.asyncio
async def test_invite_user_not_all_spaces_are_created(client, external_keycloak_mock, httpx_mock, spaces_factory):
    project_id = uuid4()
    await spaces_factory.create('dataset_test1', 'tester')
    await spaces_factory.create('dataset_test2', 'tester')
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets.*project_id.*'),
        status_code=200,
        json={'result': [{'code': 'dataset_test1'}, {'code': 'dataset_test2'}, {'code': 'dataset_test3'}]},
    )
    httpx_mock.add_response(method='PUT', url=re.compile('.*collabs.*team.*users.*'), status_code=204)

    response = await client.post(
        f'/v1/users/{project_id}/test', params={'role': 'administrator', 'token': 'access_token'}
    )

    assert response.status_code == 204
    assert len(httpx_mock.get_requests(method='PUT', url=re.compile('.*wiki.ebrains.eu/rest/v1/collabs.*'))) == 2


@pytest.mark.asyncio
async def test_invite_user_remote_service_error(client, external_keycloak_mock, httpx_mock, spaces_factory):
    project_id = uuid4()
    await spaces_factory.create('dataset_test1', 'tester')
    await spaces_factory.create('dataset_test2', 'tester')
    await spaces_factory.create('dataset_test3', 'tester')
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets.*project_id.*'),
        status_code=200,
        json={'result': [{'code': 'dataset_test1'}, {'code': 'dataset_test2'}, {'code': 'dataset_test3'}]},
    )
    httpx_mock.add_response(
        method='PUT', url=re.compile('.*collabs.*team.*users.*'), status_code=500, json={'error': 'test_error_message'}
    )

    response = await client.post(
        f'/v1/users/{project_id}/test', params={'role': 'administrator', 'token': 'access_token'}
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_remove_user(client, external_keycloak_mock, httpx_mock, spaces_factory):
    project_id = uuid4()
    await spaces_factory.create('dataset_test1', 'tester')
    await spaces_factory.create('dataset_test2', 'tester')
    await spaces_factory.create('dataset_test3', 'tester')
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets.*project_id.*'),
        status_code=200,
        json={'result': [{'code': 'dataset_test1'}, {'code': 'dataset_test2'}, {'code': 'dataset_test3'}]},
    )
    httpx_mock.add_response(method='DELETE', url=re.compile('.*collabs.*team.*users.*'), status_code=204)

    response = await client.delete(
        f'/v1/users/{project_id}/test', params={'role': 'administrator', 'token': 'access_token'}
    )

    assert response.status_code == 204
    assert len(httpx_mock.get_requests(method='DELETE', url=re.compile('.*wiki.ebrains.eu/rest/v1/collabs.*'))) == 3


@pytest.mark.asyncio
async def test_remove_user_not_all_spaces_are_created(client, external_keycloak_mock, httpx_mock, spaces_factory):
    project_id = uuid4()
    await spaces_factory.create('dataset_test1', 'tester')
    await spaces_factory.create('dataset_test2', 'tester')
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets.*project_id.*'),
        status_code=200,
        json={'result': [{'code': 'dataset_test1'}, {'code': 'dataset_test2'}, {'code': 'dataset_test3'}]},
    )
    httpx_mock.add_response(method='DELETE', url=re.compile('.*collabs.*team.*users.*'), status_code=204)

    response = await client.delete(
        f'/v1/users/{project_id}/test', params={'role': 'administrator', 'token': 'access_token'}
    )

    assert response.status_code == 204
    assert len(httpx_mock.get_requests(method='DELETE', url=re.compile('.*wiki.ebrains.eu/rest/v1/collabs.*'))) == 2


@pytest.mark.asyncio
async def test_remove_user_remote_service_error(client, external_keycloak_mock, httpx_mock, spaces_factory):
    project_id = uuid4()
    await spaces_factory.create('dataset_test1', 'tester')
    await spaces_factory.create('dataset_test2', 'tester')
    await spaces_factory.create('dataset_test3', 'tester')
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets.*project_id.*'),
        status_code=200,
        json={'result': [{'code': 'dataset_test1'}, {'code': 'dataset_test2'}, {'code': 'dataset_test3'}]},
    )
    httpx_mock.add_response(
        method='DELETE',
        url=re.compile('.*collabs.*team.*users.*'),
        status_code=500,
        json={'error': 'test_error_message'},
    )

    response = await client.delete(
        f'/v1/users/{project_id}/test', params={'role': 'administrator', 'token': 'access_token'}
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_update_user(client, external_keycloak_mock, httpx_mock, spaces_factory):
    project_id = str(uuid4())
    await spaces_factory.create('dataset_test1', 'tester')
    await spaces_factory.create('dataset_test2', 'tester')
    await spaces_factory.create('dataset_test3', 'tester')
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets.*project_id.*'),
        status_code=200,
        json={'result': [{'code': 'dataset_test1'}, {'code': 'dataset_test2'}, {'code': 'dataset_test3'}]},
    )
    httpx_mock.add_response(method='PUT', url=re.compile('.*collabs.*team.*users.*'), status_code=204)
    httpx_mock.add_response(method='DELETE', url=re.compile('.*collabs.*team.*users.*'), status_code=204)

    response = await client.put(
        f'/v1/users/{project_id}/test',
        params={'current_role': 'administrator', 'new_role': 'editor', 'token': 'access_token'},
    )

    assert response.status_code == 204
    assert len(httpx_mock.get_requests(method='PUT', url=re.compile('.*wiki.ebrains.eu/rest/v1/collabs.*'))) == 3
    assert len(httpx_mock.get_requests(method='DELETE', url=re.compile('.*wiki.ebrains.eu/rest/v1/collabs.*'))) == 3


@pytest.mark.asyncio
async def test_update_user_not_all_spaces_are_created(client, external_keycloak_mock, httpx_mock, spaces_factory):
    project_id = str(uuid4())
    await spaces_factory.create('dataset_test1', 'tester')
    await spaces_factory.create('dataset_test2', 'tester')
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets.*project_id.*'),
        status_code=200,
        json={'result': [{'code': 'dataset_test1'}, {'code': 'dataset_test2'}, {'code': 'dataset_test3'}]},
    )
    httpx_mock.add_response(method='PUT', url=re.compile('.*collabs.*team.*users.*'), status_code=204)
    httpx_mock.add_response(method='DELETE', url=re.compile('.*collabs.*team.*users.*'), status_code=204)

    response = await client.put(
        f'/v1/users/{project_id}/test',
        params={'current_role': 'administrator', 'new_role': 'editor', 'token': 'access_token'},
    )

    assert response.status_code == 204
    assert len(httpx_mock.get_requests(method='PUT', url=re.compile('.*wiki.ebrains.eu/rest/v1/collabs.*'))) == 2
    assert len(httpx_mock.get_requests(method='DELETE', url=re.compile('.*wiki.ebrains.eu/rest/v1/collabs.*'))) == 2
