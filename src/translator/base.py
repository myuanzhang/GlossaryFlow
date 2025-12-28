"""LLM Provider Abstract Interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    @abstractmethod
    def translate(self, text: str, source_lang: str = "zh", target_lang: str = "en") -> str:
        """
        Translate text from source language to target language

        Args:
            text: The text to translate
            source_lang: Source language code (default: "zh" for Chinese)
            target_lang: Target language code (default: "en" for English)

        Returns:
            Translated text
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the provider is properly configured

        Returns:
            True if configured and ready to use, False otherwise
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the provider name

        Returns:
            Provider name as string
        """
        pass

class ProviderRegistry:
    """Registry for managing LLM providers"""

    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}

    def register(self, name: str, provider: LLMProvider):
        """Register a new provider"""
        self._providers[name.lower()] = provider

    def get(self, name: str) -> Optional[LLMProvider]:
        """Get a provider by name"""
        return self._providers.get(name.lower())

    def get_or_create(self, provider_name: str, model: Optional[str] = None) -> Optional[LLMProvider]:
        """Get an existing provider or create a new one with the specified model"""
        provider_name = provider_name.lower()

        # For OpenAI, try to create new instances with different models
        if provider_name == "openai":
            try:
                from .providers.openai_provider import OpenAIProvider
                return OpenAIProvider(model=model)
            except ImportError:
                # Fall back to mock provider
                from .mock_provider import MockLLMProvider
                return MockLLMProvider("openai", model or "gpt-3.5-turbo")

        # For Ollama, create new instance with model
        elif provider_name == "ollama":
            try:
                from .providers.ollama_provider import OllamaProvider
                return OllamaProvider(model=model)
            except ImportError:
                # Fall back to mock provider
                from .mock_provider import MockLLMProvider
                return MockLLMProvider("ollama", model or "llama2")

        # For mock provider, create new instance
        elif provider_name == "mock":
            from .mock_provider import MockLLMProvider
            return MockLLMProvider("mock", model or "mock-model")

        # Return existing provider if no model-specific creation needed
        return self.get(provider_name)

    def list_providers(self) -> list[str]:
        """List all registered provider names"""
        return list(self._providers.keys())

# Global provider registry
provider_registry = ProviderRegistry()