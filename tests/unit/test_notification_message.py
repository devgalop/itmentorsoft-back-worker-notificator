import json
import pytest
from unittest.mock import patch, MagicMock

from src.models.notification_message import NotificationMessageVariables

# ─── NotificationMessageVariables ────────────────────────────────────────────


class TestNotificationMessageVariables:
    def test_to_dict(self):
        mv = NotificationMessageVariables(key="%NAME%", value="Alice")
        assert mv.to_dict() == {"key": "%NAME%", "value": "Alice"}

    def test_to_json(self):
        mv = NotificationMessageVariables(key="%USER%", value="Bob")
        result = mv.to_json()
        parsed = json.loads(result)
        assert parsed == {"key": "%USER%", "value": "Bob"}


# ─── NotificationMessage ─────────────────────────────────────────────────────
# NotificationMessage inherits from common_py_aws.PublishMessageRequest.
# We mock that base class BEFORE the module is imported so the real methods
# on NotificationMessage are used (not overridden by MagicMock).

VALID_VARS = [
    NotificationMessageVariables(key="%NAME%", value="Alice"),
]

VALID_RECIPIENT = "alice@example.com"
VALID_SUBJECT = "Hello"
VALID_TEMPLATE = "TPL"


class _FakePublishRequest:
    """Minimal stub that satisfies the inheritance requirement without
    overriding any methods."""

    pass


def _import_with_mock():
    """Import NotificationMessage with a fake base class for PublishMessageRequest."""
    with patch.dict(
        "sys.modules",
        {"common_py_aws": MagicMock(PublishMessageRequest=_FakePublishRequest)},
    ):
        import importlib
        import src.models.notification_message as nm

        importlib.reload(nm)
        return nm


class TestNotificationMessage:
    @pytest.fixture(autouse=True)
    def _setup(self):
        """Reload the module under a mocked base class before each test."""
        nm = _import_with_mock()
        self.NotificationMessage = nm.NotificationMessage

    def _make(self, vars_list=None):
        return self.NotificationMessage(
            recipient=VALID_RECIPIENT,
            subject=VALID_SUBJECT,
            html_template_code=VALID_TEMPLATE,
            message_variables=vars_list or VALID_VARS,
        )

    def test_to_dict(self):
        msg = self._make()
        d = msg.to_dict()
        assert d["recipient"] == VALID_RECIPIENT
        assert d["subject"] == VALID_SUBJECT
        assert d["html_template_code"] == VALID_TEMPLATE
        assert d["message_variables"] == [{"key": "%NAME%", "value": "Alice"}]

    def test_to_json(self):
        msg = self._make()
        parsed = json.loads(msg.to_json())
        assert parsed["recipient"] == VALID_RECIPIENT

    def test_get_url(self, monkeypatch):
        monkeypatch.setattr(
            "src.models.notification_message.EnvironmentVariablesConstants.AWS_SQS_NOTIFY_QUEUE_URL",
            "https://sqs.test/queue",
        )
        msg = self._make()
        assert msg.get_url() == "https://sqs.test/queue"

    def test_get_message_returns_json(self):
        msg = self._make()
        parsed = json.loads(msg.get_message())
        assert parsed["subject"] == VALID_SUBJECT

    def test_message_variables_serialise_correctly(self):
        vars_list = [
            NotificationMessageVariables(key="%A%", value="1"),
            NotificationMessageVariables(key="%B%", value="2"),
        ]
        msg = self._make(vars_list=vars_list)
        d = msg.to_dict()
        assert len(d["message_variables"]) == 2
        assert d["message_variables"][0] == {"key": "%A%", "value": "1"}
        assert d["message_variables"][1] == {"key": "%B%", "value": "2"}
