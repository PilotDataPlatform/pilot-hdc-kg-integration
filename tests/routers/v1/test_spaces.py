# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from datetime import datetime

MYSPACE = {
    'http://schema.org/name': 'myspace',
    'http://schema.org/identifier': 'myspace',
    'https://core.kg.ebrains.eu/vocab/meta/space/autorelease': False,
    'https://core.kg.ebrains.eu/vocab/meta/space/clientSpace': False,
    'https://core.kg.ebrains.eu/vocab/meta/space/deferCache': False,
}

COLLAB_SPACE = {
    'http://schema.org/name': 'collab-hdc-space',
    'http://schema.org/identifier': 'collab-space',
    'https://core.kg.ebrains.eu/vocab/meta/space/autorelease': False,
    'https://core.kg.ebrains.eu/vocab/meta/space/clientSpace': False,
    'https://core.kg.ebrains.eu/vocab/meta/space/deferCache': False,
}

OTHER_SPACE = {
    'http://schema.org/name': 'other',
    'http://schema.org/identifier': 'other',
    'https://core.kg.ebrains.eu/vocab/meta/space/autorelease': False,
    'https://core.kg.ebrains.eu/vocab/meta/space/clientSpace': False,
    'https://core.kg.ebrains.eu/vocab/meta/space/deferCache': False,
}


async def test_list_spaces(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*spaces.*'),
        status_code=200,
        json={
            'data': [MYSPACE, COLLAB_SPACE, OTHER_SPACE],
            'message': None,
            'error': None,
            'startTime': 1675867028544,
            'durationInMs': 49,
            'transactionId': None,
            'total': 0,
            'size': 0,
            'from': 0,
        },
    )
    response = await client.get('/v1/spaces/', params={'token': 'access_token'})

    assert response.status_code == 200
    assert response.json() == {'spaces': [{'name': 'myspace'}, {'name': 'collab-hdc-space'}]}


async def test_list_spaces_no_data(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*spaces.*'),
        status_code=200,
        json={
            'data': [],
            'message': None,
            'error': None,
            'startTime': 1675867028544,
            'durationInMs': 49,
            'transactionId': None,
            'total': 0,
            'size': 0,
            'from': 0,
        },
    )
    response = await client.get('/v1/spaces/', params={'token': 'access_token'})

    assert response.status_code == 200
    assert response.json() == {'spaces': []}


