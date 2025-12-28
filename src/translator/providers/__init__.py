"""LLM Provider Implementations"""

from ..base import provider_registry

# Try to register providers, but handle missing dependencies gracefully
try:
    from .openai_provider import OpenAIProvider
    provider_registry.register("openai", OpenAIProvider())
except ImportError:
    # OpenAI not available, register a mock provider instead
    from ..mock_provider import MockLLMProvider
    provider_registry.register("openai", MockLLMProvider("openai", "gpt-3.5-turbo"))

try:
    from .ollama_provider import OllamaProvider
    provider_registry.register("ollama", OllamaProvider())
except ImportError:
    # Ollama not available, register a mock provider instead
    from ..mock_provider import MockLLMProvider
    provider_registry.register("ollama", MockLLMProvider("ollama", "llama2"))