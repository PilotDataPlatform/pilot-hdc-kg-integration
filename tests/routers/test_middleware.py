# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re

import pytest


@pytest.mark.asyncio
async def test_request_with_token_header(client, httpx_mock, keycloak_mock):
    headers = {'Authorization': 'Bearer test_token'}
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
        match_headers={'Authorization': 'Bearer exchanged_access_token'},
    )
    response = await client.get('/v1/spaces/', headers=headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_request_with_token_param(client, httpx_mock, keycloak_mock):
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
        match_headers={'Authorization': 'Bearer exchanged_access_token'},
    )
    response = await client.get('/v1/spaces/', params={'token': 'test_token'})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_middleware_does_not_change_param_token(settings, client, httpx_mock):
    headers = {'Authorization': 'Bearer another_test_token'}
    httpx_mock.add_response(
        method='GET',
        url=settings.KEYCLOAK_URL + f'realms/{settings.KEYCLOAK_REALM}/broker/{settings.KEYCLOAK_BROKER}/token',
        status_code=200,
        json={'access_token': 'exchanged_access_token'},
        match_headers={'Authorization': 'Bearer test_token'},
    )
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
        match_headers={'Authorization': 'Bearer exchanged_access_token'},
    )
    response = await client.get('/v1/spaces/', params={'token': 'test_token'}, headers=headers)
    assert httpx_mock.get_request(match_headers={'Authorization': 'Bearer test_token'})
    assert response.status_code == 200
