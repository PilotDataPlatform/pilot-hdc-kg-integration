# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from unittest import mock
from uuid import uuid4

from kg_integration.utils.spaces_activity_log import KGActivityLog

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


async def test_get_metadata_by_id(client, keycloak_mock, httpx_mock):
    metadata_id = uuid4()
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*instances/.*'),
        json={'data': PERSON_METADATA_1},
    )
    response = await client.get(f'/v1/metadata/{metadata_id}', params={'token': 'access_token'})

    assert response.status_code == 200
    assert response.json() == PERSON_METADATA_1


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


async def test_list_metadata_not_available(client, keycloak_mock, httpx_mock):
    response = await client.get(
        '/v1/metadata/',
        params={'space': 'myspace', 'stage': 'IN_PROGRESS', 'type': 'person', 'token': 'access_token'},
    )
    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


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


async def test_check_metadata_list(client, metadata_factory):
    metadata_id = str(uuid4())
    dataset_id = str(uuid4())
    kg_instance_id = str(uuid4())
    await metadata_factory.create(
        metadata_id=metadata_id, kg_instance_id=kg_instance_id, dataset_id=dataset_id, direction='KG'
    )
    response = await client.post(
        '/v1/metadata/',
        json={
            'metadata': [{'id': metadata_id}],
        },
    )
    assert response.status_code == 200
    assert kg_instance_id in response.text


async def test_check_metadata_list_not_found(client, metadata_factory):
    metadata_id = str(uuid4())
    response = await client.post(
        '/v1/metadata/',
        json={
            'metadata': [{'id': metadata_id}],
        },
    )
    assert response.status_code == 404


