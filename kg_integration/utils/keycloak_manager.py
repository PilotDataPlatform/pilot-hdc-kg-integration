# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import backoff
import httpx
from fastapi import Depends

from kg_integration.config import Settings
from kg_integration.config import get_settings
from kg_integration.core.exceptions import TokenExchangeFailed
from kg_integration.logger import logger


class KeycloakManager:
    """Manager for Keycloak connection."""

    def __init__(self, settings: Settings):
        self.hdc_keycloak_url = (
            settings.KEYCLOAK_URL + f'realms/{settings.KEYCLOAK_REALM}/broker/{settings.KEYCLOAK_BROKER}/token'
        )
        self.ebrains_keycloak_url = settings.KEYCLOAK_EXTERNAL_URL + 'realms/hbp/protocol/openid-connect/token'
        self.service_account_id = settings.KG_SERVICE_ACCOUNT_ID
        self.service_account_secret = settings.KG_SERVICE_ACCOUNT_SECRET
        self.timeout = settings.EXTERNAL_SERVICE_TIMEOUT

    async def exchange_token(self, token: str) -> str | None:
        """Exchange local keycloak token for an EBRAINS token for external requests."""
        headers = {'Authorization': 'Bearer ' + token}
        logger.info('Exchanging token')
        async with httpx.AsyncClient() as client:
            response = await client.get(self.hdc_keycloak_url, headers=headers)
            data = response.json()

        if response.status_code != 200:
            error_msg = f'Token exchange failed for token {token}'
            logger.error(error_msg)
            raise TokenExchangeFailed('Could not exchange the token, error: ' + response.text)

        return data.get('access_token')

    @backoff.on_exception(backoff.fibo, TokenExchangeFailed, max_tries=5, jitter=None)
    async def get_service_account_token(self) -> str | None:
        """Get an access token for a KG service account from EBRAINS Keycloak."""
        logger.info('Getting service account token')
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            form_data = {
                'grant_type': 'client_credentials',
                'client_id': self.service_account_id,
                'client_secret': self.service_account_secret,
                'scope': 'openid group roles team email profile',
            }
            response = await client.post(self.ebrains_keycloak_url, data=form_data)
            data = response.json()

        if response.status_code != 200:
            logger.error('Could not get the service account token')
            raise TokenExchangeFailed('Could not get the service account token, error: ' + response.text)

        return data.get('access_token')


async def get_keycloak_manager(settings: Settings = Depends(get_settings)) -> KeycloakManager:
    """Create a FastAPI callable dependency for KGManager."""
    return KeycloakManager(settings)
