# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi.responses import JSONResponse

from kg_integration.core.db import is_db_connected

router = APIRouter()


@router.get('/health', summary='Healthcheck if all service dependencies are online.')
async def get_db_status(is_db_health: bool = Depends(is_db_connected)) -> Response:
    """Return response that represents status of the database and kafka connections."""

    if is_db_health:
        return Response(status_code=204)
    return JSONResponse(status_code=503, content='Database is unavailable.')
