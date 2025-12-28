"""
Prompt Manager

High-level interface for managing prompt files, combining loading and rendering capabilities.
Provides convenient methods for common prompt operations used by translation agents.
"""

from typing import Dict, Any, Optional, List
from .loader import PromptLoader
from .renderer import PromptRenderer


class PromptManager:
    """
    High-level manager for prompt loading and rendering operations.

    Combines the functionality of PromptLoader and PromptRenderer
    to provide a convenient interface for agent developers.
    """

    def __init__(self, base_dir: Optional[str] = None, strict_mode: bool = True):
        """
        Initialize the prompt manager.

        Args:
            base_dir: Base directory for prompt files
            strict_mode: Whether to enforce placeholder validation
        """
        self.loader = PromptLoader(base_dir)
        self.renderer = PromptRenderer(strict_mode=strict_mode)

    def load_and_render(self, prompt_path: str, **kwargs) -> str:
        """
        Load a prompt file and render it with provided values.

        Args:
            prompt_path: Path to prompt file (e.g., 'translation/base.md')
            **kwargs: Placeholder values for rendering

        Returns:
            Rendered prompt string
        """
        template = self.loader.load_prompt(prompt_path)
        return self.renderer.render(template, **kwargs)

    def compose_prompt(self, *prompt_paths: str, separator: str = "\n\n", **kwargs) -> str:
        """
        Load multiple prompt files and compose them into a single prompt.

        Args:
            *prompt_paths: List of prompt file paths to compose
            separator: String to separate prompt sections
            **kwargs: Placeholder values for rendering

        Returns:
            Composed and rendered prompt string
        """
        sections = []
        for path in prompt_paths:
            if self.loader.prompt_exists(path):
                section = self.loader.load_prompt(path)
                sections.append(section)
            else:
                # In production, you might want to raise an error
                # For now, we'll skip missing files
                pass

        # Join all sections and render
        combined_template = separator.join(sections)
        return self.renderer.render(combined_template, **kwargs)

    def get_base_translation_prompt(self) -> str:
        """
        Load the base translation prompt.

        Returns:
            Base translation prompt string
        """
        return self.loader.load_prompt('translation/base.md')

    def get_glossary_prompt(self, glossary: Dict[str, str]) -> str:
        """
        Load and render the glossary prompt with provided glossary.

        Args:
            glossary: Dictionary mapping Chinese terms to English translations

        Returns:
            Rendered glossary prompt string
        """
        return self.load_and_render('translation/glossary.md', GLOSSARY=glossary)

    def get_markdown_rules_prompt(self) -> str:
        """
        Load the markdown rules prompt.

        Returns:
            Markdown rules prompt string
        """
        return self.loader.load_prompt('translation/markdown_rules.md')

    def build_complete_translation_prompt(
        self,
        glossary: Optional[Dict[str, str]] = None,
        use_provider_system: bool = False
    ) -> str:
        """
        Build a complete translation prompt with optional glossary.

        Args:
            glossary: Optional glossary dictionary for terminology control
            use_provider_system: Whether to use provider system prompt format

        Returns:
            Complete translation prompt string
        """
        if use_provider_system:
            # Use provider system prompt format
            return self._build_provider_system_prompt(glossary)
        else:
            # Use traditional format (base + optional glossary)
            return self._build_traditional_prompt(glossary)

    def _build_traditional_prompt(self, glossary: Optional[Dict[str, str]]) -> str:
        """Build prompt in traditional format (base + glossary)."""
        if glossary:
            return self.compose_prompt(
                'translation/base.md',
                'translation/glossary.md',
                GLOSSARY=glossary
            )
        else:
            return self.get_base_translation_prompt()

    def _build_provider_system_prompt(self, glossary: Optional[Dict[str, str]]) -> str:
        """Build prompt in provider system format."""
        # Prepare components
        markdown_rules = self.get_markdown_rules_prompt()

        glossary_constraints = ""
        if glossary:
            glossary_constraints = self.load_and_render(
                'translation/glossary.md',
                GLOSSARY=glossary
            )

        # Compose provider system prompt
        return self.load_and_render(
            'translation/provider_system.md',
            MARKDOWN_RULES=markdown_rules,
            GLOSSARY_CONSTRAINTS=glossary_constraints
        )

    def validate_prompt_structure(self, prompt_path: str, **kwargs) -> Dict[str, bool]:
        """
        Validate that all placeholders in a prompt have values.

        Args:
            prompt_path: Path to prompt file
            **kwargs: Available placeholder values

        Returns:
            Dictionary mapping placeholder names to validation status
        """
        template = self.loader.load_prompt(prompt_path)
        return self.renderer.validate_placeholders(template, kwargs)

    def list_available_prompts(self, directory: str = "") -> Dict[str, str]:
        """
        List all available prompt files.

        Args:
            directory: Directory to search (relative to base)

        Returns:
            Dictionary mapping prompt names to their file paths
        """
        prompt_files = self.loader.list_prompts(directory)
        return {name: str(path) for name, path in prompt_files.items()}

    def get_prompt_info(self, prompt_path: str) -> Dict[str, Any]:
        """
        Get information about a prompt file.

        Args:
            prompt_path: Path to prompt file

        Returns:
            Dictionary with prompt information
        """
        template = self.loader.load_prompt(prompt_path)
        placeholders = self.renderer.extract_placeholders(template)

        return {
            'path': prompt_path,
            'full_path': str(self.loader.base_dir / prompt_path),
            'exists': self.loader.prompt_exists(prompt_path),
            'placeholders': placeholders,
            'placeholder_count': len(placeholders),
            'content_length': len(template)
        }

    def get_rewrite_prompt(
        self,
        sentence: str,
        preceding_sentence: Optional[str] = None,
        following_sentence: Optional[str] = None,
        document_context: Optional[object] = None
    ) -> str:
        """
        Get the complete rewrite prompt for a sentence.

        Args:
            sentence: The sentence to rewrite
            preceding_sentence: Previous sentence for context
            following_sentence: Next sentence for context
            document_context: Document-level context

        Returns:
            Complete rewrite prompt string
        """
        # Load the rewrite prompt template
        template = self.loader.load_prompt('rewrite/pre_translation_rewrite.md')

        # Prepare context information
        context_info = ""
        if document_context:
            if document_context.intent:
                context_info += f"Document Intent: {document_context.intent}\n"
            if document_context.target_audience:
                context_info += f"Target Audience: {document_context.target_audience}\n"
            if document_context.tone:
                context_info += f"Tone: {document_context.tone}\n"
            if document_context.domain:
                context_info += f"Domain: {document_context.domain}\n"

        # Prepare local context
        local_context = ""
        if preceding_sentence:
            local_context += f"Previous sentence: {preceding_sentence}\n"
        if following_sentence:
            local_context += f"Next sentence: {following_sentence}\n"

        # Render the prompt
        return self.renderer.render(
            template,
            SENTENCE=sentence,
            LOCAL_CONTEXT=local_context.strip() or "None",
            DOCUMENT_CONTEXT=context_info.strip() or "None"
        )