# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from unittest import mock

from kg_integration.utils.kafka_manager import KafkaProducerClient
from kg_integration.utils.spaces_activity_log import KGActivityLog


@mock.patch.object(KafkaProducerClient, 'send')
@mock.patch.object(KafkaProducerClient, 'create_kafka_producer')
async def test_activity_manager(mock_kafka_send, mock_kafka_producer):
    activity_log = KGActivityLog()
    await activity_log.send_metadata_on_upload_event(dataset_code='test', target_name='test', creator='test')
    await activity_log.send_metadata_on_refresh_event(dataset_code='test', target_name='test', creator='test')
    await activity_log.send_metadata_on_download_event(dataset_code='test', target_name='test', creator='test')
    await activity_log.send_metadata_on_delete_event(dataset_code='test', target_name='test', creator='test')
    mock_kafka_send.assert_called()
