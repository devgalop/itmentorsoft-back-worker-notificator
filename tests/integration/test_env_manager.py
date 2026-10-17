"""Integration tests for EnvironmentVariablesConstants.validate_mandatory_env_vars()."""

import os
import pytest
from unittest.mock import patch

from src.infrastructure.env_manager.env_manager import EnvironmentVariablesConstants


def test_validate_mandatory_env_vars_passes_when_all_set():
    """validate_mandatory_env_vars does not raise when all mandatory vars are set."""
    fake_env = {
        var: "test_value" for var in EnvironmentVariablesConstants._mandatory_env_vars
    }

    with patch.dict(os.environ, fake_env, clear=False):
        # Should not raise
        EnvironmentVariablesConstants.validate_mandatory_env_vars()


def test_validate_mandatory_env_vars_raises_when_one_missing():
    """validate_mandatory_env_vars raises EnvironmentError when a mandatory var is missing."""
    # Set all vars except BREVO_API_KEY
    fake_env = {
        var: "test_value" for var in EnvironmentVariablesConstants._mandatory_env_vars
    }
    fake_env.pop("BREVO_API_KEY")

    with patch.dict(os.environ, fake_env, clear=True):
        with pytest.raises(EnvironmentError, match="BREVO_API_KEY"):
            EnvironmentVariablesConstants.validate_mandatory_env_vars()


def test_validate_mandatory_env_vars_raises_with_correct_message():
    """validate_mandatory_env_vars includes the variable name in the error message."""
    fake_env = {
        var: "test_value" for var in EnvironmentVariablesConstants._mandatory_env_vars
    }
    fake_env.pop("DATABASE_HOST")

    with patch.dict(os.environ, fake_env, clear=True):
        with pytest.raises(EnvironmentError, match="DATABASE_HOST"):
            EnvironmentVariablesConstants.validate_mandatory_env_vars()


def test_validate_mandatory_env_vars_raises_on_empty_string():
    """validate_mandatory_env_vars raises when a mandatory var is set to empty string."""
    fake_env = {
        var: "test_value" for var in EnvironmentVariablesConstants._mandatory_env_vars
    }
    fake_env["AWS_REGION"] = ""

    with patch.dict(os.environ, fake_env, clear=True):
        with pytest.raises(EnvironmentError, match="AWS_REGION"):
            EnvironmentVariablesConstants.validate_mandatory_env_vars()


def test_validate_mandatory_env_vars_checks_first_missing_var():
    """validate_mandatory_env_vars reports the first missing variable in the list."""
    # Clear all mandatory vars
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(EnvironmentError) as exc_info:
            EnvironmentVariablesConstants.validate_mandatory_env_vars()
        # ENVIRONMENT is first in the mandatory list
        assert "ENVIRONMENT" in str(exc_info.value)
