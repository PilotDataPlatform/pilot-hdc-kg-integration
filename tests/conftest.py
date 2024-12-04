# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re
from urllib.parse import urlparse

import pytest_asyncio
from alembic.command import downgrade
from alembic.command import upgrade
from alembic.config import Config
from fastapi import FastAPI
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql.ddl import CreateSchema
from testcontainers.postgres import PostgresContainer

from kg_integration.app import create_app
from kg_integration.config import Settings
from kg_integration.config import get_settings
from kg_integration.core.db import get_db_session
from kg_integration.models import MetadataCRUD


@pytest_asyncio.fixture(scope='session')
def db_postgres():
    with PostgresContainer(
        'docker-registry.ebrains.eu/hdc-services-external/postgres:14.1', dbname='kg_integration'
    ) as postgres:
        db_uri = postgres.get_connection_url()
        yield db_uri.replace(f'{urlparse(db_uri).scheme}://', 'postgresql+asyncpg://', 1)


@pytest_asyncio.fixture()
async def create_db(db_postgres):
    engine = create_async_engine(db_postgres)
    async with engine.connect() as conn:
        await conn.execute(CreateSchema('kg_integration', if_not_exists=True))
        await conn.commit()
        await conn.close()
    config = Config('./migrations/alembic.ini')
    upgrade(config, 'head')
    yield engine
    downgrade(config, 'base')
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(create_db):
    try:
        session = AsyncSession(
            create_db,
            expire_on_commit=False,
        )
        yield session
        await session.commit()
    finally:
        await session.close()


@pytest_asyncio.fixture()
def metadata_crud(db_session) -> MetadataCRUD:
    yield MetadataCRUD(db_session)


@pytest_asyncio.fixture()
def keycloak_mock(settings: Settings, httpx_mock) -> None:
    httpx_mock.add_response(
        method='GET',
        url=settings.KEYCLOAK_URL + f'realms/{settings.KEYCLOAK_REALM}/broker/{settings.KEYCLOAK_BROKER}/token',
        status_code=200,
        json={'access_token': 'exchanged_access_token'},
    )


@pytest_asyncio.fixture()
def keycloak_fail_mock(settings: Settings, httpx_mock) -> None:
    httpx_mock.add_response(
        method='GET',
        url=settings.KEYCLOAK_URL + f'realms/{settings.KEYCLOAK_REALM}/broker/{settings.KEYCLOAK_BROKER}/token',
        status_code=500,
        json={'error': 'token_exchange_error'},
    )


@pytest_asyncio.fixture()
def external_keycloak_mock(settings, httpx_mock) -> None:
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


@pytest_asyncio.fixture()
def settings(db_postgres) -> Settings:
    settings = get_settings()
    settings.RDS_DB_URI = db_postgres
    yield settings


@pytest_asyncio.fixture()
def app(settings, db_session) -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_db_session] = lambda: db_session
    yield app


@pytest_asyncio.fixture()
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='https://kg_integration') as client:
        yield client


@pytest_asyncio.fixture
def non_mocked_hosts() -> list:
    return ['kg_integration', '127.0.0.1']


pytest_plugins = [
    'tests.fixtures.base',
    'tests.fixtures.spaces',
    'tests.fixtures.metadata',
]
