# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends

from kg_integration.config import Settings
from kg_integration.config import get_settings

router = APIRouter()


@router.get('/')
async def root(settings: Settings = Depends(get_settings)):
    """For testing if service's up."""
    return {'message': 'Service KG Integration On, Version: ' + settings.VERSION}
