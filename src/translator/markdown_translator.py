"""Markdown Document Translator"""

import re
import logging
from typing import List, Tuple, Optional
from providers.registry import provider_registry
from translator.glossary import Glossary
from core.config import config
from core.output_contract import TranslationOutputContract
from prompt import PromptManager

logger = logging.getLogger(__name__)

class MarkdownTranslator:
    """Markdown document translator with structure preservation and glossary support"""

    def __init__(self, provider_name: str = None, model_name: str = None, glossary: Optional[Glossary] = None):
        # Get provider
        provider_name = provider_name or config.provider

        # Get default model based on provider
        if not model_name:
            if provider_name == "openai" and config.openai_models:
                model_name = config.openai_models[0]
            elif provider_name == "ollama" and config.ollama_models:
                model_name = config.ollama_models[0]
            elif provider_name == "mimo" and config.mimo_models:
                model_name = config.mimo_models[0]
            elif provider_name == "deepseek" and config.deepseek_models:
                model_name = config.deepseek_models[0]
            elif provider_name == "qwen" and config.qwen_models:
                model_name = config.qwen_models[0]
            else:
                model_name = "gpt-3.5-turbo"  # Final fallback

        # Store model name for later use
        self.model_name = model_name
        self.provider_name = provider_name  # Store provider name for model type detection

        # Get provider from registry (providers are auto-registered via import)
        self.provider = provider_registry.get_or_create(provider_name, model_name)

        if not self.provider:
            available = provider_registry.list_available_providers()
            raise ValueError(f"Provider '{provider_name}' not found. Available: {available}")

        if not self.provider.is_configured():
            raise ValueError(f"Provider '{provider_name}' is not properly configured")

        self.glossary = glossary

        # Initialize prompt manager
        self.prompt_manager = PromptManager()

        # Detect model capabilities and type
        self.is_reasoning_model = self._detect_reasoning_model(model_name)
        self.model_type = self._detect_model_type(model_name, provider_name)  # 'reasoning', 'chat', or 'mt-like'

    def translate(self, markdown_text: str) -> str:
        """
        Translate markdown document while preserving structure and applying glossary

        Args:
            markdown_text: Input markdown text

        Returns:
            Translated markdown text
        """
        # Try translation with retry for failed translations
        # Only retry DeepSeek chat models, NOT mt-like models
        if self.model_type == 'chat':
            max_retries = 2
        elif self.model_type == 'reasoning':
            max_retries = 1
        else:  # mt-like
            max_retries = 1  # No retry for MT-like models

        for attempt in range(max_retries):
            result = self._translate_once(markdown_text, attempt)

            # Different validation for different model types
            if self.model_type == 'mt-like':
                # MT-like models: validate but don't retry (post-processing handles cleanup)
                # The bilingual cleanup is already done in _clean_model_output
                # Just log the final stats
                chinese_char_count = sum(1 for char in result if '\u4e00' <= char <= '\u9fff')
                chinese_ratio = chinese_char_count / len(result) if result else 0
                logger.info(f"MT-like translation final stats: {chinese_char_count} Chinese chars, ratio={chinese_ratio:.2%}")
                # Always return result (bilingual cleanup already applied)
                return result
            else:
                # DeepSeek models: validate translation occurred
                if self._validate_translation(result):
                    return result
                elif attempt < max_retries - 1:
                    logger.warning(f"Translation validation failed (attempt {attempt + 1}/{max_retries}), retrying with stronger prompt...")
                    # Will retry with modified approach
                else:
                    logger.error(f"Translation failed after {max_retries} attempts, returning original text")
                    return markdown_text

        return markdown_text  # Fallback

    def _translate_once(self, markdown_text: str, attempt: int) -> str:
        """
        Perform a single translation attempt.

        Args:
            markdown_text: Input markdown text
            attempt: Attempt number (for logging)

        Returns:
            Translated and cleaned markdown text
        """
        # Build the complete prompt with optional glossary
        prompt = self._build_complete_prompt()

        # For retry attempts, add stronger translation directive
        if attempt > 0:
            prompt = self._build_retry_prompt(prompt)

        # Combine prompt with markdown text
        full_text = f"{prompt}\n\n{markdown_text}"

        # Log translation request
        logger.info(f"Translation attempt {attempt + 1}: provider={self.provider.get_name()}, model={self.model_name}, input_length={len(markdown_text)}, prompt_length={len(prompt)}")

        # Use provider.translate which now detects full prompts
        try:
            raw_result = self.provider.translate(
                full_text,
                source_lang="zh",
                target_lang="en",
                model=self.model_name
            )

            # Log raw result
            logger.info(f"Raw translation result: length={len(raw_result)}, first_100_chars={raw_result[:100]}")

        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Return original text on error
            return markdown_text

        # Post-process to clean up model output using the output contract
        cleaned_result, metadata = TranslationOutputContract.parse_model_output(
            raw_result,
            source_text=markdown_text
        )

        # Log cleaning metadata
        logger.info(f"Output cleaning: status={metadata['status']}, "
                   f"original_len={metadata['original_length']}, "
                   f"cleaned_len={metadata['cleaned_length']}, "
                   f"removed_prefix={metadata.get('removed_prefix')}, "
                   f"has_chinese={metadata['has_chinese']}")

        # If cleaning resulted in empty content, return raw result
        if not cleaned_result.strip():
            logger.warning("Output cleaning resulted in empty content, returning raw result")
            return raw_result

        return cleaned_result

    def _build_retry_prompt(self, original_prompt: str) -> str:
        """
        Build a stronger prompt for retry attempts.

        Args:
            original_prompt: Original prompt

        Returns:
            Enhanced prompt for retry
        """
        retry_instruction = """
⚠️ IMPORTANT: You MUST translate ALL Chinese text to English.
- Your output MUST be in English language
- Do NOT repeat or copy the original Chinese text
- Every Chinese character must be translated
"""
        return f"{retry_instruction}\n{original_prompt}"

    def _validate_translation(self, translated_text: str) -> bool:
        """
        Validate that translation actually occurred (language changed).

        Args:
            translated_text: The translated text to validate

        Returns:
            True if translation appears successful
        """
        if not translated_text:
            return False

        # Count Chinese characters
        chinese_char_count = sum(1 for char in translated_text if '\u4e00' <= char <= '\u9fff')
        chinese_ratio = chinese_char_count / len(translated_text) if translated_text else 0

        logger.info(f"Translation validation: {chinese_char_count} Chinese chars, ratio={chinese_ratio:.2%}")

        # Translation is successful if less than 30% Chinese characters
        # (Allowing some Chinese for proper nouns, technical terms, etc.)
        is_valid = chinese_ratio < 0.3

        if not is_valid:
            logger.warning(f"Translation validation FAILED: {chinese_ratio:.1%} Chinese characters detected")

        return is_valid

    def _detect_reasoning_model(self, model_name: str) -> bool:
        """
        Detect if the model is a reasoning model that outputs thinking process.

        Args:
            model_name: Name of the model

        Returns:
            True if this is a reasoning model
        """
        reasoning_keywords = ['reason', 'r1', 'deepseek-reasoner', 'o1', 'o3']
        model_lower = model_name.lower()
        return any(keyword in model_lower for keyword in reasoning_keywords)

    def _detect_model_type(self, model_name: str, provider_name: str = None) -> str:
        """
        Detect the model type for appropriate prompt and validation strategy.

        Args:
            model_name: Name of the model
            provider_name: Name of the provider (optional, for additional context)

        Returns:
            Model type: 'reasoning', 'chat', or 'mt-like'
        """
        model_lower = model_name.lower()
        provider_lower = provider_name.lower() if provider_name else ""

        logger.info(f"Detecting model type for: model='{model_name}', provider='{provider_name}'")
        logger.info(f"  -> model_lower='{model_lower}', provider_lower='{provider_lower}'")

        # 1. Reasoning models (require strict output control)
        reasoning_keywords = ['reason', 'r1', 'deepseek-reasoner', 'o1', 'o3']
        if any(kw in model_lower for kw in reasoning_keywords):
            logger.info(f"Model '{model_name}' classified as 'reasoning' (matched model name)")
            return 'reasoning'

        # 2. MT-like models (traditional translation models, minimal constraints)
        # Check BOTH provider name and model name for MT-like indicators
        # NOTE: Qwen models with 'mt-' in name are NOT MT-like models, they are general LLMs
        mt_like_keywords = ['mimo', 'nmt', 'translate', 'opus-mt']

        # First check provider name (more reliable)
        if any(kw in provider_lower for kw in mt_like_keywords):
            logger.info(f"Model '{model_name}' classified as 'mt-like' (matched provider '{provider_name}')")
            return 'mt-like'

        # Then check model name, but EXCLUDE qwen models with 'mt-' prefix
        # qwen-mt-* are general LLMs, not MT-like translation models
        if 'qwen' not in model_lower and any(kw in model_lower for kw in mt_like_keywords):
            logger.info(f"Model '{model_name}' classified as 'mt-like' (matched keyword in model name)")
            return 'mt-like'

        # 3. Chat models (need translation emphasis but not strict control)
        logger.info(f"Model '{model_name}' classified as 'chat' (default)")
        return 'chat'

    def _build_complete_prompt(self) -> str:
        """
        Build the complete translation prompt including optional glossary

        Returns:
            Complete prompt string
        """
        # Get glossary dictionary if available
        glossary_dict = None
        if self.glossary and not self.glossary.is_empty():
            glossary_dict = self.glossary.get_terms()

        # Use different prompts based on model type
        logger.info(f"Building prompt for model type: {self.model_type} (model={self.model_name})")

        if self.model_type == 'reasoning':
            # Reasoning models: strict prompt to suppress thinking output
            logger.info(f"Using reasoning-focused prompt for model: {self.model_name}")
            return self.prompt_manager.build_complete_translation_prompt(
                glossary=glossary_dict,
                use_provider_system=False
            )

        elif self.model_type == 'mt-like':
            # MT-like models (Mimo, etc.): minimal, simple prompt
            logger.info(f"Using minimal MT-like prompt for model: {self.model_name}")
            return self._build_mt_like_prompt(glossary_dict)

        elif self.provider_name == 'ollama':
            # Ollama local models: use optimized prompt with clear delimiters
            logger.info(f"Using Ollama-optimized prompt for model: {self.model_name}")
            return self._build_ollama_prompt(glossary_dict)

        else:  # 'chat'
            # Chat models: emphasize translation task
            logger.info(f"Using chat-focused translation prompt for model: {self.model_name}")
            if self.prompt_manager.loader.prompt_exists('translation/base_chat.md'):
                base_prompt = self.prompt_manager.loader.load_prompt('translation/base_chat.md')
                # Add glossary if available
                if glossary_dict:
                    glossary_prompt = self.prompt_manager.load_and_render(
                        'translation/glossary.md',
                        GLOSSARY=glossary_dict
                    )
                    return f"{base_prompt}\n\n{glossary_prompt}"
                return base_prompt
            else:
                # Fallback to regular prompt
                logger.warning("base_chat.md not found, falling back to base.md")
                return self.prompt_manager.build_complete_translation_prompt(
                    glossary=glossary_dict,
                    use_provider_system=False
                )

    def _build_ollama_prompt(self, glossary_dict: Optional[dict]) -> str:
        """
        Build an optimized prompt for Ollama local models.

        Uses clear delimiters and minimal instructions to reduce prompt echo.

        Args:
            glossary_dict: Optional glossary dictionary

        Returns:
            Optimized prompt for Ollama models
        """
        # Use the new Ollama-optimized prompt template
        if self.prompt_manager.loader.prompt_exists('translation/base_ollama.md'):
            base_prompt = self.prompt_manager.loader.load_prompt('translation/base_ollama.md')

            # Add glossary if available (keep it minimal)
            if glossary_dict:
                glossary_items = [f"- {zh}: {en}" for zh, en in list(glossary_dict.items())[:20]]  # Limit to 20 terms
                glossary_section = "TERMINOLOGY:\n" + "\n".join(glossary_items)
                return f"{base_prompt}\n{glossary_section}\n"

            return base_prompt
        else:
            # Fallback to MT-like prompt
            logger.warning("base_ollama.md not found, falling back to MT-like prompt")
            return self._build_mt_like_prompt(glossary_dict)

    def _build_mt_like_prompt(self, glossary_dict: Optional[dict]) -> str:
        """
        Build a minimal, simple prompt for MT-like models (Mimo, etc.).

        These models are designed for translation and don't need heavy constraints.

        Args:
            glossary_dict: Optional glossary dictionary

        Returns:
            Simple translation prompt
        """
        # Base prompt: simple and direct with CRITICAL output constraints
        prompt = """Translate the following Markdown document from Chinese to English.

CRITICAL OUTPUT REQUIREMENTS:
- Output ONLY the English translation
- DO NOT include the original Chinese text
- DO NOT output bilingual pairs or parallel text
- DO NOT show "Chinese: ... English: ..." format
- Your output must contain ONLY English text

Preserve all Markdown formatting, code blocks, and structure.
"""

        # Add glossary if available (keep it brief)
        if glossary_dict:
            glossary_items = [f"- {zh}: {en}" for zh, en in glossary_dict.items()]
            glossary_section = "Use these translations for specific terms:\n" + "\n".join(glossary_items)
            prompt = f"{prompt}\n{glossary_section}\n"

        return prompt


def translate_markdown(input_md: str, provider: str = None, glossary: Optional[Glossary] = None) -> str:
    """
    Translate markdown content

    Args:
        input_md: Input markdown content as string
        provider: LLM provider name (optional, uses config default)
        glossary: Glossary instance for terminology control (optional)

    Returns:
        Translated markdown content
    """
    translator = MarkdownTranslator(provider, glossary)
    return translator.translate(input_md)