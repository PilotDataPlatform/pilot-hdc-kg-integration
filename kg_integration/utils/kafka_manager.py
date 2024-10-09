# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from io import BytesIO

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from aiokafka.errors import KafkaError

from kg_integration.config import get_settings
from kg_integration.logger import logger

settings = get_settings()


class KafkaProducerClient:

    aioproducer = None

    async def create_kafka_producer(self):
        if not self.aioproducer:
            try:
                self.aioproducer = AIOKafkaProducer(bootstrap_servers=[settings.KAFKA_URL])
                await self.aioproducer.start()
            except KafkaConnectionError as exc:
                logger.exception('Kafka connection error')
                self.aioproducer = None
                raise exc

    async def send(self, topic: str, msg: BytesIO):
        try:
            await self.aioproducer.send(topic, msg)
        except KafkaError:
            logger.exception('Error sending ActivityLog to Kafka')


kafka_client = KafkaProducerClient()


async def get_kafka_client():
    await kafka_client.create_kafka_producer()
    return kafka_client
