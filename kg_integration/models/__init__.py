# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from .base import DBModel
from .metadata import Metadata
from .metadata import MetadataCRUD
from .metadata import get_metadata_crud
from .spaces import Spaces
from .spaces import SpacesCRUD
from .spaces import get_spaces_crud

__all__ = ['DBModel', 'Spaces', 'Metadata', 'SpacesCRUD', 'MetadataCRUD', 'get_spaces_crud', 'get_metadata_crud']
