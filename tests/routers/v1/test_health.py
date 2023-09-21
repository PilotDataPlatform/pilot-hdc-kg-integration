# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest


@pytest.mark.asyncio
async def test_health_should_return_204_with_empty_response(client):
    response = await client.get('/v1/health')
    assert response.status_code == 204
    assert not response.text
