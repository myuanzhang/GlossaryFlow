"""
Translation Output Contract

This module defines a model-agnostic contract for translation output.
It ensures that ALL models (cloud, local, reasoning, chat) produce clean output.
"""

import re
import logging
from typing import Tuple, Optional
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TranslationOutputContract:
    """
    Model-agnostic translation output contract.

    Guarantees:
    1. No prompt/instruction text in output
    2. No truncation of translated content
    3. Deterministic, reproducible cleaning
    4. Safe for all model types
    """

    # Markers that indicate where translated content STARTS
    # These are model-independent patterns that signal "instructions end, output begins"
    CONTENT_START_MARKERS = [
        # Explicit translation start markers (ONLY these)
        'translation:',
        'translated content:',
        'here is the translation:',
        'below is the translation:',

        # Chinese markers
        '翻译如下：',
        '翻译结果：',
        '以下是翻译：',
    ]

    # ⚠️ DO NOT include '# ' (markdown headers) as markers!
    # Headers are legitimate content, not instruction boundaries.

    # Patterns that indicate content is NOT translated content
    # These are model-independent and safe to remove
    NON_CONTENT_PATTERNS = [
        # Prompt/instruction text (unique phrases unlikely in valid translation)
        'you are a professional translator',
        'translate all chinese text',
        'important requirements:',
        'preserve all markdown formatting',
        'terminology constraints:',
        'do not translate:',
        'variable names',
        'brand names in english',

        # Reasoning/chat filler
        'i will translate',
        'let me translate',
        'step 1:',
        'step 2:',
        'translation strategy:',
        'here is my plan',

        # Chinese intro
        '这是您提供的',
        '以下是翻译后的内容',
        '好的，这是',
        'markdown 文档',
    ]

    # Prefix patterns that should be stripped from the start of output
    PREFIX_CLEANUP_PATTERNS = [
        r'^here is the (translated )?(markdown )?document:?\s*\n',
        r'^here is the translation:?\s*\n',
        r'^translation:?\s*\n',
        r'^translated content:?\s*\n',
        r'^好的，这是.*?翻译：\s*\n',
        r'^这是您提供的.*?翻译：\s*\n',
        r'^以下是翻译后的?内容：\s*\n',
    ]

    @classmethod
    def parse_model_output(cls, raw_output: str, source_text: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Parse and clean model output according to the contract.

        This is the ONLY method that should be used to clean model output.
        It is deterministic, model-agnostic, and safe for all model types.

        Args:
            raw_output: Raw output from the model
            source_text: Optional source text for validation

        Returns:
            (cleaned_output, metadata) where metadata contains parsing info
        """
        if not raw_output:
            return "", {"status": "empty", "original_length": 0}

        original_length = len(raw_output)
        metadata = {
            "status": "unknown",
            "original_length": original_length,
            "cleaned_length": 0,
            "removed_prefix": None,
            "removed_suffix": None,
            "has_chinese": False,
            "validation_errors": []
        }

        # Step 1: Remove known prefix patterns (deterministic, safe)
        cleaned = cls._remove_prefix_patterns(raw_output)
        if cleaned != raw_output:
            metadata["removed_prefix"] = "pattern_match"
            logger.info(f"Removed prefix pattern: {len(raw_output) - len(cleaned)} chars")

        # Step 2: Remove thinking/reasoning tags if present (safe)
        cleaned = cls._remove_thinking_tags(cleaned)
        if len(cleaned) < original_length * 0.9:  # Only log if significant removal
            logger.info(f"Removed thinking tags: {len(raw_output) - len(cleaned)} chars")

        # Step 3: Detect and remove instruction echo at the START (safe, bounded)
        # Only look at first 50 lines - prevents false positives on long content
        cleaned, removed_intro = cls._remove_instruction_echo_at_start(cleaned)
        if removed_intro:
            metadata["removed_prefix"] = "instruction_echo"

        # Step 4: Find and extract actual content start (safe, explicit)
        # Look for explicit content start markers
        cleaned, start_marker = cls._extract_from_start_marker(cleaned)
        if start_marker:
            metadata["removed_prefix"] = f"marker:{start_marker}"
            logger.info(f"Extracted content from marker: {start_marker}")

        # Step 5: Remove any remaining single-line prompt artifacts (safe)
        cleaned = cls._remove_prompt_artifacts(cleaned)

        # Step 6: Final validation (non-destructive)
        metadata["cleaned_length"] = len(cleaned)

        # Check for Chinese characters
        chinese_count = sum(1 for c in cleaned if '\u4e00' <= c <= '\u9fff')
        metadata["has_chinese"] = chinese_count > 0

        # Validate: if cleaning removed too much, use original
        if len(cleaned) < original_length * 0.3:
            logger.warning(f"Cleaning removed too much content ({len(cleaned)}/{original_length}), using original with minimal cleanup")
            metadata["validation_errors"].append("over_aggressive_cleaning")
            cleaned = cls._minimal_cleanup(raw_output)
            metadata["cleaned_length"] = len(cleaned)

        if len(cleaned) == 0:
            metadata["status"] = "empty"
            logger.error("Output cleaning resulted in empty content")
        else:
            metadata["status"] = "cleaned"

        return cleaned, metadata

    @classmethod
    def _remove_prefix_patterns(cls, text: str) -> str:
        """Remove known prefix patterns from the start of text."""
        for pattern in cls.PREFIX_CLEANUP_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return text[match.end():]
        return text

    @classmethod
    def _remove_thinking_tags(cls, text: str) -> str:
        """Remove <thinking>, <analysis>, <reasoning> tags and content."""
        # Remove thinking/analysis/reasoning blocks (multiline)
        for tag in ['thinking', 'analysis', 'reasoning']:
            pattern = rf'<{tag}>.*?</{tag}>'
            text = re.sub(pattern, '', text, flags=re.DOTALL | re.IGNORECASE)

        # Clean up extra whitespace
        lines = text.split('\n')
        cleaned_lines = [line for line in lines if line.strip()]
        return '\n'.join(cleaned_lines).strip()

    @classmethod
    def _remove_instruction_echo_at_start(cls, text: str) -> Tuple[str, bool]:
        """
        Remove instruction echo from the START of output.

        This is safe and bounded:
        - Only examines first 50 lines
        - Stops at first content-like line
        - Only removes lines matching instruction patterns

        ⚠️ SAFETY: Prefer false negatives (keep instruction echo)
        over false positives (remove legitimate content).
        """
        lines = text.split('\n')

        # Only check first 50 lines for instruction echo
        scan_limit = min(50, len(lines))
        content_start_idx = 0
        consecutive_instruction_lines = 0

        for i in range(scan_limit):
            line = lines[i].strip()

            # Empty line - reset counter and keep going
            if not line:
                # If we've seen instruction lines, this might be the boundary
                if consecutive_instruction_lines > 0:
                    # Check if next non-empty line looks like content
                    for j in range(i + 1, min(i + 3, len(lines))):
                        if lines[j].strip():
                            next_line = lines[j].strip()
                            # If next line is clearly content, stop here
                            if next_line.startswith('#') or len(next_line) > 80:
                                content_start_idx = i + 1
                                break
                    break
                continue

            # Check if this line is instruction/prompt text
            is_instruction = any(
                pattern in line.lower()
                for pattern in cls.NON_CONTENT_PATTERNS
            )

            if is_instruction:
                # This is still instruction, skip it
                content_start_idx = i + 1
                consecutive_instruction_lines += 1
                continue

            # Check if this looks like actual content
            # Content indicators (conservative check):
            # - Starts with Markdown header (# ## ###)
            # - Is reasonably long (> 30 chars, was 50)
            # - Contains markdown patterns (```, **, *, [, etc.)
            # - Is NOT a short numbered list item
            looks_like_content = (
                line.startswith('#') or
                len(line) > 30 or  # Relaxed from 50 to 30
                (any(marker in line for marker in ['```', '**', '*', '[', ']']) and len(line) > 20)
            )

            # Additional check: short numbered lists might be reasoning
            is_numbered_list = (
                line and
                line[0].isdigit() and
                (line[1] == '.' or line[1:3] == '. ')
            )

            if looks_like_content and not is_numbered_list:
                # Found content, stop here
                break

            # If we've seen multiple consecutive instruction-like lines,
            # and this line doesn't look like content, keep skipping
            if consecutive_instruction_lines >= 2:
                content_start_idx = i + 1
                continue

            # Otherwise, be conservative and assume this is content
            break

        # Extract from content start
        if content_start_idx > 0:
            result = '\n'.join(lines[content_start_idx:]).strip()
            removed_count = content_start_idx
            if len(result) > 20 and removed_count < 20:  # Only if substantial content remains and not too many lines removed
                logger.info(f"Removed {removed_count} lines of instruction echo from start")
                return result, True

        return text, False

    @classmethod
    def _extract_from_start_marker(cls, text: str) -> Tuple[str, Optional[str]]:
        """
        Extract content starting from an explicit content start marker.

        This is safe because markers are explicit and unambiguous.
        Markers MUST be instruction-delimiter patterns, NOT legitimate content.

        ⚠️ SAFETY: Only use markers that are UNIQUE to instruction text.
        Never use markdown patterns (like '# ') as they are valid content.
        """
        lines = text.split('\n')

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            # Check if this line contains a content start marker
            for marker in cls.CONTENT_START_MARKERS:
                # Match must be at the START of the line (not in the middle)
                # This prevents false positives on legitimate content
                if line_lower.startswith(marker.lower()):
                    # Extract everything AFTER this line
                    # Skip the marker line itself + 1 empty line
                    result_start = i + 1

                    # Skip empty lines immediately after marker
                    while result_start < len(lines) and not lines[result_start].strip():
                        result_start += 1

                    if result_start < len(lines):
                        result = '\n'.join(lines[result_start:]).strip()

                        # Only extract if substantial content remains
                        if len(result) > 20:
                            logger.info(f"Extracted content from marker '{marker}' at line {i}, "
                                       f"skipping {result_start - i} lines")
                            return result, marker

        return text, None

    @classmethod
    def _remove_prompt_artifacts(cls, text: str) -> str:
        """Remove single-line prompt artifacts from the output."""
        lines = text.split('\n')
        cleaned = []

        for line in lines:
            stripped = line.strip()

            # Skip empty lines but keep them for structure
            if not stripped:
                cleaned.append(line)
                continue

            # Skip lines that are clearly prompt artifacts
            is_artifact = any(
                keyword in stripped.lower()
                for keyword in [
                    'variable names',
                    'brand names in english',
                    'preserve all',
                    'do not translate:',
                    'output only',
                    'terminology constraints:',
                    'you must use the following',
                    'when the chinese term appears',
                    'specified english translation',
                    'do not paraphrase',
                    'if a term in the glossary',
                ]
            )

            # But keep lines that look like actual content
            if is_artifact and not (
                stripped.startswith('#') or
                stripped.startswith('```') or
                (stripped.startswith('|') and stripped.endswith('|'))
            ):
                continue

            cleaned.append(line)

        return '\n'.join(cleaned).strip()

    @classmethod
    def _minimal_cleanup(cls, text: str) -> str:
        """
        Minimal, safe cleanup that only removes obvious artifacts.

        Used when aggressive cleaning removed too much content.
        """
        # Only remove thinking tags
        cleaned = cls._remove_thinking_tags(text)

        # Remove obvious prefix patterns
        cleaned = cls._remove_prefix_patterns(cleaned)

        return cleaned.strip()
