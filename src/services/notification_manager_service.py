from itmentorsoft_persistence import AsyncSessionLocal

from src.contracts.notification_service import (
    NotificationConfigBuilder,
    NotificationService,
)
from src.models.notification_email_request import NotificationEmailRequest
from itmentorsoft_persistence.repositories import NotificationRepository
from src.services.template_loader import TemplateLoader
from itmentorsoft_persistence.dto import InsertNotificationRequest
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession


class NotificationManagerService:

    def __init__(
        self,
        notify_service: NotificationService,
        template_loader: TemplateLoader,
        notification_repository_factory: Callable[
            [AsyncSession], NotificationRepository
        ],
    ):
        self.notify_service = notify_service
        self.template_loader = template_loader
        self.notification_repository_factory = notification_repository_factory

    async def send(self, notification_message: NotificationEmailRequest) -> bool:
        """Send a notification email based on the provided notification message.

        Args:
            notification_message (NotificationEmailRequest): Notification message containing recipient, subject, template code, and message variables.

        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """

        notification_builder = NotificationConfigBuilder(
            destination=notification_message.recipient,
            subject=notification_message.subject,
        )
        try:
            html_content = self.template_loader.load(
                notification_message.html_template_code
            )
            html_content = self.replace_variables(html_content, notification_message)
            notification_builder.set_template(html_content)
            notification_config = notification_builder.build()
            await self.insert_notification(notification_message)
            is_sent = await self.notify_service.send_notification(notification_config)
            if not is_sent:
                print(f"Failed to send email to {notification_message.recipient}.")
            return is_sent
        except FileNotFoundError:
            print(
                f"Email template {notification_message.html_template_code} not found. Please contact support."
            )
            return False

    def replace_variables(
        self, html_content: str, notification_message: NotificationEmailRequest
    ) -> str:
        """Replace all message variables in the HTML content with their corresponding values from the notification message.

        Args:
            html_content (str): HTML content of the email template.
            notification_message (NotificationEmailRequest): Notification message containing variables to replace in the HTML content.

        Returns:
            str: HTML content with all message variables replaced.
        """
        for variable in notification_message.message_variables:
            html_content = html_content.replace(variable.key, variable.value)
        return html_content

    def get_summary_message(self, template_code: str) -> str:
        """Get a summary message for a given template code.

        Args:
            template_code: The template code, e.g. "recovery_password".

        Returns:
            A summary message as a string.
        """
        return self.template_loader.get_summary_message(template_code)

    async def insert_notification(self, notification_message: NotificationEmailRequest):
        message = self.get_summary_message(notification_message.html_template_code)
        if not message or message.strip() == "":
            return

        url_variable = self.template_loader.get_url(
            notification_message.html_template_code
        )
        if not url_variable or url_variable.strip() == "":
            for variable in notification_message.message_variables:
                url_variable = url_variable.replace(variable.key, variable.value)

        async with AsyncSessionLocal() as session:
            self.notification_repository = self.notification_repository_factory(session)
            notification = InsertNotificationRequest(
                user_id=notification_message.recipient,
                subject=notification_message.subject,
                message=message,
                url=url_variable,
            )
            await self.notification_repository.create_notification(notification)
