"""OpenAI LLM Provider Implementation"""

import openai
from typing import Optional
from ..base import LLMProvider
from ...config import config

class OpenAIProvider(LLMProvider):
    """OpenAI GPT-based translation provider"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        # If model is specified, get model-specific configuration
        if model:
            model_config = config.get_model_config(model)
            self.api_key = api_key or model_config.get('api_key') or config.openai_api_key
            self.base_url = base_url or model_config.get('base_url') or config.openai_base_url
        else:
            self.api_key = api_key or config.openai_api_key
            self.base_url = base_url or config.openai_base_url

        self.model = model or config.openai_model
        self.client = None

        if self.api_key:
            client_kwargs = {"api_key": self.api_key}
            if self.base_url:
                client_kwargs["base_url"] = self.base_url
            self.client = openai.OpenAI(**client_kwargs)

    def translate(self, text: str, source_lang: str = "zh", target_lang: str = "en") -> str:
        """Translate text using OpenAI GPT"""
        if not self.is_configured():
            if self.base_url:
                raise ValueError(f"OpenAI-compatible provider is not configured. Please set OPENAI_API_KEY. (Base URL: {self.base_url})")
            else:
                raise ValueError("OpenAI provider is not configured. Please set OPENAI_API_KEY.")

        try:
            # Check if text contains a system prompt and user content
            if "\n\n" in text and text.strip().startswith("You are"):
                # Split system prompt and user content
                parts = text.split("\n\n", 1)
                if len(parts) == 2:
                    system_prompt, user_content = parts
                    messages = [
                        {"role": "system", "content": system_prompt.strip()},
                        {"role": "user", "content": user_content.strip()}
                    ]
                else:
                    messages = [{"role": "user", "content": text}]
            else:
                # Use the translation-specific system prompt
                messages = [
                    {"role": "system", "content": self._get_translation_prompt()},
                    {"role": "user", "content": text}
                ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=4000
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"Translation failed: {str(e)}")

    def is_configured(self) -> bool:
        """Check if OpenAI API key is configured"""
        return self.api_key is not None and self.client is not None

    def get_name(self) -> str:
        """Get provider name"""
        if self.base_url:
            return f"OpenAI-compatible ({self.base_url})"
        return "OpenAI"

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