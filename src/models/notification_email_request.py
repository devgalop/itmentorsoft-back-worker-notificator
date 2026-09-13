import json

from pydantic import BaseModel, field_validator
import re

from src.contracts.input_message import InputMessage

EMAIL_PATTERN = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
MESSAGE_KEY_PATTERN = r"^%\w+%$"


class MessageVariables(BaseModel):
    key: str
    value: str

    @field_validator("key")
    def validate_variable_key(cls, value: str) -> str:
        if not re.match(MESSAGE_KEY_PATTERN, value):
            raise ValueError("Invalid message variable key format")
        return value

    @field_validator("key", "value")
    def validate_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Field cannot be empty")
        return value

    def to_dict(self) -> dict[str, str]:
        return {"key": self.key, "value": self.value}


class NotificationEmailRequest(BaseModel, InputMessage):
    recipient: str
    subject: str
    html_template_code: str
    message_variables: list[MessageVariables]

    def get_content(self) -> str:
        return json.dumps(
            {
                "recipient": self.recipient,
                "subject": self.subject,
                "html_template_code": self.html_template_code,
                "message_variables": [mv.to_dict() for mv in self.message_variables],
            }
        )

    @field_validator("recipient")
    def validate_recipient(cls, value: str) -> str:
        if not value:
            raise ValueError("Recipient email address is required")
        if len(value) < 5:
            raise ValueError("Recipient email address is too short")
        if len(value) > 254:
            raise ValueError("Recipient email address is too long")
        if not re.match(EMAIL_PATTERN, value):
            raise ValueError("Invalid email address")
        return value

    @field_validator("subject")
    def validate_subject(cls, value: str) -> str:
        if not value:
            raise ValueError("Subject is required")
        if len(value) < 3:
            raise ValueError("Subject is too short")
        if len(value) > 255:
            raise ValueError("Subject is too long")
        return value

    @field_validator("html_template_code")
    def validate_html_template_code(cls, value: str) -> str:
        if not value:
            raise ValueError("HTML template code is required")
        if len(value) < 3:
            raise ValueError("HTML template code is too short")
        if len(value) > 100:
            raise ValueError("HTML template code is too long")
        return value
