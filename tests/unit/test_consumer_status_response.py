import pytest

from src.models.consumer_status_response import ConsumerStatusResponse


class TestConsumerStatusResponse:
    def test_valid_enabled(self):
        resp = ConsumerStatusResponse(is_enabled=True, message="Active")
        assert resp.is_enabled is True
        assert resp.message == "Active"

    def test_valid_disabled(self):
        resp = ConsumerStatusResponse(is_enabled=False, message="Paused")
        assert resp.is_enabled is False
        assert resp.message == "Paused"

    def test_field_access(self):
        resp = ConsumerStatusResponse(is_enabled=True, message="Running")
        assert resp.is_enabled
        assert resp.message == "Running"

    def test_model_fields(self):
        resp = ConsumerStatusResponse(is_enabled=False, message="")
        assert resp.model_fields_set == {"is_enabled", "message"}

    def test_empty_message_allowed(self):
        resp = ConsumerStatusResponse(is_enabled=True, message="")
        assert resp.message == ""
