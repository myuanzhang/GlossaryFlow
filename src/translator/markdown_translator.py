"""Markdown Document Translator"""

import re
import logging
from typing import List, Tuple, Optional
from providers.registry import provider_registry
from translator.glossary import Glossary
from core.config import config
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

        # Post-process to clean up model output
        cleaned_result = self._clean_model_output(raw_result)

        # Log cleaned result
        logger.info(f"Cleaned translation result: length={len(cleaned_result)}, first_100_chars={cleaned_result[:100]}")

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

    def _clean_model_output(self, raw_output: str) -> str:
        """
        Clean up model output by removing prompt content and prefixes

        Uses different strategies based on model type:
        - MT-like: Minimal cleaning (trust the model)
        - Chat: Standard cleaning
        - Reasoning: Aggressive cleaning (remove thinking, etc.)

        Args:
            raw_output: Raw output from the LLM

        Returns:
            Cleaned translated markdown content
        """
        # If output is empty or very short, return as-is
        if not raw_output or len(raw_output.strip()) < 10:
            return raw_output

        # MT-like models: special cleaning to remove Chinese lines if present
        if self.model_type == 'mt-like':
            logger.info("MT-like model: using bilingual content removal strategy")
            # First, try to remove Chinese lines if model output bilingual content
            cleaned = self._remove_chinese_lines_from_bilingual(raw_output)
            # Then do basic final cleanup
            return self._final_cleanup(cleaned)

        original_length = len(raw_output)

        # Strategy 0: Remove <thinking> tags and content (DeepSeek R1, etc.)
        cleaned_output = self._remove_thinking_tags(raw_output)
        had_thinking_tags = cleaned_output != raw_output
        if had_thinking_tags:
            logger.info(f"Removed <thinking> tags: original_len={len(raw_output)}, cleaned_len={len(cleaned_output)}")
            raw_output = cleaned_output

        # Detect if output still contains reasoning patterns
        has_reasoning = self._detect_reasoning(raw_output)

        # If no thinking tags were found and no reasoning detected, use gentle cleaning
        # This preserves the full translation content
        if not had_thinking_tags and not has_reasoning:
            logger.info("No reasoning detected, using gentle pattern-based cleanup")
            result = self._clean_by_patterns(raw_output)
            result = self._final_cleanup(result)

            # If pattern-based resulted in too short content, return original
            if len(result) < original_length * 0.5:
                logger.warning(f"Pattern-based cleaning removed too much content ({len(result)}/{original_length}), returning original with minimal cleanup")
                result = self._final_cleanup(raw_output)

            return result

        # Reasoning detected: use aggressive cleaning strategies
        lines = raw_output.split('\n')

        # Strategy 1: Try separator detection first (least aggressive)
        separator_result = self._clean_by_separator(raw_output)
        if separator_result and len(separator_result) > 10:
            logger.info(f"Output cleaning: Used separator detection, result_length={len(separator_result)}")
            result = separator_result
        # Strategy 2: Try reverse search (more aggressive)
        elif (reverse_result := self._clean_by_reverse_search(lines)) and len(reverse_result) > 10:
            logger.info(f"Output cleaning: Used reverse search, result_length={len(reverse_result)}")
            result = reverse_result
        # Strategy 3: Fall back to pattern-based detection
        else:
            result = self._clean_by_patterns(raw_output)

        # Final cleanup
        result = self._final_cleanup(result)

        return result

    def _detect_reasoning(self, text: str) -> bool:
        """
        Detect if the output contains reasoning/thinking content.

        This helps us decide whether to use aggressive cleaning strategies.

        Args:
            text: Text to check

        Returns:
            True if reasoning patterns are detected
        """
        if not text:
            return False

        # Strong indicators of reasoning content
        strong_reasoning_indicators = [
            '<thinking>',
            '<analysis>',
            '<reasoning>',
            'i will translate',
            'i need to translate',
            'let me translate',
            'step 1:',
            'step 2:',
            'first, i will',
            'my approach is to',
            'translation strategy:',
            'here is my plan'
        ]

        lower_text = text.lower()
        for indicator in strong_reasoning_indicators:
            if indicator in lower_text:
                return True

        # Check for numbered reasoning steps at the beginning
        lines = text.split('\n')
        reasoning_line_count = 0
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            stripped = line.strip()
            # Numbered list like "1.", "2.", "3." in first few lines
            if stripped and stripped[0].isdigit() and (stripped[1] == '.' or stripped[1:3] == '. '):
                reasoning_line_count += 1

        # If we have 3+ numbered steps at the beginning, it's likely reasoning
        if reasoning_line_count >= 3:
            return True

        return False

    def _remove_thinking_tags(self, text: str) -> str:
        """
        Remove <thinking> tags and their content from the output.

        This is a defensive measure for reasoning models that may output
        thinking process in the content field instead of reasoning_content.

        Args:
            text: Text that may contain <thinking> tags

        Returns:
            Text with thinking tags removed
        """
        if not text:
            return text

        # Remove <thinking>...</thinking> blocks (multiline)
        thinking_pattern = r'<thinking>.*?</thinking>'
        cleaned = re.sub(thinking_pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove <analysis>...</analysis> blocks (multiline)
        analysis_pattern = r'<analysis>.*?</analysis>'
        cleaned = re.sub(analysis_pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Remove <reasoning>...</reasoning> blocks (multiline)
        reasoning_pattern = r'<reasoning>.*?</reasoning>'
        cleaned = re.sub(reasoning_pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)

        # Clean up extra whitespace that may result from tag removal
        lines = cleaned.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:  # Keep non-empty lines
                cleaned_lines.append(line)

        result = '\n'.join(cleaned_lines).strip()
        return result

    def _clean_by_reverse_search(self, lines: list[str]) -> str:
        """
        Clean output by searching from the end backwards to find actual translation content.

        This is effective for models (like Deepseek) that output reasoning first,
        then the actual translation at the end.

        WARNING: This is a last-resort aggressive strategy and should only be used
        when reasoning is explicitly detected.
        """
        if not lines:
            return ""

        # Start from the end and work backwards
        # Find the last line that looks like actual content (not reasoning)
        content_end_idx = len(lines) - 1
        content_start_idx = -1

        # Skip empty lines at the end
        while content_end_idx >= 0 and not lines[content_end_idx].strip():
            content_end_idx -= 1

        # Now work backwards to find where the actual content starts
        # Look for patterns that indicate we're still in reasoning
        reasoning_patterns = [
            'i will translate',
            'i need to',
            'let me',
            'first, i',
            'step ',
            'finally,',
            'in summary',
            'to summarize',
            'break down',
            'identify all',
            'translate each',
            'ensure that',
            'making sure',
            'checking that',
            'note:',
            'important:',
            'the document',
            'the user',
            'the text',
            'looking at',
            'here is what i will do',
            'my approach',
            'my strategy'
        ]

        # Only search in the first 30% of the document for reasoning
        # This prevents incorrectly removing numbered lists from actual content
        search_limit = max(0, int(len(lines) * 0.3))

        for i in range(content_end_idx, -1, -1):
            line = lines[i].strip()

            # Stop searching if we've gone too far back (past 30% of document)
            if i < search_limit:
                break

            if not line:
                continue

            lower = line.lower()

            # Check if this line contains reasoning patterns
            is_reasoning = any(pattern in lower for pattern in reasoning_patterns)

            # Check if this is a numbered list item - ONLY if near the beginning
            # This prevents removing actual numbered lists from the content
            is_numbered = False
            if line and line[0].isdigit() and (line[1] == '.' or line[1:3] == '. '):
                # Only treat as reasoning if it's in the first 20% of lines
                is_numbered = i < len(lines) * 0.2

            # Check if this is a short bullet point (likely reasoning)
            is_short_bullet = (line.startswith('- ') or line.startswith('* ')) and len(line) < 100

            if is_reasoning or is_numbered or is_short_bullet:
                # This is still reasoning, content starts after this
                content_start_idx = i + 1
                break

        # If we didn't find a clear reasoning section, return empty to signal "use different strategy"
        if content_start_idx == -1:
            logger.info("Reverse search: No clear reasoning section found, returning empty")
            return ""

        if content_start_idx >= 0 and content_start_idx <= content_end_idx:
            result = '\n'.join(lines[content_start_idx:content_end_idx + 1]).strip()
            if len(result) > 50:  # Only return if substantial content
                logger.info(f"Reverse search: Extracted lines {content_start_idx}-{content_end_idx}, length={len(result)}")
                return result

        return ""

    def _clean_by_separator(self, raw_output: str) -> str:
        """
        Clean output by detecting separators (---, ===, etc.)

        Models often separate their intro text from actual content with separators.
        """
        lines = raw_output.split('\n')

        # Find separator line
        separator_idx = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Common separator patterns
            if stripped in ['---', '===', '***', '___']:
                separator_idx = i
                break

        if separator_idx >= 0 and separator_idx < len(lines) - 1:
            # Found separator, return everything after it
            result = '\n'.join(lines[separator_idx + 1:]).strip()
            if result and len(result) > 10:
                return result

        # No separator found, try to find where reasoning ends and actual content begins
        # Look for patterns like:
        # - "Let's write the translation."
        # - "Here's the translation:"
        # - "Translation:" followed by content
        content_start_idx = -1
        reasoning_end_patterns = [
            "let's write the translation",
            "let's translate",
            "here's the translation",
            "translation:",
            "we will translate",
            "let's break down",
            "we are to output"
        ]

        for i, line in enumerate(lines):
            lower = line.strip().lower()
            if any(pattern in lower for pattern in reasoning_end_patterns):
                # Found the end of reasoning, look for actual content after this
                # Skip a few lines to avoid transition text
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].strip() and len(lines[j].strip()) > 20:
                        content_start_idx = j
                        break
                break

        if content_start_idx >= 0:
            result = '\n'.join(lines[content_start_idx:]).strip()
            if result and len(result) > 10:
                logger.info(f"Found content after reasoning, start_idx={content_start_idx}")
                return result

        # No separator found, try finding double newline + content
        double_newline_idx = -1
        for i in range(len(lines) - 2):
            # Check if current and next line are empty
            if not lines[i].strip() and not lines[i + 1].strip() and lines[i + 2].strip():
                # Found pattern: empty, empty, content
                next_line = lines[i + 2].strip()
                # Check if next line looks like content (not intro)
                if next_line and not self._is_intro_line(next_line):
                    double_newline_idx = i + 2
                    break

        if double_newline_idx >= 0:
            result = '\n'.join(lines[double_newline_idx:]).strip()
            if result and len(result) > 10:
                return result

        return ""

    def _clean_by_patterns(self, raw_output: str) -> str:
        """
        Clean output by detecting and skipping intro patterns
        """
        lines = raw_output.split('\n')

        # Find the actual content by looking for common patterns
        content_start_idx = 0

        # Patterns that indicate we're still in the prompt section or introductory text
        prompt_patterns = [
            'you are a professional translator',
            'translate all chinese',
            'important requirements',
            'preserve all markdown',
            'do not translate:',
            'headings and paragraphs',
            'table content and',
            'list items',
            'image alt text',
            'code inside code blocks',
            'inline code content',
            'urls',
            'file paths',
            '- headings',
            '- table',
            '- list',
            '- code',
            '- preserve',
            # Chinese intro patterns
            '这是您提供的',
            '以下是',
            '好的，这是',
            'markdown 文档',
            '英文翻译',
            '中文翻译'
        ]

        # Find where actual content starts
        found_content = False
        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                continue

            # Check if this is an intro line
            if self._is_intro_line(stripped, prompt_patterns):
                continue

            # This might be real content
            # Relaxed check: if it starts with # or is long enough
            if stripped.startswith('#') or len(stripped) > 10:
                content_start_idx = i
                found_content = True
                break

        # Extract content
        result = '\n'.join(lines[content_start_idx:]).strip()

        # Debug logging
        logger.info(f"Output cleaning (pattern-based): found_content={found_content}, start_idx={content_start_idx}, total_lines={len(lines)}, result_length={len(result)}")

        # If result is empty or too short after cleaning, return original
        if not result or len(result) < 10:
            logger.warning(f"Output cleaning resulted in insufficient content (len={len(result)}), returning raw")
            return raw_output

        return result

    def _is_intro_line(self, line: str, patterns: list[str] = None) -> bool:
        """
        Detect if a line is an intro/prompt line rather than actual content

        Args:
            line: Line to check
            patterns: Optional list of patterns to match against

        Returns:
            True if this is likely an intro line
        """
        if not line:
            return False

        lower = line.lower()

        # Check against provided patterns
        if patterns:
            if any(pattern in lower for pattern in patterns):
                return True

        # Generic intro patterns (doesn't depend on specific text)
        intro_indicators = [
            'here is',
            'below is',
            'following is',
            'translated',
            'translation:',
            'document:',
            'markdown document',
            'english translation',
            'chinese translation',
            '这是',
            '以下是',
            '翻译',
            # Reasoning patterns
            'the document has',
            'steps:',
            'let\'s',
            'we will',
            'we are to',
            'let\'s break down',
            'note:',
            'original chinese text:',
            'we will translate',
            'paragraph by paragraph',
            'we note that',
            'we also note'
        ]

        # If line contains multiple intro indicators, it's likely intro
        indicator_count = sum(1 for indicator in intro_indicators if indicator in lower)
        if indicator_count >= 2:
            return True

        # If line is short and contains intro indicators
        if len(line) < 100 and indicator_count >= 1:
            return True

        # Check for numbered lists (1., 2., 3.) which are often reasoning steps
        stripped = line.strip()
        if stripped and stripped[0].isdigit() and (stripped[1] == '.' or stripped[1:3] == '. '):
            return True

        # Check for bullet points with short text (likely reasoning, not content)
        if stripped.startswith('- ') or stripped.startswith('* '):
            if len(stripped) < 100:  # Short bullet points are likely reasoning
                return True

        return False

    def _remove_chinese_lines_from_bilingual(self, text: str) -> str:
        """
        Remove Chinese lines from bilingual output (common in MT-like models like Mimo).

        Some MT models output "original line + translated line" format.
        This method detects and removes Chinese-dominant lines while preserving English.

        Args:
            text: Text that may contain bilingual content

        Returns:
            Text with Chinese lines removed
        """
        if not text:
            return text

        lines = text.split('\n')
        filtered_lines = []
        removed_count = 0

        for line in lines:
            # Skip empty lines but keep them for structure
            if not line.strip():
                filtered_lines.append(line)
                continue

            # Count Chinese characters in this line
            chinese_chars = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
            total_chars = len(line.strip())

            if total_chars == 0:
                filtered_lines.append(line)
                continue

            chinese_ratio = chinese_chars / total_chars

            # Skip lines that are predominantly Chinese (>40% Chinese characters)
            # This threshold allows for some Chinese in proper nouns, technical terms, etc.
            if chinese_ratio > 0.4:
                logger.debug(f"Removing Chinese-dominant line: {line[:50]}... (chinese_ratio={chinese_ratio:.2%})")
                removed_count += 1
            else:
                filtered_lines.append(line)

        result = '\n'.join(filtered_lines)

        if removed_count > 0:
            logger.info(f"Removed {removed_count} Chinese-dominant lines from bilingual output (original={len(lines)}, remaining={len(filtered_lines)})")

        return result

    def _remove_prompt_artifacts(self, text: str) -> str:
        """
        Remove any remaining prompt artifacts from the text

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove common prefixes (English and Chinese)
        prefixes_to_remove = [
            "Here is the translated Markdown document:\n\n",
            "Here is the translation:\n\n",
            "Translated content:\n\n",
            "Translation:\n\n",
            # Chinese intro patterns
            "好的，这是您提供的 Markdown 文档的英文翻译：\n\n",
            "好的，这是您提供的 Markdown 文档的英文翻译：\n---\n\n",
            "这是您提供的 Markdown 文档的英文翻译：\n\n",
            "以下是翻译后的内容：\n\n",
            "好的，这是您提供的中文文档的英文翻译：\n\n"
        ]

        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text[len(prefix):]
                break

        return text.strip()

    def _final_cleanup(self, text: str) -> str:
        """
        Final cleanup to remove any remaining single-line artifacts

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip lines that are clearly prompt artifacts
            if (stripped and
                any(keyword in stripped.lower() for keyword in [
                    'variable names', 'brand names in english', 'preserve all',
                    'do not translate:', 'output only', 'markdown formatting',
                    'terminology constraints:', 'you must use the following',
                    'when the chinese term appears', 'specified english translation',
                    'do not paraphrase', 'do not abbreviate', 'do not substitute',
                    'if a term in the glossary', 'ignore it', 'if a chinese term',
                    'prefer the glossary translation',
                    # Chinese intro patterns
                    '这是您提供的', '以下是', '好的，这是', 'markdown 文档',
                    '英文翻译', '中文翻译'
                ]) and
                not stripped.startswith('#') and  # Keep headers
                not stripped.startswith('```') and  # Keep code blocks
                not (stripped.startswith('|') and stripped.endswith('|'))):  # Keep table rows
                continue

            # Skip standalone "Glossary:" lines
            if stripped.lower() == 'glossary:':
                continue

            # Skip isolated bullet lines that look like glossary entries
            if (stripped.startswith('-') and
                any(brand in stripped.lower() for brand in [
                    'certificate center', 'byteplus', 'digi cert', 'geo trust',
                    'global sign', 'alpha ssl', 'wotrus'
                ])):
                continue

            cleaned_lines.append(line)

        result = '\n'.join(cleaned_lines).strip()

        # Remove any leading empty lines
        while result.startswith('\n'):
            result = result[1:]

        return result

    
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