@mock.patch.object(KGActivityLog, 'send_metadata_on_upload_event')
async def test_upload_metadata(mock_activity_log, client, keycloak_mock, httpx_mock, metadata_factory):
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
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets/.*'),
        status_code=200,
        json={
            'code': 'test',
        },
    )
    response = await client.post(
        '/v1/metadata/upload',
        params={
            'space': 'myspace',
            'metadata_id': str(uuid4()),
            'dataset_id': str(uuid4()),
            'uploader': 'test',
            'token': 'access_token',
        },
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
    mock_activity_log.assert_called_once_with(dataset_code='test', creator='test')


async def test_upload_metadata_not_available(client, keycloak_mock, httpx_mock):
    response = await client.post(
        '/v1/metadata/upload',
        params={
            'space': 'myspace',
            'metadata_id': str(uuid4()),
            'dataset_id': str(uuid4()),
            'uploader': 'test',
            'token': 'access_token',
        },
        json={
            '@type': 'https://openminds.ebrains.eu/core/testing',
            'http://schema.org/name': 'Matvey',
            'http://schema.org/surname': 'Loshakov',
        },
    )
    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


@mock.patch.object(KGActivityLog, 'send_metadata_on_upload_event')
async def test_upload_metadata_creates_db_entry(mock_activity_log, client, keycloak_mock, httpx_mock, metadata_factory):
    metadata_id = str(uuid4())
    dataset_id = str(uuid4())
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
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets/.*'),
        status_code=200,
        json={
            'code': 'test',
        },
    )
    response = await client.post(
        '/v1/metadata/upload',
        params={
            'space': 'myspace',
            'metadata_id': metadata_id,
            'dataset_id': dataset_id,
            'uploader': 'test',
            'token': 'access_token',
        },
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
    mock_activity_log.assert_called_once_with(dataset_code='test', creator='test')


async def test_update_metadata(client, keycloak_mock, httpx_mock, metadata_factory):
    metadata_id = str(uuid4())
    dataset_id = str(uuid4())
    kg_instance_id = '9bd75916-4dce-49f6-a70b-878cc7f36cf7'
    await metadata_factory.create(
        metadata_id=metadata_id, kg_instance_id=kg_instance_id, dataset_id=dataset_id, direction='KG'
    )
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
        params={
            'space': 'myspace',
            'token': 'access_token',
            'uploader': 'test',
            'filename': 'test.jsonld',
            'dataset_id': dataset_id,
        },
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


@mock.patch.object(KGActivityLog, 'send_metadata_on_upload_event')
async def test_update_metadata_does_not_exist(mock_activity_log, client, keycloak_mock, httpx_mock):
    metadata_id = str(uuid4())
    dataset_id = str(uuid4())
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
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets/.*'),
        status_code=200,
        json={
            'code': 'test',
        },
    )
    response = await client.put(
        f'/v1/metadata/update/{metadata_id}',
        params={
            'space': 'myspace',
            'token': 'access_token',
            'uploader': 'test',
            'filename': 'test.jsonld',
            'dataset_id': dataset_id,
        },
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
    mock_activity_log.assert_called_once_with(dataset_code='test', target_name='test.jsonld', creator='test')


@mock.patch.object(KGActivityLog, 'send_metadata_on_upload_event')
async def test_bulk_update_metadata(mock_activity_log, client, keycloak_mock, httpx_mock, metadata_factory):
    dataset_id = 'ffbac5e0-f135-4057-a7bf-4bda9cdf77d8'
    kg_instance_id_1 = '9bd75916-4dce-49f6-a70b-878cc7f36cf7'
    kg_instance_id_2 = '3ccfd11b-8d4d-46b2-8564-5674354f553a'
    await metadata_factory.create(
        metadata_id='bfb392a8-65e8-4a83-91fb-f872f63b19fa',
        kg_instance_id=kg_instance_id_1,
        dataset_id=dataset_id,
        direction='KG',
    )
    await metadata_factory.create(
        metadata_id='357d4665-cbb7-443b-a4a7-03f38ae056b6',
        kg_instance_id=kg_instance_id_2,
        dataset_id=dataset_id,
        direction='KG',
    )
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*schema/list.*'),
        status_code=200,
        json={
            'result': [
                {
                    'geid': 'bfb392a8-65e8-4a83-91fb-f872f63b19fa',
                    'name': 'essential.schema.json',
                    'dataset_geid': 'ffbac5e0-f135-4057-a7bf-4bda9cdf77d8',
                    'tpl_geid': 'bfb392a8-65e8-4a83-91fb-f872f63b19fa',
                    'standard': 'open_minds',
                    'system_defined': False,
                    'is_draft': False,
                    'creator': 'mloshakov',
                    'content': PERSON_METADATA_1,
                    'create_timestamp': '2025-02-04T09:45:15',
                    'update_timestamp': '2025-02-04T09:45:15',
                },
                {
                    'geid': '357d4665-cbb7-443b-a4a7-03f38ae056b6',
                    'name': 'me_new_no_id.jsonld',
                    'dataset_geid': 'ffbac5e0-f135-4057-a7bf-4bda9cdf77d8',
                    'tpl_geid': '79de7000-70dd-4086-9bc7-e255e08fed69',
                    'standard': 'open_minds',
                    'system_defined': False,
                    'is_draft': False,
                    'creator': 'mloshakov',
                    'content': PERSON_METADATA_2,
                    'create_timestamp': '2025-02-04T09:47:03',
                    'update_timestamp': '2025-02-04T09:47:03',
                },
            ]
        },
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets/ffbac5e0-f135-4057-a7bf-4bda9cdf77d.*'),
        status_code=200,
        json={'code': 'test'},
    )
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
    httpx_mock.add_response(
        method='PUT',
        url=re.compile('.*instances.*3ccfd11b-8d4d-46b2-8564-5674354f553a.*'),
        status_code=200,
        json={
            'data': PERSON_METADATA_2,
            'message': None,
            'error': None,
            'startTime': 1676042794406,
            'durationInMs': 218,
            'transactionId': None,
        },
    )
    response = await client.put(
        f'/v1/metadata/update/dataset/{dataset_id}',
        params={
            'token': 'access_token',
            'username': 'test',
        },
    )
    assert response.status_code == 200
    mock_activity_log.has_calls(
        mock.call(dataset_code='test', target_name='357d4665-cbb7-443b-a4a7-03f38ae056b6', creator='test')
    )


@mock.patch.object(KGActivityLog, 'send_metadata_on_delete_event')
async def test_delete_metadata(mock_activity_log, client, keycloak_mock, httpx_mock, metadata_factory):
    metadata_id = str(uuid4())
    dataset_id = str(uuid4())
    kg_instance_id = '9bd75916-4dce-49f6-a70b-878cc7f36cf7'
    await metadata_factory.create(
        metadata_id=metadata_id, kg_instance_id=kg_instance_id, dataset_id=dataset_id, direction='KG'
    )
    httpx_mock.add_response(
        method='DELETE',
        url=re.compile('.*instances.*9bd75916-4dce-49f6-a70b-878cc7f36cf7.*'),
        status_code=200,
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets/.*'),
        status_code=200,
        json={
            'code': 'test',
        },
    )
    response = await client.delete(
        f'/v1/metadata/{kg_instance_id}',
        params={'username': 'test', 'token': 'access_token'},
    )
    assert response.status_code == 204
    mock_activity_log.assert_called_once_with(
        dataset_code='test', target_name='9bd75916-4dce-49f6-a70b-878cc7f36cf7', creator='test'
    )


