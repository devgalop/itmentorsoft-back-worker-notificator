"""Shared test configuration.

Sets the minimum environment variables that source code reads at import time
or during test execution, so tests don't depend on a local .env file.
"""

import pytest

from src.infrastructure.env_manager.env_manager import EnvironmentVariablesConstants


@pytest.fixture(autouse=True)
def _set_required_env_vars():
    """Ensure class-level env attributes have safe defaults for every test."""
    original_sender = EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER

    if not EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER:
        EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER = "test@test.com"

    yield

    EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER = original_sender
