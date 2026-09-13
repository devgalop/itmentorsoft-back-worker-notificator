import json
import pytest

from src.services.notification_message_sanitizer import NotificationMessageSanitizer
from src.models.notification_email_request import (
    NotificationEmailRequest,
    MessageVariables,
)

VALID_JSON = json.dumps(
    {
        "recipient": "alice@example.com",
        "subject": "Hello",
        "html_template_code": "TPL",
        "message_variables": [{"key": "%NAME%", "value": "Alice"}],
    }
)

VALID_JSON_NO_VARS = json.dumps(
    {
        "recipient": "alice@example.com",
        "subject": "Hello",
        "html_template_code": "TPL",
    }
)


class TestNotificationMessageSanitizer:
    def _sanitizer(self):
        return NotificationMessageSanitizer()

    def test_valid_message_with_variables(self):
        result = self._sanitizer().sanitize(VALID_JSON)
        assert isinstance(result, NotificationEmailRequest)
        assert result.recipient == "alice@example.com"
        assert result.subject == "Hello"
        assert result.html_template_code == "TPL"
        assert len(result.message_variables) == 1
        assert result.message_variables[0].key == "%NAME%"
        assert result.message_variables[0].value == "Alice"

    def test_valid_message_without_variables_defaults_to_empty_list(self):
        result = self._sanitizer().sanitize(VALID_JSON_NO_VARS)
        assert isinstance(result, NotificationEmailRequest)
        assert result.message_variables == []

    def test_empty_message_raises(self):
        # The sanitizer calls json.loads("") first which raises JSONDecodeError,
        # so we catch the broader parse failure rather than the custom ValueError.
        with pytest.raises((ValueError, json.JSONDecodeError)):
            self._sanitizer().sanitize("")

    def test_missing_recipient_raises(self):
        data = json.dumps({"subject": "Hi", "html_template_code": "TPL"})
        with pytest.raises(ValueError, match="Recipient is missing"):
            self._sanitizer().sanitize(data)

    def test_missing_subject_raises(self):
        data = json.dumps({"recipient": "a@b.com", "html_template_code": "TPL"})
        with pytest.raises(ValueError, match="Subject is missing"):
            self._sanitizer().sanitize(data)

    def test_missing_html_template_code_raises(self):
        data = json.dumps({"recipient": "a@b.com", "subject": "Hi"})
        with pytest.raises(ValueError, match="HTML template code is missing"):
            self._sanitizer().sanitize(data)

    def test_message_variables_not_a_list_raises(self):
        data = json.dumps(
            {
                "recipient": "a@b.com",
                "subject": "Hi",
                "html_template_code": "TPL",
                "message_variables": "not-a-list",
            }
        )
        with pytest.raises(ValueError, match="Message variables should be a list"):
            self._sanitizer().sanitize(data)

    def test_variable_not_a_dict_raises(self):
        data = json.dumps(
            {
                "recipient": "a@b.com",
                "subject": "Hi",
                "html_template_code": "TPL",
                "message_variables": ["string-item"],
            }
        )
        with pytest.raises(
            ValueError, match="Each message variable should be a dictionary"
        ):
            self._sanitizer().sanitize(data)

    def test_variable_missing_key_raises(self):
        data = json.dumps(
            {
                "recipient": "a@b.com",
                "subject": "Hi",
                "html_template_code": "TPL",
                "message_variables": [{"value": "no-key"}],
            }
        )
        with pytest.raises(
            ValueError, match="Each message variable should have a 'key'"
        ):
            self._sanitizer().sanitize(data)

    def test_variable_missing_value_raises(self):
        data = json.dumps(
            {
                "recipient": "a@b.com",
                "subject": "Hi",
                "html_template_code": "TPL",
                "message_variables": [{"key": "%K%"}],
            }
        )
        with pytest.raises(
            ValueError, match="Each message variable should have a 'value'"
        ):
            self._sanitizer().sanitize(data)

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            self._sanitizer().sanitize("not-json")

    def test_multiple_variables(self):
        data = json.dumps(
            {
                "recipient": "user@test.com",
                "subject": "Welcome",
                "html_template_code": "WELCOME",
                "message_variables": [
                    {"key": "%NAME%", "value": "Alice"},
                    {"key": "%CODE%", "value": "12345"},
                ],
            }
        )
        result = self._sanitizer().sanitize(data)
        assert len(result.message_variables) == 2
        assert result.message_variables[0].key == "%NAME%"
        assert result.message_variables[1].key == "%CODE%"