async def test_list_spaces_not_found(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(method='GET', url=re.compile('.*spaces.*'), status_code=404, json={'error': 'Not Found'})
    response = await client.get('/v1/spaces/', params={'token': 'access_token'})

    assert response.status_code == 404
    assert 'Not Found' in response.text


async def test_list_spaces_not_available(client, keycloak_mock, httpx_mock):
    response = await client.get('/v1/spaces/', params={'token': 'access_token'})

    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


async def test_list_spaces_remote_service_error(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='GET', url=re.compile('.*spaces.*'), status_code=500, json={'error': 'test_error_message'}
    )
    response = await client.get('/v1/spaces/', params={'token': 'access_token'})

    assert response.status_code == 500
    assert 'test_error_message' in response.text


async def test_list_spaces_token_exchange_failed(client, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*spaces.*'),
        status_code=200,
        json={
            'data': [MYSPACE, COLLAB_SPACE, OTHER_SPACE],
            'message': None,
            'error': None,
            'startTime': 1675867028544,
            'durationInMs': 49,
            'transactionId': None,
            'total': 0,
            'size': 0,
            'from': 0,
        },
    )
    response = await client.get('/v1/spaces/', params={'token': 'access_token'})

    assert httpx_mock.get_requests()
    httpx_mock.reset(False)
    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


async def test_get_space_details(client, spaces_factory):
    await spaces_factory.create('test', 'tester')
    response = await client.get('/v1/spaces/test')

    space = response.json()

    assert response.status_code == 200
    assert space['name'] == 'test'
    assert space['creator'] == 'tester'


async def test_get_space_details_not_found(client, spaces_factory):
    await spaces_factory.create('test', 'tester')
    response = await client.get('/v1/spaces/not_test')

    assert response.status_code == 404
    assert 'Requested resource is not found' in response.text


async def test_check_multiple_spaces(client, spaces_factory):
    await spaces_factory.create('test', 'tester')
    await spaces_factory.create('test2', 'tester')
    payload = {'spaces': [{'name': 'test'}, {'name': 'test2'}]}
    response = await client.post('/v1/spaces/', json=payload)
    data = response.json()

    assert response.status_code == 200
    assert len(data['spaces']) == 2


async def test_check_multiple_spaces_missing_some(client, spaces_factory):
    await spaces_factory.create('test', 'tester')
    await spaces_factory.create('test2', 'tester')
    payload = {'spaces': [{'name': 'test'}, {'name': 'test2'}, {'name': 'test3'}]}
    response = await client.post('/v1/spaces/', json=payload)
    data = response.json()

    assert response.status_code == 200
    assert len(data['spaces']) == 2


async def test_create_space(client, external_keycloak_mock, httpx_mock):
    httpx_mock.add_response(method='PUT', url=re.compile('.*spaces/collab-hdc-test/specification'), status_code=200)
    response = await client.post('/v1/spaces/create', params={'name': 'test', 'token': 'access_token'})

    space = response.json()
    assert response.status_code == 201
    assert space['name'] == 'test'
    assert space['creator'] == 'service'


async def test_create_duplicate_space(client, spaces_factory, external_keycloak_mock, httpx_mock):
    await spaces_factory.create('test', 'tester')
    httpx_mock.add_response(method='PUT', url=re.compile('.*spaces/collab-hdc-test/specification'), status_code=200)
    response = await client.post('/v1/spaces/create', params={'name': 'test', 'token': 'access_token'})

    assert response.status_code == 400
    assert 'Space was already created' in response.text


async def test_create_space_writes_to_db(client, external_keycloak_mock, httpx_mock):
    httpx_mock.add_response(method='PUT', url=re.compile('.*spaces/collab-hdc-test/specification'), status_code=200)
    response = await client.post('/v1/spaces/create', params={'name': 'test', 'token': 'access_token'})

    space = response.json()
    assert response.status_code == 201
    assert space['name'] == 'test'
    assert space['creator'] == 'service'

    response = await client.get('/v1/spaces/test')

    space = response.json()
    assert response.status_code == 200
    assert space['name'] == 'test'
    assert space['creator'] == 'service'


async def test_create_space_keycloak_not_available(client, httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*/auth/realms/hbp/protocol/openid-connect/token'),
        status_code=503,
        json={'error_message': 'Error'},
    )
    response = await client.post('/v1/spaces/create', params={'name': 'test', 'token': 'access_token'})

    assert response.status_code == 401
    assert 'Could not get the service account token' in response.text


async def test_create_space_for_project(client, keycloak_mock, external_keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*collabs.*'),
        status_code=200,
        json={
            'collabCreationSeafileJob': 'collabCreationSeafileJob/test',
            'collabCreationKeycloakJob': 'collabCreationKeycloakJob/test',
            'collabCreationTemplateJob': 'refactoring/create/1676643909527-329',
            'collabCreationXWikiJob': 'collabCreationXWikiJob/test',
        },
    )
    httpx_mock.add_response(
        method='GET', url=re.compile('.*users/me'), json={'data': {'http://schema.org/alternateName': 'test'}}
    )
    httpx_mock.add_response(method='GET', url=re.compile('.*collabCreationKeycloakJob/test'), status_code=200)
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*admin/roles/users.*'),
        status_code=200,
        json={
            'code': 200,
            'error_msg': '',
            'page': 0,
            'total': 7,
            'num_of_pages': 1,
            'result': [
                {
                    'id': 'f08e5d67-1eb1-424e-a108-7b94f95711fe',
                    'name': 'dandric',
                    'username': 'dandric',
                    'first_name': 'Dusan',
                    'last_name': 'Andric',
                    'email': 'dandric@indocresearch.org',
                    'permission': 'admin',
                    'time_created': '2023-01-19T13:32:37',
                },
                {
                    'id': 'e4cf44bb-f430-418b-bd33-ed30ad2a1a19',
                    'name': 'vmoshynskyi',
                    'username': 'vmoshynskyi',
                    'first_name': 'Vadym',
                    'last_name': 'Moshynskyi',
                    'email': 'vmoshynskyi@indocresearch.org',
                    'permission': 'admin',
                    'time_created': '2023-01-20T04:43:17',
                },
            ],
        },
    )
    httpx_mock.add_response(method='PUT', url=re.compile('.*collabs.*team.*users.*'), status_code=204)
    httpx_mock.add_response(method='PUT', url=re.compile('.*spaces/collab-hdc-test/specification'), status_code=200)
    response = await client.post('/v1/spaces/create/project/test', params={'token': 'access_token'})

    assert response.status_code == 201


