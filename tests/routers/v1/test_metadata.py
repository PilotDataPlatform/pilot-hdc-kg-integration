# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from uuid import uuid4

import pytest

PERSON_METADATA_1 = {
    'http://schema.org/name': 'Matvey',
    '@type': ['https://openminds.ebrains.eu/core/person'],
    'https://core.kg.ebrains.eu/vocab/meta/space': 'myspace',
    'http://schema.org/surname': 'Loshakov',
    'https://core.kg.ebrains.eu/vocab/meta/user': {
        '@id': 'https://kg.ebrains.eu/api/instances/0d3137ad-ff53-46dc-b68e-b781edc3e37b'
    },
    '@id': 'https://kg.ebrains.eu/api/instances/9bd75916-4dce-49f6-a70b-878cc7f36cf7',
    'https://core.kg.ebrains.eu/vocab/meta/revision': 'rev',
    'http://schema.org/identifier': ['https://kg.ebrains.eu/api/instances/9bd75916-4dce-49f6-a70b-878cc7f36cf7'],
}
PERSON_METADATA_2 = {
    'http://schema.org/name': 'Also Matvey',
    '@type': ['https://openminds.ebrains.eu/core/person'],
    'https://core.kg.ebrains.eu/vocab/meta/space': 'myspace',
    'http://schema.org/surname': 'Loshakov Again',
    'https://core.kg.ebrains.eu/vocab/meta/user': {
        '@id': 'https://kg.ebrains.eu/api/instances/0d3137ad-ff53-46dc-b68e-b781edc3e37b'
    },
    '@id': 'https://kg.ebrains.eu/api/instances/b5817f36-da1e-44a2-81ed-3d769450eb65',
    'https://core.kg.ebrains.eu/vocab/meta/revision': 'rev',
    'http://schema.org/identifier': ['https://kg.ebrains.eu/api/instances/b5817f36-da1e-44a2-81ed-3d769450eb65'],
}


