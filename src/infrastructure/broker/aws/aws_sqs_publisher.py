from common_py_aws import PublishMessageRequest, SqsConnection, SqsPublisherService

from src.infrastructure.env_manager.env_manager import EnvironmentVariablesConstants


class SqsNotifierMessage(PublishMessageRequest):
    def __init__(self, body: str):
        self.body = body

    def get_url(self):
        return EnvironmentVariablesConstants.AWS_SQS_NOTIFY_QUEUE_URL

    def get_message(self):
        return self.body


class SqsPublisher:
    def __init__(self, client: SqsConnection):
        self.sqs_client = client
        self.sqs_publisher = SqsPublisherService(client)

    async def publish_sample_messages(self):
        sample_messages = [
            {"body": "Message 1"},
            {"body": "Message 2"},
            {"body": "Message 3"},
        ]
        for message in sample_messages:
            await self.sqs_publisher.publish(SqsNotifierMessage(message["body"]))