async def test_create_space_for_project_pre_existing_collab(client, keycloak_mock, external_keycloak_mock, httpx_mock):
    httpx_mock.add_response(method='POST', url=re.compile('.*collabs.*'), status_code=409)
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*admin/roles/users.*'),
        status_code=200,
        json={
            'code': 200,
            'error_msg': '',
            'page': 0,
            'total': 7,
            'num_of_pages': 1,
            'result': [
                {
                    'id': 'f08e5d67-1eb1-424e-a108-7b94f95711fe',
                    'name': 'dandric',
                    'username': 'dandric',
                    'first_name': 'Dusan',
                    'last_name': 'Andric',
                    'email': 'dandric@indocresearch.org',
                    'permission': 'admin',
                    'time_created': '2023-01-19T13:32:37',
                },
                {
                    'id': 'e4cf44bb-f430-418b-bd33-ed30ad2a1a19',
                    'name': 'vmoshynskyi',
                    'username': 'vmoshynskyi',
                    'first_name': 'Vadym',
                    'last_name': 'Moshynskyi',
                    'email': 'vmoshynskyi@indocresearch.org',
                    'permission': 'admin',
                    'time_created': '2023-01-20T04:43:17',
                },
            ],
        },
    )
    httpx_mock.add_response(
        method='GET', url=re.compile('.*users/me'), json={'data': {'http://schema.org/alternateName': 'test'}}
    )
    httpx_mock.add_response(method='PUT', url=re.compile('.*collabs.*team.*users.*'), status_code=204)
    httpx_mock.add_response(method='PUT', url=re.compile('.*spaces/collab-hdc-test/specification'), status_code=200)
    response = await client.post('/v1/spaces/create/project/test', params={'token': 'access_token'})

    assert response.status_code == 201


async def test_create_space_for_project_fails(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*collabs.*'),
        status_code=200,
        json={
            'collabCreationSeafileJob': 'collabCreationSeafileJob/test',
            'collabCreationKeycloakJob': 'collabCreationKeycloakJob/test',
            'collabCreationTemplateJob': 'refactoring/create/1676643909527-329',
            'collabCreationXWikiJob': 'collabCreationXWikiJob/test',
        },
    )
    httpx_mock.add_response(method='GET', url=re.compile('.*collabCreationKeycloakJob/test'), status_code=200)
    httpx_mock.add_response(
        method='GET', url=re.compile('.*users/me'), json={'data': {'http://schema.org/alternateName': 'test'}}
    )
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*admin/roles/users.*'),
        status_code=200,
        json={
            'code': 200,
            'error_msg': '',
            'page': 0,
            'total': 7,
            'num_of_pages': 1,
            'result': [
                {
                    'id': 'f08e5d67-1eb1-424e-a108-7b94f95711fe',
                    'name': 'dandric',
                    'username': 'dandric',
                    'first_name': 'Dusan',
                    'last_name': 'Andric',
                    'email': 'dandric@indocresearch.org',
                    'permission': 'admin',
                    'time_created': '2023-01-19T13:32:37',
                },
                {
                    'id': 'e4cf44bb-f430-418b-bd33-ed30ad2a1a19',
                    'name': 'vmoshynskyi',
                    'username': 'vmoshynskyi',
                    'first_name': 'Vadym',
                    'last_name': 'Moshynskyi',
                    'email': 'vmoshynskyi@indocresearch.org',
                    'permission': 'admin',
                    'time_created': '2023-01-20T04:43:17',
                },
            ],
        },
    )
    httpx_mock.add_response(method='PUT', url=re.compile('.*collabs.*team.*users.*'), status_code=204)
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*/auth/realms/hbp/protocol/openid-connect/token'),
        status_code=200,
        json={
            'access_token': 'TOKEN',
            'expires_in': 604797,
            'refresh_expires_in': 0,
            'token_type': 'Bearer',
            'id_token': 'TOKEN',
            'not-before-policy': 0,
            'scope': 'openid profile roles email',
        },
    )
    httpx_mock.add_response(
        method='PUT',
        url=re.compile('.*spaces/collab-hdc-test/specification'),
        status_code=503,
        json={'error_message': 'KG is down'},
    )
    start_time = datetime.now()
    response = await client.post('/v1/spaces/create/project/test', params={'token': 'access_token'})
    finish_time = datetime.now()
    time_diff = finish_time - start_time

    assert response.status_code == 500
    assert 'KG is down' in response.text
    # backoff should retry 4 times: 1 sec, 1 sec, 2 sec, 3 sec = 7+ sec for test
    assert time_diff.total_seconds() > 7


