import json

from common_py_aws import ConsumerHandler, SqsMessageReceived

from src.contracts.message_sanitizer import MessageSanitizer
from src.models.notification_email_request import NotificationEmailRequest
from src.services.notification_manager_service import NotificationManagerService


class SqsNotificatorConsumer(ConsumerHandler):

    def __init__(
        self,
        message_sanitizer: MessageSanitizer,
        notification_manager_service: NotificationManagerService,
    ):
        self._message_sanitizer = message_sanitizer
        self._notification_manager_service = notification_manager_service

    async def process_message(self, message: SqsMessageReceived) -> bool:
        # Recibir mensaje, enviarlo a servicio de validación
        # Si es valido, enviar correo
        try:
            print(f"Processing message: {message.body}")
            sanitized_message = self._message_sanitizer.sanitize(message.body)
            print(f"Sanitized message {sanitized_message.get_content()}")
            is_sent = await self._notification_manager_service.send(
                NotificationEmailRequest(**json.loads(sanitized_message.get_content()))
            )
            print(f"Notification sent: {is_sent}")
            if not is_sent:
                print("Failed to send notification")
            return is_sent
        except ValueError as e:
            print(f"Message validation failed: {e}")
            return False
