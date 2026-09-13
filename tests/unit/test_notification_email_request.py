import json
import pytest
from pydantic import ValidationError

from src.models.notification_email_request import (
    MessageVariables,
    NotificationEmailRequest,
)

# ─── MessageVariables ────────────────────────────────────────────────────────


class TestMessageVariables:
    def test_valid_creation(self):
        mv = MessageVariables(key="%NAME%", value="Alice")
        assert mv.key == "%NAME%"
        assert mv.value == "Alice"

    def test_to_dict(self):
        mv = MessageVariables(key="%USER%", value="Bob")
        assert mv.to_dict() == {"key": "%USER%", "value": "Bob"}

    @pytest.mark.parametrize(
        "invalid_key",
        [
            "NAME",  # missing % delimiters
            "%NAME",  # missing closing %
            "NAME%",  # missing opening %
            "",  # empty
            "%%",  # empty between delimiters
            "%invalid key%",  # space not allowed by \w
        ],
    )
    def test_invalid_key_format(self, invalid_key: str):
        with pytest.raises(ValidationError):
            MessageVariables(key=invalid_key, value="val")

    def test_empty_key_raises(self):
        with pytest.raises(ValidationError):
            MessageVariables(key="", value="val")

    def test_empty_value_raises(self):
        with pytest.raises(ValidationError):
            MessageVariables(key="%K%", value="")


# ─── NotificationEmailRequest ────────────────────────────────────────────────

VALID_PAYLOAD = {
    "recipient": "alice@example.com",
    "subject": "Hello there",
    "html_template_code": "TPL",
    "message_variables": [{"key": "%NAME%", "value": "Alice"}],
}


class TestNotificationEmailRequest:
    def test_valid_creation(self):
        req = NotificationEmailRequest(**VALID_PAYLOAD)
        assert req.recipient == "alice@example.com"
        assert req.subject == "Hello there"
        assert req.html_template_code == "TPL"
        assert len(req.message_variables) == 1

    def test_empty_message_variables_allowed(self):
        data = {**VALID_PAYLOAD, "message_variables": []}
        req = NotificationEmailRequest(**data)
        assert req.message_variables == []

    # ── recipient ─────────────────────────────────────────────────────────
    @pytest.mark.parametrize(
        "bad",
        [
            "",  # empty
            "a@b",  # too short (<5)
            "x" * 255 + "@example.com",  # too long (>254)
            "not-an-email",  # no @
            "@missing-local.com",  # no local part
            "user@",  # no domain
            "user @domain.com",  # space in email
        ],
    )
    def test_invalid_recipient(self, bad: str):
        data = {**VALID_PAYLOAD, "recipient": bad}
        with pytest.raises(ValidationError):
            NotificationEmailRequest(**data)

    # ── subject ───────────────────────────────────────────────────────────
    @pytest.mark.parametrize(
        "bad",
        [
            "",  # empty
            "Hi",  # too short (<3)
            "S" * 256,  # too long (>255)
        ],
    )
    def test_invalid_subject(self, bad: str):
        data = {**VALID_PAYLOAD, "subject": bad}
        with pytest.raises(ValidationError):
            NotificationEmailRequest(**data)

    # ── html_template_code ────────────────────────────────────────────────
    @pytest.mark.parametrize(
        "bad",
        [
            "",  # empty
            "AB",  # too short (<3)
            "X" * 101,  # too long (>100)
        ],
    )
    def test_invalid_html_template_code(self, bad: str):
        data = {**VALID_PAYLOAD, "html_template_code": bad}
        with pytest.raises(ValidationError):
            NotificationEmailRequest(**data)

    # ── get_content ───────────────────────────────────────────────────────
    def test_get_content_returns_valid_json(self):
        req = NotificationEmailRequest(**VALID_PAYLOAD)
        raw = req.get_content()
        parsed = json.loads(raw)
        assert parsed["recipient"] == "alice@example.com"
        assert parsed["subject"] == "Hello there"
        assert parsed["html_template_code"] == "TPL"
        assert parsed["message_variables"] == [{"key": "%NAME%", "value": "Alice"}]

    # ── get_content implements InputMessage contract ──────────────────────
    def test_get_content_is_str(self):
        req = NotificationEmailRequest(**VALID_PAYLOAD)
        assert isinstance(req.get_content(), str)