@pytest.mark.asyncio
async def test_list_metadata(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*instances.*space=myspace.*type=person.*'),
        status_code=200,
        json={
            'data': [PERSON_METADATA_1, PERSON_METADATA_2],
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
    response = await client.get(
        '/v1/metadata/',
        params={'space': 'myspace', 'stage': 'IN_PROGRESS', 'type': 'person', 'token': 'access_token'},
    )
    assert response.status_code == 200
    assert response.json() == {
        'result': [
            {
                'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
                'data': {'http://schema.org/name': 'Matvey', 'http://schema.org/surname': 'Loshakov'},
                'id': '9bd75916-4dce-49f6-a70b-878cc7f36cf7',
                'revision': 'rev',
                'space': 'myspace',
                'type': ['https://openminds.ebrains.eu/core/person'],
            },
            {
                'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
                'data': {'http://schema.org/name': 'Also Matvey', 'http://schema.org/surname': 'Loshakov Again'},
                'id': 'b5817f36-da1e-44a2-81ed-3d769450eb65',
                'revision': 'rev',
                'space': 'myspace',
                'type': ['https://openminds.ebrains.eu/core/person'],
            },
        ]
    }


@pytest.mark.asyncio
async def test_list_metadata_not_found(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*instances.*space=myspace.*type=person.*'),
        status_code=404,
        json={'error': 'Not Found'},
    )
    response = await client.get(
        '/v1/metadata/',
        params={'space': 'myspace', 'stage': 'IN_PROGRESS', 'type': 'person', 'token': 'access_token'},
    )
    assert response.status_code == 404
    assert 'Not Found' in response.text


@pytest.mark.asyncio
async def test_list_metadata_remote_service_error(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*instances.*space=myspace.*type=person.*'),
        status_code=500,
        json={'error': 'test_error_message'},
    )
    response = await client.get(
        '/v1/metadata/',
        params={'space': 'myspace', 'stage': 'IN_PROGRESS', 'type': 'person', 'token': 'access_token'},
    )
    assert response.status_code == 500
    assert 'test_error_message' in response.text


@pytest.mark.asyncio
async def test_list_metadata_not_available(client, keycloak_mock, httpx_mock):
    response = await client.get(
        '/v1/metadata/',
        params={'space': 'myspace', 'stage': 'IN_PROGRESS', 'type': 'person', 'token': 'access_token'},
    )
    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


@pytest.mark.asyncio
async def test_list_metadata_no_data(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*instances.*space=collab-hdc-persons.*type=person.*'),
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
    response = await client.get(
        '/v1/metadata/',
        params={'space': 'persons', 'stage': 'IN_PROGRESS', 'type': 'person', 'token': 'access_token'},
    )
    assert response.status_code == 200
    assert response.json() == {'result': []}


@pytest.mark.asyncio
async def test_list_metadata_token_exchange_failed(client, httpx_mock):
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*instances.*space=myspace.*type=person.*'),
        status_code=200,
        json={
            'data': [PERSON_METADATA_1, PERSON_METADATA_2],
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
    response = await client.get(
        '/v1/metadata/', params={'space': 'persons', 'stage': 'IN_PROGRESS', 'type': 'person', 'token': 'access_token'}
    )

    assert httpx_mock.get_requests()
    httpx_mock.reset(False)
    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


@pytest.mark.asyncio
async def test_get_metadata_by_id(client, metadata_factory):
    metadata_id = uuid4()
    kg_integration_id = uuid4()
    await metadata_factory.create(metadata_id, kg_integration_id)
    response = await client.get(f'/v1/metadata/{metadata_id}')
    assert response.status_code == 200
    assert str(metadata_id) == response.json()['metadata_id']


@pytest.mark.asyncio
async def test_get_metadata_by_id_not_found(client):
    response = await client.get('/v1/metadata/11111111-2222-3333-4444-555555555555')
    assert response.status_code == 404
    assert 'Requested resource is not found' in response.text


@pytest.mark.asyncio
async def test_upload_metadata(client, keycloak_mock, httpx_mock, metadata_factory):
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*instances.*'),
        status_code=200,
        json={
            'data': PERSON_METADATA_1,
            'message': None,
            'error': None,
            'startTime': 1676042794406,
            'durationInMs': 218,
            'transactionId': None,
        },
    )
    response = await client.post(
        '/v1/metadata/upload',
        params={'space': 'myspace', 'metadata_id': str(uuid4()), 'token': 'access_token'},
        json={
            '@type': 'https://openminds.ebrains.eu/core/testing',
            'http://schema.org/name': 'Matvey',
            'http://schema.org/surname': 'Loshakov',
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
        'data': {'http://schema.org/name': 'Matvey', 'http://schema.org/surname': 'Loshakov'},
        'id': '9bd75916-4dce-49f6-a70b-878cc7f36cf7',
        'revision': 'rev',
        'space': 'myspace',
        'type': ['https://openminds.ebrains.eu/core/person'],
    }


@pytest.mark.asyncio
async def test_upload_metadata_not_available(client, keycloak_mock, httpx_mock):
    response = await client.post(
        '/v1/metadata/upload',
        params={'space': 'myspace', 'metadata_id': str(uuid4()), 'token': 'access_token'},
        json={
            '@type': 'https://openminds.ebrains.eu/core/testing',
            'http://schema.org/name': 'Matvey',
            'http://schema.org/surname': 'Loshakov',
        },
    )
    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


@pytest.mark.asyncio
async def test_upload_metadata_creates_db_entry(client, keycloak_mock, httpx_mock, metadata_factory):
    metadata_id = str(uuid4())
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*instances.*'),
        status_code=200,
        json={
            'data': PERSON_METADATA_1,
            'message': None,
            'error': None,
            'startTime': 1676042794406,
            'durationInMs': 218,
            'transactionId': None,
        },
    )
    response = await client.post(
        '/v1/metadata/upload',
        params={'space': 'myspace', 'metadata_id': metadata_id, 'token': 'access_token'},
        json={
            '@type': 'https://openminds.ebrains.eu/core/testing',
            'http://schema.org/name': 'Matvey',
            'http://schema.org/surname': 'Loshakov',
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
        'data': {'http://schema.org/name': 'Matvey', 'http://schema.org/surname': 'Loshakov'},
        'id': '9bd75916-4dce-49f6-a70b-878cc7f36cf7',
        'revision': 'rev',
        'space': 'myspace',
        'type': ['https://openminds.ebrains.eu/core/person'],
    }

    response = await client.get(f'/v1/metadata/{metadata_id}')
    assert response.status_code == 200
    assert metadata_id == response.json()['metadata_id']


@pytest.mark.asyncio
async def test_update_metadata(client, keycloak_mock, httpx_mock, metadata_factory):
    metadata_id = str(uuid4())
    kg_instance_id = '9bd75916-4dce-49f6-a70b-878cc7f36cf7'
    await metadata_factory.create(metadata_id=metadata_id, kg_instance_id=kg_instance_id)
    httpx_mock.add_response(
        method='PUT',
        url=re.compile('.*instances.*9bd75916-4dce-49f6-a70b-878cc7f36cf7.*'),
        status_code=200,
        json={
            'data': PERSON_METADATA_1,
            'message': None,
            'error': None,
            'startTime': 1676042794406,
            'durationInMs': 218,
            'transactionId': None,
        },
    )
    response = await client.put(
        f'/v1/metadata/update/{metadata_id}',
        params={'space': 'myspace', 'token': 'access_token'},
        json={
            '@type': 'https://openminds.ebrains.eu/core/testing',
            'http://schema.org/name': 'Matvey',
            'http://schema.org/surname': 'Loshakov',
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
        'data': {'http://schema.org/name': 'Matvey', 'http://schema.org/surname': 'Loshakov'},
        'id': '9bd75916-4dce-49f6-a70b-878cc7f36cf7',
        'revision': 'rev',
        'space': 'myspace',
        'type': ['https://openminds.ebrains.eu/core/person'],
    }


@pytest.mark.asyncio
async def test_update_metadata_does_not_exist(client, keycloak_mock, httpx_mock):
    metadata_id = str(uuid4())
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*instances.*'),
        status_code=200,
        json={
            'data': PERSON_METADATA_1,
            'message': None,
            'error': None,
            'startTime': 1676042794406,
            'durationInMs': 218,
            'transactionId': None,
        },
    )
    response = await client.put(
        f'/v1/metadata/update/{metadata_id}',
        params={'space': 'myspace', 'token': 'access_token'},
        json={
            '@type': 'https://openminds.ebrains.eu/core/testing',
            'http://schema.org/name': 'Matvey',
            'http://schema.org/surname': 'Loshakov',
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        'creator': '0d3137ad-ff53-46dc-b68e-b781edc3e37b',
        'data': {'http://schema.org/name': 'Matvey', 'http://schema.org/surname': 'Loshakov'},
        'id': '9bd75916-4dce-49f6-a70b-878cc7f36cf7',
        'revision': 'rev',
        'space': 'myspace',
        'type': ['https://openminds.ebrains.eu/core/person'],
    }

    response = await client.get(f'/v1/metadata/{metadata_id}')
    assert response.status_code == 200
    assert metadata_id == response.json()['metadata_id']


@pytest.mark.asyncio
async def test_delete_metadata(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='DELETE',
        url=re.compile('.*instances.*b5817f36-da1e-44a2-81ed-3d769450eb65.*'),
        status_code=200,
    )
    response = await client.delete(
        '/v1/metadata/b5817f36-da1e-44a2-81ed-3d769450eb65',
        params={'token': 'access_token'},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_metadata_not_available(client, keycloak_mock, httpx_mock):
    response = await client.delete(
        '/v1/metadata/b5817f36-da1e-44a2-81ed-3d769450eb65',
        params={'token': 'access_token'},
    )
    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


@pytest.mark.asyncio
async def test_delete_metadata_remote_service_error(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='DELETE',
        url=re.compile('.*instances.*b5817f36-da1e-44a2-81ed-3d769450eb65.*'),
        status_code=500,
        json={'error': 'test_error_message'},
    )
    response = await client.delete(
        '/v1/metadata/b5817f36-da1e-44a2-81ed-3d769450eb65',
        params={'token': 'access_token'},
    )
    assert response.status_code == 500
    assert 'test_error_message' in response.text