async def test_delete_metadata_not_available(client, keycloak_mock, httpx_mock):
    response = await client.delete(
        '/v1/metadata/b5817f36-da1e-44a2-81ed-3d769450eb65',
        params={'username': 'test', 'token': 'access_token'},
    )
    assert response.status_code == 503
    assert 'Remote resource is not available' in response.text


async def test_delete_metadata_remote_service_error(client, keycloak_mock, httpx_mock):
    httpx_mock.add_response(
        method='DELETE',
        url=re.compile('.*instances.*b5817f36-da1e-44a2-81ed-3d769450eb65.*'),
        status_code=500,
        json={'error': 'test_error_message'},
    )
    response = await client.delete(
        '/v1/metadata/b5817f36-da1e-44a2-81ed-3d769450eb65',
        params={'username': 'test', 'token': 'access_token'},
    )
    assert response.status_code == 500
    assert 'test_error_message' in response.text


@mock.patch.object(KGActivityLog, 'send_metadata_on_download_event')
async def test_download_metadata_from_kg(mock_activity_log, client, keycloak_mock, httpx_mock):
    kg_id = '9bd75916-4dce-49f6-a70b-878cc7f36cf7'
    dataset_id = str(uuid4())
    template_id = str(uuid4())
    username = 'test'
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*dataset/default/schemaTPL/list.*'),
        status_code=200,
        json={'result': [{'name': 'Open_minds', 'geid': template_id}]},
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets/.*'),
        status_code=200,
        json={
            'code': 'test',
        },
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*release/status.*'),
        status_code=200,
        json={
            'data': 'UNRELEASED',
            'message': None,
            'error': None,
            'startTime': None,
            'durationInMs': None,
            'transactionId': None,
        },
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*instances/9bd75916-4dce-49f6-a70b-878cc7f36cf7.*stage=IN_PROGRESS.*'),
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
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*schema$'),
        match_json={
            'name': kg_id + '.jsonld',
            'dataset_geid': dataset_id,
            'tpl_geid': template_id,
            'standard': 'open_minds',
            'system_defined': False,
            'is_draft': False,
            'content': PERSON_METADATA_1,
            'creator': username,
        },
        status_code=200,
        json={
            'result': {
                'geid': '2e9d768f-5c38-48e0-9436-c97199769ca9',
                'name': kg_id + '.jsonld',
                'dataset_geid': dataset_id,
                'tpl_geid': template_id,
                'standard': 'open_minds',
                'system_defined': False,
                'is_draft': False,
                'creator': username,
                'content': PERSON_METADATA_1,
                'create_timestamp': '2024-09-04T08:08:53',
                'update_timestamp': '2024-09-04T08:08:53',
            }
        },
    )
    response = await client.get(
        f'/v1/metadata/upload/{kg_id}/{dataset_id}',
        params={'token': 'access_token', 'uploader': username},
    )
    assert response.status_code == 200
    assert response.json() == {
        'geid': '2e9d768f-5c38-48e0-9436-c97199769ca9',
        'name': kg_id + '.jsonld',
        'dataset_geid': dataset_id,
        'tpl_geid': template_id,
        'standard': 'open_minds',
        'system_defined': False,
        'is_draft': False,
        'creator': username,
        'content': PERSON_METADATA_1,
        'create_timestamp': '2024-09-04T08:08:53',
        'update_timestamp': '2024-09-04T08:08:53',
    }
    mock_activity_log.assert_called_once_with(dataset_code='test', target_name=kg_id + '.jsonld', creator='test')