async def test_create_space_for_dataset(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*collabs.*'),
        status_code=200,
        json={
            'collabCreationSeafileJob': 'collabCreationSeafileJob/test',
            'collabCreationKeycloakJob': 'collabCreationKeycloakJob/test',
            'collabCreationTemplateJob': 'refactoring/create/1676643909527-329',
            'collabCreationXWikiJob': 'collabCreationXWikiJob/test',
        },
    )
    httpx_mock.add_response(
        method='GET', url=re.compile('.*users/me'), json={'data': {'http://schema.org/alternateName': 'test'}}
    )
    httpx_mock.add_response(method='GET', url=re.compile('.*collabCreationKeycloakJob/test'), status_code=200)
    httpx_mock.add_response(
        method='GET', url=re.compile('.*datasets/test'), status_code=200, json={'project_id': 'project_test'}
    )
    httpx_mock.add_response(
        method='GET', url=re.compile('.*projects/project_test'), status_code=200, json={'project_code': 'code_test'}
    )
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*admin/roles/users.*'),
        status_code=200,
        json={
            'code': 200,
            'error_msg': '',
            'page': 0,
            'total': 7,
            'num_of_pages': 1,
            'result': [
                {
                    'id': 'f08e5d67-1eb1-424e-a108-7b94f95711fe',
                    'name': 'dandric',
                    'username': 'dandric',
                    'first_name': 'Dusan',
                    'last_name': 'Andric',
                    'email': 'dandric@indocresearch.org',
                    'permission': 'admin',
                    'time_created': '2023-01-19T13:32:37',
                },
                {
                    'id': 'e4cf44bb-f430-418b-bd33-ed30ad2a1a19',
                    'name': 'vmoshynskyi',
                    'username': 'vmoshynskyi',
                    'first_name': 'Vadym',
                    'last_name': 'Moshynskyi',
                    'email': 'vmoshynskyi@indocresearch.org',
                    'permission': 'admin',
                    'time_created': '2023-01-20T04:43:17',
                },
            ],
        },
    )
    httpx_mock.add_response(method='PUT', url=re.compile('.*collabs.*team.*users.*'), status_code=204)
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*/auth/realms/hbp/protocol/openid-connect/token'),
        status_code=200,
        json={
            'access_token': 'TOKEN',
            'expires_in': 604797,
            'refresh_expires_in': 0,
            'token_type': 'Bearer',
            'id_token': 'TOKEN',
            'not-before-policy': 0,
            'scope': 'openid profile roles email',
        },
    )
    httpx_mock.add_response(method='PUT', url=re.compile('.*spaces/collab-hdc-test/specification'), status_code=200)
    response = await client.post('/v1/spaces/create/dataset/test', params={'token': 'access_token'})

    assert response.status_code == 201


async def test_create_duplicate_space_for_dataset(client, spaces_factory):
    await spaces_factory.create('test', 'tester')
    response = await client.post('/v1/spaces/create/dataset/test', params={'token': 'access_token'})

    assert response.status_code == 400
    assert 'Space was already created' in response.text


async def test_create_duplicate_space_for_project(client, spaces_factory):
    await spaces_factory.create('test', 'tester')
    response = await client.post('/v1/spaces/create/project/test', params={'token': 'access_token'})

    assert response.status_code == 400
    assert 'Space was already created' in response.text
