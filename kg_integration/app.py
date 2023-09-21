# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from functools import partial

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi_sqlalchemy import DBSessionMiddleware
from starlette.responses import JSONResponse

from kg_integration.config import Settings
from kg_integration.config import get_settings
from kg_integration.core.exceptions import NotAvailable
from kg_integration.core.exceptions import ServiceException
from kg_integration.core.exceptions import UnhandledException
from kg_integration.middleware import TokenMiddleware
from kg_integration.routers import api_root
from kg_integration.routers.v1 import api_health
from kg_integration.routers.v1 import api_metadata
from kg_integration.routers.v1 import api_spaces
from kg_integration.routers.v1 import api_users


def create_app() -> FastAPI:
    """Initialize and configure the application."""

    settings = get_settings()

    app = FastAPI(
        title='KG Integration Service',
        description='Service for performing KG requests.',
        docs_url='/v1/api-doc',
        redoc_url='/v1/api-redoc',
        version=settings.VERSION,
    )

    setup_routers(app)
    setup_middlewares(app, settings)
    setup_dependencies(app, settings)
    setup_exception_handlers(app)

    return app


def setup_routers(app: FastAPI) -> None:
    """Configure the application routers."""
    app.include_router(api_health.router, prefix='/v1')
    app.include_router(api_spaces.router, prefix='/v1')
    app.include_router(api_metadata.router, prefix='/v1')
    app.include_router(api_users.router, prefix='/v1')
    app.include_router(api_root.router, prefix='/v1')


def setup_middlewares(app: FastAPI, settings: Settings) -> None:
    """Configure the application middlewares."""
    app.add_middleware(TokenMiddleware)
    app.add_middleware(DBSessionMiddleware, db_url=settings.RDS_DB_URI)
    app.add_middleware(
        CORSMiddleware,
        allow_origins='*',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )


def setup_dependencies(app: FastAPI, settings: Settings) -> None:
    """Perform dependencies setup/teardown at the application startup/shutdown events."""

    app.add_event_handler('startup', partial(startup_event, settings))


async def startup_event(settings: Settings) -> None:
    """Initialise dependencies at the application startup event."""
    pass


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure the application exception handlers."""

    app.add_exception_handler(ServiceException, service_exception_handler)
    app.add_exception_handler(httpx.TimeoutException, timeout_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)


def service_exception_handler(request: Request, exception: ServiceException) -> JSONResponse:
    """Return the default response structure for service exceptions."""

    return JSONResponse(status_code=exception.status, content={'error': exception.dict(), 'message': str(exception)})


def unexpected_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    """Return the default unhandled exception response structure for all unexpected exceptions."""

    return service_exception_handler(request, UnhandledException())


def timeout_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    """Return the default unhandled exception response structure for all unexpected exceptions."""

    return service_exception_handler(request, NotAvailable())
