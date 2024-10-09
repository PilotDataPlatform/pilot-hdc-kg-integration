# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from urllib.parse import urlencode

from starlette.middleware.base import BaseHTTPMiddleware


class TokenMiddleware(BaseHTTPMiddleware):
    """Middleware to get token from headers (if exists) and put it into query params."""

    async def dispatch(self, request, call_next):
        if not request.query_params.get('token'):
            bearer_token = request.headers.get('Authorization')
            if bearer_token:
                _, token = bearer_token.split(' ')
                params = dict(request.query_params)
                params['token'] = token
                request.scope['query_string'] = urlencode(params).encode('utf-8')

        response = await call_next(request)
        return response
