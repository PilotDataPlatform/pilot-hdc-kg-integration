# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from kg_integration.models.crud import CRUD


class BaseFactory:
    """Base class for creating testing purpose entries."""

    crud: CRUD

    def __init__(self, crud: CRUD) -> None:
        self.crud = crud