@mock.patch.object(KGActivityLog, 'send_metadata_on_download_event')
async def test_upload_metadata_from_kg_with_filename(mock_activity_log, client, keycloak_mock, httpx_mock):
    kg_id = '9bd75916-4dce-49f6-a70b-878cc7f36cf7'
    dataset_id = str(uuid4())
    template_id = str(uuid4())
    username = 'test'
    filename = 'random_name'
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*dataset/default/schemaTPL/list.*'),
        status_code=200,
        json={'result': [{'name': 'Open_minds', 'geid': template_id}]},
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets/.*'),
        status_code=200,
        json={
            'code': 'test',
        },
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*release/status.*'),
        status_code=200,
        json={
            'data': 'UNRELEASED',
            'message': None,
            'error': None,
            'startTime': None,
            'durationInMs': None,
            'transactionId': None,
        },
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*instances/9bd75916-4dce-49f6-a70b-878cc7f36cf7.*stage=IN_PROGRESS.*'),
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
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*schema$'),
        match_json={
            'name': filename + '.jsonld',
            'dataset_geid': dataset_id,
            'tpl_geid': template_id,
            'standard': 'open_minds',
            'system_defined': False,
            'is_draft': False,
            'content': PERSON_METADATA_1,
            'creator': username,
        },
        status_code=200,
        json={
            'result': {
                'geid': '2e9d768f-5c38-48e0-9436-c97199769ca9',
                'name': filename + '.jsonld',
                'dataset_geid': dataset_id,
                'tpl_geid': template_id,
                'standard': 'open_minds',
                'system_defined': False,
                'is_draft': False,
                'creator': username,
                'content': PERSON_METADATA_1,
                'create_timestamp': '2024-09-04T08:08:53',
                'update_timestamp': '2024-09-04T08:08:53',
            }
        },
    )
    response = await client.get(
        f'/v1/metadata/upload/{kg_id}/{dataset_id}',
        params={'token': 'access_token', 'uploader': username, 'filename': filename},
    )
    assert response.status_code == 200
    assert response.json() == {
        'geid': '2e9d768f-5c38-48e0-9436-c97199769ca9',
        'name': filename + '.jsonld',
        'dataset_geid': dataset_id,
        'tpl_geid': template_id,
        'standard': 'open_minds',
        'system_defined': False,
        'is_draft': False,
        'creator': username,
        'content': PERSON_METADATA_1,
        'create_timestamp': '2024-09-04T08:08:53',
        'update_timestamp': '2024-09-04T08:08:53',
    }
    mock_activity_log.assert_called_once_with(dataset_code='test', target_name='random_name', creator='test')


async def test_upload_metadata_from_kg_doesnt_exists(client, keycloak_mock, httpx_mock):
    kg_id = '9bd75916-4dce-49f6-a70b-878cc7f36cf7'
    dataset_id = str(uuid4())
    template_id = str(uuid4())
    username = 'test'
    httpx_mock.add_response(
        method='POST',
        url=re.compile('.*dataset/default/schemaTPL/list.*'),
        status_code=200,
        json={'result': [{'name': 'Open_minds', 'geid': template_id}]},
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*release/status.*'),
        status_code=404,
    )

    response = await client.get(
        f'/v1/metadata/upload/{kg_id}/{dataset_id}',
        params={'token': 'access_token', 'uploader': username},
    )
    assert response.status_code == 404
    assert 'remote_service_exception' in response.text


@mock.patch.object(KGActivityLog, 'send_metadata_on_refresh_event')
async def test_refresh_metadata_from_kg(mock_activity_log, client, keycloak_mock, httpx_mock, metadata_factory):
    kg_id = '9bd75916-4dce-49f6-a70b-878cc7f36cf7'
    dataset_id = str(uuid4())
    template_id = str(uuid4())
    metadata_id = str(uuid4())
    username = 'test'
    await metadata_factory.create(
        metadata_id=metadata_id,
        dataset_id=dataset_id,
        kg_instance_id=kg_id,
        direction='KG',
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*release/status.*'),
        status_code=200,
        json={
            'data': 'UNRELEASED',
            'message': None,
            'error': None,
            'startTime': None,
            'durationInMs': None,
            'transactionId': None,
        },
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*instances/9bd75916-4dce-49f6-a70b-878cc7f36cf7.*stage=IN_PROGRESS.*'),
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
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets/.*'),
        status_code=200,
        json={
            'code': 'test',
        },
    )
    httpx_mock.add_response(
        method='PUT',
        url=re.compile('.*schema/.*'),
        match_json={
            'username': username,
            'activity': [],
            'content': PERSON_METADATA_1,
        },
        status_code=200,
        json={
            'result': {
                'geid': '2e9d768f-5c38-48e0-9436-c97199769ca9',
                'name': kg_id + '.jsonld',
                'dataset_geid': dataset_id,
                'tpl_geid': template_id,
                'standard': 'open_minds',
                'system_defined': False,
                'is_draft': False,
                'creator': username,
                'content': PERSON_METADATA_1,
                'create_timestamp': '2024-09-04T08:08:53',
                'update_timestamp': '2024-09-04T08:08:53',
            }
        },
    )

    response = await client.get(
        f'/v1/metadata/refresh/{metadata_id}',
        params={'token': 'access_token', 'username': username},
    )
    assert response.status_code == 200
    assert response.json() == {
        'geid': '2e9d768f-5c38-48e0-9436-c97199769ca9',
        'name': kg_id + '.jsonld',
        'dataset_geid': dataset_id,
        'tpl_geid': template_id,
        'standard': 'open_minds',
        'system_defined': False,
        'is_draft': False,
        'creator': username,
        'content': PERSON_METADATA_1,
        'create_timestamp': '2024-09-04T08:08:53',
        'update_timestamp': '2024-09-04T08:08:53',
    }
    mock_activity_log.assert_called_once_with(dataset_code='test', target_name=kg_id + '.jsonld', creator='test')


