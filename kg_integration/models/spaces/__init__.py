# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from .crud import SpacesCRUD
from .crud import get_spaces_crud
from .spaces import Spaces

__all__ = ['Spaces', 'SpacesCRUD', 'get_spaces_crud']
