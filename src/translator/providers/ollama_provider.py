"""Ollama LLM Provider Implementation"""

import requests
import json
from typing import Optional
from ..base import LLMProvider
from ...config import config

class OllamaProvider(LLMProvider):
    """Ollama-based translation provider"""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or config.ollama_base_url
        self.model = model or config.ollama_model

    def translate(self, text: str, source_lang: str = "zh", target_lang: str = "en") -> str:
        """Translate text using Ollama"""
        if not self.is_configured():
            raise ValueError("Ollama provider is not configured. Please check OLLAMA_BASE_URL.")

        try:
            # Use the proper translation prompt
            prompt = self._get_translation_prompt() + f"\n\n{text}"

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 4000
                    }
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                raise RuntimeError(f"Ollama API error: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to connect to Ollama: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Translation failed: {str(e)}")

    def is_configured(self) -> bool:
        """Check if Ollama is accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def get_name(self) -> str:
        """Get provider name"""
        return "Ollama"

    def _get_translation_prompt(self) -> str:
        """Get the translation system prompt"""
        return """You are a document translation assistant.

Translate Chinese text in the following Markdown document into English.

Rules:
- Preserve all Markdown formatting exactly.
- Do NOT translate:
  - Code blocks
  - Inline code
  - URLs
  - File paths
- Do NOT add explanations or comments.
- Output only the translated Markdown content."""