@mock.patch.object(KGActivityLog, 'send_metadata_on_refresh_event')
async def test_bulk_refresh_metadata_from_kg(mock_activity_log, client, keycloak_mock, httpx_mock, metadata_factory):
    kg_id_1 = str(uuid4())
    kg_id_2 = str(uuid4())
    dataset_id = str(uuid4())
    metadata_id_1 = str(uuid4())
    metadata_id_2 = str(uuid4())
    template_id = str(uuid4())
    username = 'test'
    await metadata_factory.create(
        metadata_id=metadata_id_1,
        dataset_id=dataset_id,
        kg_instance_id=kg_id_1,
        direction='KG',
    )
    await metadata_factory.create(
        metadata_id=metadata_id_2,
        dataset_id=dataset_id,
        kg_instance_id=kg_id_2,
        direction='KG',
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*release/status.*'),
        status_code=200,
        json={
            'data': 'UNRELEASED',
            'message': None,
            'error': None,
            'startTime': None,
            'durationInMs': None,
            'transactionId': None,
        },
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile(f'.*instances/{kg_id_1}.*stage=IN_PROGRESS.*'),
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
    httpx_mock.add_response(
        method='GET',
        url=re.compile(f'.*instances/{kg_id_2}.*stage=IN_PROGRESS.*'),
        status_code=200,
        json={
            'data': PERSON_METADATA_2,
            'message': None,
            'error': None,
            'startTime': 1676042794406,
            'durationInMs': 218,
            'transactionId': None,
        },
    )
    httpx_mock.add_response(
        method='GET',
        url=re.compile('.*datasets/.*'),
        status_code=200,
        json={
            'code': 'test',
        },
    )
    httpx_mock.add_response(
        method='PUT',
        url=re.compile(f'.*schema/{metadata_id_1}.*'),
        match_json={
            'username': username,
            'activity': [],
            'content': PERSON_METADATA_1,
        },
        status_code=200,
        json={
            'result': {
                'geid': '2e9d768f-5c38-48e0-9436-c97199769ca9',
                'name': kg_id_1 + '.jsonld',
                'dataset_geid': dataset_id,
                'tpl_geid': template_id,
                'standard': 'open_minds',
                'system_defined': False,
                'is_draft': False,
                'creator': username,
                'content': PERSON_METADATA_1,
                'create_timestamp': '2024-09-04T08:08:53',
                'update_timestamp': '2024-09-04T08:08:53',
            }
        },
    )
    httpx_mock.add_response(
        method='PUT',
        url=re.compile(f'.*schema/{metadata_id_2}.*'),
        match_json={
            'username': username,
            'activity': [],
            'content': PERSON_METADATA_2,
        },
        status_code=200,
        json={
            'result': {
                'geid': '2e9d768f-5c38-48e0-9436-c97199769ca9',
                'name': kg_id_2 + '.jsonld',
                'dataset_geid': dataset_id,
                'tpl_geid': template_id,
                'standard': 'open_minds',
                'system_defined': False,
                'is_draft': False,
                'creator': username,
                'content': PERSON_METADATA_2,
                'create_timestamp': '2024-09-04T08:08:53',
                'update_timestamp': '2024-09-04T08:08:53',
            }
        },
    )

    response = await client.get(
        f'/v1/metadata/refresh/dataset/{dataset_id}',
        params={'token': 'access_token', 'username': username},
    )
    assert response.status_code == 200
    mock_activity_log.has_calls(mock.call(dataset_code='test', target_name=kg_id_1 + '.jsonld', creator='test'))


async def test_refresh_metadata_from_kg_not_found(client, keycloak_mock):
    metadata_id = str(uuid4())
    username = 'tester'

    response = await client.get(
        f'/v1/metadata/refresh/{metadata_id}',
        params={'token': 'access_token', 'username': username},
    )
    assert response.status_code == 404
    assert 'Requested resource is not found' in response.text
