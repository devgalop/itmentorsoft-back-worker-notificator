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
    original_db_user = EnvironmentVariablesConstants.DATABASE_USER
    original_db_password = EnvironmentVariablesConstants.DATABASE_PASSWORD
    original_db_host = EnvironmentVariablesConstants.DATABASE_HOST
    original_db_name = EnvironmentVariablesConstants.DATABASE_NAME

    if not EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER:
        EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER = "test@test.com"
    if not EnvironmentVariablesConstants.DATABASE_USER:
        EnvironmentVariablesConstants.DATABASE_USER = "test_user"
    if not EnvironmentVariablesConstants.DATABASE_PASSWORD:
        EnvironmentVariablesConstants.DATABASE_PASSWORD = "test_password"
    if not EnvironmentVariablesConstants.DATABASE_HOST:
        EnvironmentVariablesConstants.DATABASE_HOST = "localhost"
    if not EnvironmentVariablesConstants.DATABASE_NAME:
        EnvironmentVariablesConstants.DATABASE_NAME = "test_db"

    yield

    EnvironmentVariablesConstants.EMAIL_DEFAULT_SENDER = original_sender
    EnvironmentVariablesConstants.DATABASE_USER = original_db_user
    EnvironmentVariablesConstants.DATABASE_PASSWORD = original_db_password
    EnvironmentVariablesConstants.DATABASE_HOST = original_db_host
    EnvironmentVariablesConstants.DATABASE_NAME = original_db_name
