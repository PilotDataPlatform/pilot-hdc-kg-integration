# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from kg_integration.schemas.activity_log import SpaceActivityLogSchema
from kg_integration.utils.activity_log_manager import ActivityLogService


class BaseKGActivityLog(ActivityLogService):

    topic = 'dataset.activity'
    avro_schema_path = 'kg_integration/schemas/space.activity.avsc'


class KGActivityLog(BaseKGActivityLog):
    """Class for managing the dataset event send to the msg broker."""

    async def send_kg_on_create_event(self, dataset_code: str, creator: str):

        log_schema = SpaceActivityLogSchema(activity_type='kg_create', container_code=dataset_code, user=creator)

        return await self._message_send(log_schema.model_dump())

    async def send_metadata_event(self, activity_type: str, dataset_code: str, target_name: str, creator: str):
        log_schema = SpaceActivityLogSchema(
            activity_type=activity_type, target_name=target_name, container_code=dataset_code, user=creator
        )
        return await self._message_send(log_schema.model_dump())

    async def send_metadata_on_upload_event(self, **kwargs):
        return await self.send_metadata_event(activity_type='kg_metadata_upload', **kwargs)

    async def send_metadata_on_download_event(self, **kwargs):
        return await self.send_metadata_event(activity_type='kg_metadata_download', **kwargs)

    async def send_metadata_on_delete_event(self, **kwargs):
        return await self.send_metadata_event(activity_type='kg_metadata_delete', **kwargs)

    async def send_metadata_on_refresh_event(self, **kwargs):
        return await self.send_metadata_event(activity_type='kg_metadata_refresh', **kwargs)
