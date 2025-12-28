"""Glossary/Terminology Management"""

import json
import os
from typing import Dict, Optional, Union
from pathlib import Path

class Glossary:
    """
    Glossary for managing terminology translations (Chinese to English)
    """

    def __init__(self, terms: Optional[Dict[str, str]] = None):
        """
        Initialize glossary with terms dictionary

        Args:
            terms: Dictionary mapping Chinese terms to English translations
        """
        self.terms = terms or {}

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'Glossary':
        """
        Load glossary from JSON or YAML file

        Args:
            file_path: Path to glossary file

        Returns:
            Glossary instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Glossary file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    return cls._load_yaml(f)
                elif file_path.suffix.lower() == '.json':
                    return cls._load_json(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")
        except Exception as e:
            raise ValueError(f"Failed to load glossary from {file_path}: {str(e)}")

    @classmethod
    def _load_json(cls, file_handle) -> 'Glossary':
        """Load glossary from JSON file"""
        data = json.load(file_handle)

        if not isinstance(data, dict):
            raise ValueError("Glossary file must contain a dictionary")

        # Validate that all keys and values are strings
        for key, value in data.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("All glossary keys and values must be strings")

        return cls(data)

    @classmethod
    def _load_yaml(cls, file_handle) -> 'Glossary':
        """Load glossary from YAML file"""
        try:
            import yaml
        except ImportError:
            raise ValueError("PyYAML is required for YAML glossary files. Install with: pip install PyYAML")

        data = yaml.safe_load(file_handle)

        if not isinstance(data, dict):
            raise ValueError("Glossary file must contain a dictionary")

        # Validate that all keys and values are strings
        for key, value in data.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("All glossary keys and values must be strings")

        return cls(data)

    def add_term(self, chinese_term: str, english_term: str):
        """
        Add or update a term in the glossary

        Args:
            chinese_term: Chinese term
            english_term: English translation
        """
        self.terms[chinese_term] = english_term

    def get_translation(self, chinese_term: str) -> Optional[str]:
        """
        Get English translation for a Chinese term

        Args:
            chinese_term: Chinese term to translate

        Returns:
            English translation if found, None otherwise
        """
        return self.terms.get(chinese_term)

    def is_empty(self) -> bool:
        """
        Check if glossary is empty

        Returns:
            True if no terms are defined
        """
        return len(self.terms) == 0

    def to_prompt_string(self) -> str:
        """
        Convert glossary to prompt-friendly string format

        Returns:
            Formatted string for LLM prompt
        """
        if self.is_empty():
            return ""

        lines = []
        for chinese, english in sorted(self.terms.items()):
            lines.append(f"- {chinese}: {english}")

        return "\n".join(lines)

    def get_term_count(self) -> int:
        """
        Get number of terms in glossary

        Returns:
            Number of defined terms
        """
        return len(self.terms)

    def get_terms(self) -> Dict[str, str]:
        """
        Get copy of all terms

        Returns:
            Dictionary of Chinese to English terms
        """
        return self.terms.copy()

    def __len__(self) -> int:
        """Return number of terms"""
        return len(self.terms)

    def __contains__(self, chinese_term: str) -> bool:
        """Check if term exists in glossary"""
        return chinese_term in self.terms

    def __repr__(self) -> str:
        """String representation"""
        return f"Glossary(terms={self.get_term_count()})"