"""Integration tests for TemplateLoader using actual template files on disk."""

import pytest
import tempfile
import os
from pathlib import Path

from src.services.template_loader import TemplateLoader


def _write_template(directory: Path, name: str, content: str) -> Path:
    """Write a template file and return its path."""
    path = directory / f"{name}.html"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def temp_templates_dir():
    """Create a temporary directory with test template files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def loader_with_temp(temp_templates_dir):
    """TemplateLoader pointed at a temporary templates directory."""
    return TemplateLoader(base_path=str(temp_templates_dir))


def test_load_existing_template(loader_with_temp, temp_templates_dir):
    """load() reads the content of an existing .html template file."""
    _write_template(temp_templates_dir, "test_email", "<p>Hello {{name}}</p>")
    content = loader_with_temp.load("test_email")
    assert content == "<p>Hello {{name}}</p>"


def test_load_unicode_template(loader_with_temp, temp_templates_dir):
    """load() reads templates containing unicode characters (utf-8)."""
    _write_template(temp_templates_dir, "unicode", "<p>Ñoño & café ☕</p>")
    content = loader_with_temp.load("unicode")
    assert "Ñoño" in content
    assert "☕" in content


def test_load_multiline_template(loader_with_temp, temp_templates_dir):
    """load() preserves line breaks and whitespace in templates."""
    html = (
        "<html>\n"
        "  <body>\n"
        "    <h1>Welcome</h1>\n"
        "    <p>Hello %name%</p>\n"
        "  </body>\n"
        "</html>"
    )
    _write_template(temp_templates_dir, "multiline", html)
    content = loader_with_temp.load("multiline")
    assert content == html


def test_load_nonexistent_template_raises(loader_with_temp):
    """load() raises FileNotFoundError when the template does not exist."""
    with pytest.raises(FileNotFoundError, match="Template not found"):
        loader_with_temp.load("missing_template")


def test_load_real_otp_template():
    """load() reads the actual otp.html template from the assets/templates directory."""
    loader = TemplateLoader()
    content = loader.load("otp")
    assert isinstance(content, str)
    assert len(content) > 0


def test_load_real_recovery_password_template():
    """load() reads the actual recovery_password.html template."""
    loader = TemplateLoader()
    content = loader.load("recovery_password")
    assert isinstance(content, str)
    assert len(content) > 0


def test_load_real_user_created_template():
    """load() reads the actual user_created.html template."""
    loader = TemplateLoader()
    content = loader.load("user_created")
    assert isinstance(content, str)
    assert len(content) > 0


def test_load_real_item_created_template():
    """load() reads the actual item_created.html template."""
    loader = TemplateLoader()
    content = loader.load("item_created")
    assert isinstance(content, str)
    assert len(content) > 0


def test_load_all_real_templates():
    """load() reads every template in the assets/templates directory successfully."""
    loader = TemplateLoader()
    for name in ["otp", "recovery_password", "user_created", "item_created"]:
        content = loader.load(name)
        assert len(content) > 0, f"Template {name} should not be empty"


def test_default_base_path_points_to_assets_templates():
    """TemplateLoader without base_path resolves to src/assets/templates."""
    loader = TemplateLoader()
    expected_suffix = Path("assets") / "templates"
    assert loader.base_path.name == "templates"
    assert loader.base_path.parent.name == "assets"


def test_load_nonexistent_real_template_raises():
    """load() raises FileNotFoundError for a template name that does not exist in the real directory."""
    loader = TemplateLoader()
    with pytest.raises(FileNotFoundError):
        loader.load("does_not_exist_at_all")
