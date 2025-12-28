"""
Prompt Rendering Utility

Handles rendering of prompt templates with placeholder substitution.
Supports safe placeholder replacement without code execution.
"""

import re
from typing import Dict, Any, Optional
from typing import Union


class PromptRenderer:
    """
    Utility for rendering prompt templates with placeholder substitution.

    Uses simple double-brace syntax: {{PLACEHOLDER_NAME}}
    Supports string replacement, conditional inclusion, and safe rendering.
    """

    PLACEHOLDER_PATTERN = re.compile(r'\{\{(\w+)\}\}')

    def __init__(self, strict_mode: bool = True):
        """
        Initialize the prompt renderer.

        Args:
            strict_mode: If True, raises error for undefined placeholders.
                        If False, leaves undefined placeholders unchanged.
        """
        self.strict_mode = strict_mode

    def render(self, template: str, **kwargs) -> str:
        """
        Render a template string with provided placeholder values.

        Args:
            template: Template string with {{PLACEHOLDER}} patterns
            **kwargs: Placeholder name-value pairs

        Returns:
            Rendered string with placeholders substituted

        Raises:
            ValueError: If strict_mode=True and placeholder has no value
        """
        def replace_placeholder(match):
            placeholder_name = match.group(1)

            if placeholder_name in kwargs:
                value = kwargs[placeholder_name]
                return self._format_value(value)
            elif self.strict_mode:
                raise ValueError(f"Undefined placeholder: {placeholder_name}")
            else:
                # Leave placeholder unchanged in non-strict mode
                return match.group(0)

        return self.PLACEHOLDER_PATTERN.sub(replace_placeholder, template)

    def render_with_context(self, template: str, context: Dict[str, Any]) -> str:
        """
        Render a template string using a context dictionary.

        Args:
            template: Template string with {{PLACEHOLDER}} patterns
            context: Dictionary containing placeholder values

        Returns:
            Rendered string with placeholders substituted
        """
        return self.render(template, **context)

    def extract_placeholders(self, template: str) -> list:
        """
        Extract all placeholder names from a template.

        Args:
            template: Template string

        Returns:
            List of placeholder names found in the template
        """
        return self.PLACEHOLDER_PATTERN.findall(template)

    def validate_placeholders(self, template: str, available_values: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate that all placeholders in template have corresponding values.

        Args:
            template: Template string
            available_values: Dictionary of available placeholder values

        Returns:
            Dictionary mapping placeholder names to whether they have values
        """
        placeholders = self.extract_placeholders(template)
        validation = {}

        for placeholder in placeholders:
            validation[placeholder] = placeholder in available_values

        return validation

    def _format_value(self, value: Any) -> str:
        """
        Format a value for insertion into the template.

        Args:
            value: Value to format

        Returns:
            Formatted string value
        """
        if value is None:
            return ""
        elif isinstance(value, str):
            return value
        elif isinstance(value, dict):
            # Handle dictionary by converting to formatted text
            return self._format_dict(value)
        elif isinstance(value, list):
            # Handle list by joining with newlines
            return "\n".join(str(item) for item in value)
        else:
            return str(value)

    def _format_dict(self, data: Dict[str, Union[str, Any]]) -> str:
        """
        Format a dictionary as key-value pairs for glossary-like content.

        Args:
            data: Dictionary to format

        Returns:
            Formatted string with key-value pairs
        """
        lines = []
        for key, value in data.items():
            if isinstance(key, str) and isinstance(value, str):
                lines.append(f"- {key}: {value}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def create_conditional(self, condition: bool, content: str) -> str:
        """
        Create conditional content that can be used in templates.

        Args:
            condition: Whether to include the content
            content: Content to include if condition is True

        Returns:
            Content if condition True, empty string otherwise
        """
        return content if condition else ""

    @staticmethod
    def escape_braces(text: str) -> str:
        """
        Escape double braces in text to prevent placeholder substitution.

        Args:
            text: Text to escape

        Returns:
            Text with braces escaped
        """
        return text.replace('{{', '\\{\\{').replace('}}', '\\}\\}')