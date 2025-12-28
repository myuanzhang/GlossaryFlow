"""Configuration Management"""

import os
from typing import Optional

# Load environment variables if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

class Config:
    """Configuration management for document translation"""

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "openai")

        # OpenAI Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_models = self._parse_models(os.getenv("OPENAI_MODELS", os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")))
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")  # For OpenAI-compatible third-party APIs

        # Model-specific configurations
        self.model_configs = self._load_model_configs()

        # Ollama Configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_models = self._parse_models(os.getenv("OLLAMA_MODELS", os.getenv("OLLAMA_MODEL", "llama2")))

        # Glossary Configuration
        self.default_glossary_path = os.getenv("DEFAULT_GLOSSARY_PATH", "")

    def _load_model_configs(self) -> dict[str, dict[str, str]]:
        """Load model-specific configurations from environment variables"""
        model_configs = {}

        for model in self.openai_models:
            config = {}

            # Determine config prefix based on model name
            if model.startswith('mimo'):
                prefix = 'MIMO'
            elif model.startswith('glm'):
                prefix = 'GLM'
            elif model.startswith('qwen'):
                prefix = 'QWEN'
            else:
                prefix = 'OPENAI'  # default prefix

            # Get model-specific API key and base URL
            api_key = os.getenv(f"{prefix}_API_KEY") or self.openai_api_key
            base_url = os.getenv(f"{prefix}_BASE_URL") or self.openai_base_url

            config['api_key'] = api_key
            config['base_url'] = base_url
            config['prefix'] = prefix

            model_configs[model] = config

        return model_configs

    def _parse_models(self, models_str: str) -> list[str]:
        """Parse comma-separated model string into list"""
        if not models_str:
            return []

        # Split by comma and clean whitespace
        models = [model.strip() for model in models_str.split(',')]
        # Remove empty strings and duplicates
        return [model for model in models if model]

    def get_provider_models(self, provider: str) -> list[str]:
        """Get available models for a provider"""
        if provider == "openai":
            return self.openai_models
        elif provider == "ollama":
            return self.ollama_models
        return []

    def get_model_config(self, model_name: str) -> dict[str, str]:
        """Get configuration for a specific model"""
        return self.model_configs.get(model_name, {
            'api_key': self.openai_api_key,
            'base_url': self.openai_base_url,
            'prefix': 'OPENAI'
        })

    def get_provider_models_with_config(self, provider: str) -> list[dict[str, str]]:
        """Get models with their configurations for a provider"""
        if provider == "openai":
            models_with_config = []
            for model in self.openai_models:
                config = self.model_configs.get(model, {})
                models_with_config.append({
                    'name': model,
                    'api_key': config.get('api_key', ''),
                    'base_url': config.get('base_url', ''),
                    'prefix': config.get('prefix', 'OPENAI'),
                    'configured': bool(config.get('api_key'))
                })
            return models_with_config
        elif provider == "ollama":
            return [{'name': model, 'configured': True} for model in self.ollama_models]
        return []

    # Backward compatibility properties
    @property
    def openai_model(self) -> str:
        """Get first OpenAI model for backward compatibility"""
        return self.openai_models[0] if self.openai_models else ""

    @property
    def ollama_model(self) -> str:
        """Get first Ollama model for backward compatibility"""
        return self.ollama_models[0] if self.ollama_models else ""

    def is_openai_configured(self) -> bool:
        """Check if OpenAI provider is properly configured"""
        return bool(self.openai_api_key)

    def is_ollama_configured(self) -> bool:
        """Check if Ollama provider is properly configured"""
        return True  # Ollama is local, always available if URL is set

    def validate(self) -> bool:
        """Validate current configuration"""
        if self.provider == "openai":
            return self.is_openai_configured()
        elif self.provider == "ollama":
            return self.is_ollama_configured()
        else:
            return False

# Global config instance
config = Config()