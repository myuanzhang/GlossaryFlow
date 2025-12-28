"""
Prompt Loading Utility

Handles loading of external prompt files from the filesystem.
Supports different prompt formats and provides error handling.
"""

import os
from pathlib import Path
from typing import Optional, Dict


class PromptLoader:
    """
    Utility for loading prompt files from the filesystem.

    Prompts are stored as text files and can be loaded by name/path.
    The loader handles file existence checks and provides helpful error messages.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the prompt loader.

        Args:
            base_dir: Base directory for prompt files. If None, uses default 'prompts/' directory.
        """
        if base_dir is None:
            # Default to prompts/ directory relative to project root
            project_root = Path(__file__).parent.parent.parent
            self.base_dir = project_root / "prompts"
        else:
            self.base_dir = Path(base_dir)

    def load_prompt(self, prompt_path: str) -> str:
        """
        Load a prompt file by path.

        Args:
            prompt_path: Path to prompt file relative to base directory (e.g., 'translation/base.md')

        Returns:
            Content of the prompt file as string

        Raises:
            FileNotFoundError: If prompt file doesn't exist
            IOError: If prompt file cannot be read
        """
        full_path = self.base_dir / prompt_path

        if not full_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {full_path}\n"
                f"Base directory: {self.base_dir}\n"
                f"Relative path: {prompt_path}"
            )

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            return content
        except IOError as e:
            raise IOError(f"Failed to read prompt file {full_path}: {str(e)}")

    def load_prompt_with_fallback(self, prompt_path: str, fallback: str) -> str:
        """
        Load a prompt file with a fallback string if file doesn't exist.

        Args:
            prompt_path: Path to prompt file relative to base directory
            fallback: Fallback prompt string to use if file doesn't exist

        Returns:
            Content of prompt file or fallback string
        """
        try:
            return self.load_prompt(prompt_path)
        except FileNotFoundError:
            return fallback

    def list_prompts(self, directory: str = "") -> Dict[str, Path]:
        """
        List all available prompt files in a directory.

        Args:
            directory: Directory relative to base directory to search

        Returns:
            Dictionary mapping prompt names to their file paths
        """
        search_dir = self.base_dir / directory
        prompts = {}

        if not search_dir.exists():
            return prompts

        for file_path in search_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.md', '.txt']:
                # Create relative path from base directory
                relative_path = file_path.relative_to(self.base_dir)
                prompts[str(relative_path)] = file_path

        return prompts

    def prompt_exists(self, prompt_path: str) -> bool:
        """
        Check if a prompt file exists.

        Args:
            prompt_path: Path to prompt file relative to base directory

        Returns:
            True if prompt file exists, False otherwise
        """
        return (self.base_dir / prompt_path).exists()

    def get_base_dir(self) -> Path:
        """
        Get the base directory for prompt files.

        Returns:
            Base directory as Path object
        """
        return self.base_dir