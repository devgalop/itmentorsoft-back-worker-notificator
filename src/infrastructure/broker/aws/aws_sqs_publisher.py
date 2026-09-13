from common_py_aws import SqsConnection, SqsPublisherService

from src.models.notification_message import (
    NotificationMessage,
    NotificationMessageVariables,
)


class SqsPublisher:
    def __init__(self, client: SqsConnection):
        self.sqs_client = client
        self.sqs_publisher = SqsPublisherService(client)

    async def publish_sample_messages(self):
        sample_messages = [
            NotificationMessage(
                recipient="recipient_1@yopmail.com",
                subject="Subject 1",
                html_template_code="recovery_password",
                message_variables=[
                    NotificationMessageVariables(key="%key1%", value="value1")
                ],
            ),
            NotificationMessage(
                recipient="recipient_2@yopmail.com",
                subject="Subject 2",
                html_template_code="otp",
                message_variables=[
                    NotificationMessageVariables(key="%key2%", value="value2")
                ],
            ),
            NotificationMessage(
                recipient="recipient_3@yopmail.com",
                subject="Subject 3",
                html_template_code="user_created",
                message_variables=[
                    NotificationMessageVariables(key="%key3%", value="value3")
                ],
            ),
        ]
        for message in sample_messages:
            await self.sqs_publisher.publish(message)
