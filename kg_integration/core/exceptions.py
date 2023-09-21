# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from abc import ABCMeta
from abc import abstractmethod
from http import HTTPStatus


class ServiceException(Exception, metaclass=ABCMeta):
    """Base class for service exceptions."""

    domain: str = 'global'

    @property
    @abstractmethod
    def status(self) -> int:
        """HTTP status code applicable to the problem."""

        raise NotImplementedError

    @property
    @abstractmethod
    def code(self) -> str:
        """Component-specific error code."""

        raise NotImplementedError

    @property
    @abstractmethod
    def details(self) -> str:
        """Additional information with specific explanation for this occurrence of the problem."""

        raise NotImplementedError

    def dict(self) -> dict[str, str]:
        """Represent error as dictionary."""

        return {
            'code': f'{self.domain}.{self.code}',
            'details': self.details,
        }


class RemoteServiceException(ServiceException):
    """Raised when remote service returned an error."""

    def __init__(self, status: int, details: str):
        self.remote_status = status
        self.error_message = details

    @property
    def status(self) -> int:
        return self.remote_status

    @property
    def code(self) -> str:
        return 'remote_service_exception'

    @property
    def details(self) -> str:
        return self.error_message


class UnhandledException(ServiceException):
    """Raised when unhandled/unexpected internal error occurred."""

    @property
    def status(self) -> int:
        return HTTPStatus.INTERNAL_SERVER_ERROR

    @property
    def code(self) -> str:
        return 'unhandled_exception'

    @property
    def details(self) -> str:
        return 'Unexpected Internal Server Error'


class TokenExchangeFailed(ServiceException):
    """Raised when authentication token could not be exchanged."""

    @property
    def status(self) -> int:
        return HTTPStatus.UNAUTHORIZED

    @property
    def code(self) -> str:
        return 'not_authorised'

    @property
    def details(self) -> str:
        return 'Could not exchange authentication token with Keycloak'


class TokenNotProvided(ServiceException):
    """Raised when there is no authorization token in the request."""

    @property
    def status(self) -> int:
        return HTTPStatus.UNPROCESSABLE_ENTITY

    @property
    def code(self) -> str:
        return 'no_token'

    @property
    def details(self) -> str:
        return 'No authorization token in the request'


class NotAvailable(ServiceException):
    """Raised when remote resource is not available."""

    @property
    def status(self) -> int:
        return HTTPStatus.SERVICE_UNAVAILABLE

    @property
    def code(self) -> str:
        return 'not_available'

    @property
    def details(self) -> str:
        return 'Remote resource is not available.'


class NoData(ServiceException):
    """Raised when remote resource returns no data."""

    @property
    def status(self) -> int:
        return HTTPStatus.SERVICE_UNAVAILABLE

    @property
    def code(self) -> str:
        return 'no_data'

    @property
    def details(self) -> str:
        return 'Remote resource returned no data.'


class NoProject(ServiceException):
    """Raised when dataset does not contain project code."""

    @property
    def status(self) -> int:
        return HTTPStatus.NOT_FOUND

    @property
    def code(self) -> str:
        return 'no_project'

    @property
    def details(self) -> str:
        return 'Dataset is not connected to a project.'


class NotFound(ServiceException):
    """Raised when requested resource is not found."""

    @property
    def status(self) -> int:
        return HTTPStatus.NOT_FOUND

    @property
    def code(self) -> str:
        return 'not_found'

    @property
    def details(self) -> str:
        return 'Requested resource is not found'


class SpaceAlreadyExists(ServiceException):
    """Raised when trying to create already existing space."""

    @property
    def status(self) -> int:
        return HTTPStatus.BAD_REQUEST

    @property
    def code(self) -> str:
        return 'already_exists'

    @property
    def details(self) -> str:
        return 'Space was already created'
