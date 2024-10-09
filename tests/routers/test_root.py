# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest


@pytest.mark.asyncio
async def test_root_should_return_200_and_version(client, settings):
    response = await client.get('/v1/')
    assert response.status_code == 200
    assert response.json() == {'message': 'Service KG Integration On, Version: ' + settings.VERSION}
