import pytest
from pathlib import Path

from src.services.template_loader import TemplateLoader


class TestTemplateLoader:
    def test_load_existing_template(self, tmp_path):
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        tpl = template_dir / "welcome.html"
        tpl.write_text("<h1>Welcome</h1>", encoding="utf-8")

        loader = TemplateLoader(base_path=str(template_dir))
        content = loader.load("welcome")
        assert content == "<h1>Welcome</h1>"

    def test_load_nonexistent_template_raises(self, tmp_path):
        loader = TemplateLoader(base_path=str(tmp_path))
        with pytest.raises(FileNotFoundError, match="Template not found"):
            loader.load("missing")

    def test_custom_base_path(self, tmp_path):
        custom = tmp_path / "my_templates"
        custom.mkdir()
        (custom / "custom.html").write_text("<p>Custom</p>", encoding="utf-8")

        loader = TemplateLoader(base_path=str(custom))
        assert loader.load("custom") == "<p>Custom</p>"

    def test_default_base_path_uses_assets_templates(self):
        """Verify the default base_path resolves to assets/templates next to the module."""
        loader = TemplateLoader()
        expected_suffix = Path("assets") / "templates"
        assert loader.base_path.parts[-2:] == ("assets", "templates")

    def test_load_utf8_encoding(self, tmp_path):
        tpl_dir = tmp_path
        (tpl_dir / "utf8.html").write_text(
            "Hola \u00e1\u00e9\u00ed\u00f3\u00fa", encoding="utf-8"
        )
        loader = TemplateLoader(base_path=str(tpl_dir))
        content = loader.load("utf8")
        assert content == "Hola \u00e1\u00e9\u00ed\u00f3\u00fa"

    def test_base_path_stored_as_path_object(self, tmp_path):
        loader = TemplateLoader(base_path=str(tmp_path))
        assert isinstance(loader.base_path, Path)
