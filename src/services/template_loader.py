from pathlib import Path

MESSAGES = [
    {"template_name": "evaluation_end", "summary": "La evaluación ha sido completada."},
    {"template_name": "item_created", "summary": "Un nuevo item ha sido creado."},
]


class TemplateLoader:
    """Loads HTML templates from the assets/templates directory."""

    def __init__(self, base_path: str | None = None):
        self.base_path = (
            Path(base_path)
            if base_path
            else Path(__file__).resolve().parents[1] / "assets" / "templates"
        )

    def load(self, template_name: str) -> str:
        """Load a template by name (without .html extension).

        Args:
            template_name: The template name, e.g. "recovery_password".

        Returns:
            The template content as a string.

        Raises:
            FileNotFoundError: If the template file does not exist.
        """
        template_path = self.base_path / f"{template_name}.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text(encoding="utf-8")

    def get_summary_message(self, template_name: str) -> str:
        """Get a summary message for a given template.

        Args:
            template_name: The template name, e.g. "recovery_password".

        Returns:
            A summary message as a string.
        """
        for message in MESSAGES:
            if message["template_name"] == template_name:
                return message["summary"]
        return ""
