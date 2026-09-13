from src.contracts.input_message import InputMessage
import json
from src.contracts.message_sanitizer import MessageSanitizer
from src.models.notification_email_request import (
    MessageVariables,
    NotificationEmailRequest,
)


class NotificationMessageSanitizer(MessageSanitizer):

    def sanitize(self, message: str) -> InputMessage:
        message_to_dict = json.loads(message)
        if not message_to_dict:
            raise ValueError("Message content is empty")
        if "recipient" not in message_to_dict:
            raise ValueError("Recipient is missing in the message content")
        if "subject" not in message_to_dict:
            raise ValueError("Subject is missing in the message content")
        if "html_template_code" not in message_to_dict:
            raise ValueError("HTML template code is missing in the message content")
        if "message_variables" not in message_to_dict:
            message_to_dict["message_variables"] = []

        if not isinstance(message_to_dict["message_variables"], list):
            raise ValueError("Message variables should be a list")
        message_variables: list[MessageVariables] = []
        for variable in message_to_dict["message_variables"]:
            if not isinstance(variable, dict):
                raise ValueError("Each message variable should be a dictionary")
            if "key" not in variable:
                raise ValueError("Each message variable should have a 'key'")
            if "value" not in variable:
                raise ValueError("Each message variable should have a 'value'")
            message_variables.append(
                MessageVariables(key=variable["key"], value=variable["value"])
            )

        return NotificationEmailRequest(
            recipient=message_to_dict["recipient"],
            subject=message_to_dict["subject"],
            html_template_code=message_to_dict["html_template_code"],
            message_variables=message_variables,
        )
