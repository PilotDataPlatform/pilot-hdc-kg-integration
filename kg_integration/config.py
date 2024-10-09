# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import logging
from functools import lru_cache
from typing import Any

from common import VaultClient
from pydantic_settings import BaseSettings
from pydantic_settings import InitSettingsSource
from pydantic_settings import PydanticBaseSettingsSource
from pydantic_settings import SettingsConfigDict
from starlette.config import Config

config = Config('.env')
SRV_NAMESPACE = config('APP_NAME', cast=str, default='service_kg_integration')
CONFIG_CENTER_ENABLED = config('CONFIG_CENTER_ENABLED', cast=str, default='false')


def load_vault_settings() -> dict[str, Any]:
    if CONFIG_CENTER_ENABLED == 'false':
        return {}
    else:
        return vault_factory()


def vault_factory() -> dict:
    vc = VaultClient(config('VAULT_URL'), config('VAULT_CRT'), config('VAULT_TOKEN'))
    return vc.get_from_vault(SRV_NAMESPACE)


class Settings(BaseSettings):
    """KG integration service configuration settings."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='allow',
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        vault_settings = InitSettingsSource(settings_cls, load_vault_settings())
        return env_settings, vault_settings, init_settings, file_secret_settings

    APP_NAME: str = 'kg_integration'
    VERSION: str = '1.2.1'
    HOST: str = '127.0.0.1'
    PORT: int = 5064
    WORKERS: int = 1
    RELOAD: bool = False
    LOGGING_LEVEL: int = logging.INFO
    LOGGING_FORMAT: str = 'json'
    EXTERNAL_SERVICE_TIMEOUT: int = 1000

    RDS_SCHEMA_DEFAULT: str = 'kg_integration'
    RDS_DB: str = 'kg_integration'
    RDS_HOST: str = 'localhost'
    RDS_USER: str = 'postgres'
    RDS_PASSWORD: str = 'postgresD3G5D'
    RDS_PORT: str = '5432'

    KG_ENV: str = 'ppd'
    KG_PREFIX: str = 'collab-'

    COLLAB_ENV: str = 'prod'
    COLLAB_PREFIX: str = 'hdc-'

    KEYCLOAK_URL: str = 'https://iam.dev.hdc.humanbrainproject.eu/'
    KEYCLOAK_REALM: str = 'hdc'
    KEYCLOAK_BROKER: str = 'ebrains-keycloak'
    KEYCLOAK_EXTERNAL_URL: str = 'https://iam.ebrains.eu/auth/'

    KG_SERVICE_ACCOUNT_ID: str = 'hdcclient-kg'
    KG_SERVICE_ACCOUNT_SECRET: str = 'notarealsecret'

    KAFKA_URL: str = 'kafka-headless:9092'

    AUTH_SERVICE: str = 'http://auth.utility'
    DATASET_SERVICE: str = 'http://dataset.utility'
    PROJECT_SERVICE: str = 'http://project.utility'

    def __init__(self, *args: Any, **kwds: Any) -> None:
        super().__init__(*args, **kwds)

        self.RDS_DB_URI = (
            f'postgresql+asyncpg://{self.RDS_USER}:{self.RDS_PASSWORD}@{self.RDS_HOST}:{self.RDS_PORT}/{self.RDS_DB}'
        )
        self.KG_URL = 'https://core.kg-ppd.ebrains.eu/' if self.KG_ENV == 'ppd' else 'https://core.kg.ebrains.eu/'
        self.COLLAB_URL = (
            'https://wiki-int.ebrains.eu/rest/' if self.COLLAB_ENV == 'ppd' else 'https://wiki.ebrains.eu/rest/'
        )
        if not self.KEYCLOAK_URL.endswith('/'):
            self.KEYCLOAK_URL = self.KEYCLOAK_URL + '/'


@lru_cache(1)
def get_settings() -> Settings:
    settings = Settings()
    return settings
