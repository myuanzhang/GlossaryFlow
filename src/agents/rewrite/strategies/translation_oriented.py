"""
Translation-Oriented Rewrite Strategy

Rewrites Chinese documents to be more translation-friendly for machine translation
to English while preserving semantic meaning and Markdown structure.
"""

import logging
import signal
import time
import re
from typing import Dict, List, Any

from .base import RewriteStrategy, RewriteResult, RewriteContext
from prompt.managers.translation_oriented_manager import TranslationOrientedPromptManager

logger = logging.getLogger(__name__)


class TranslationOrientedRewriteStrategy(RewriteStrategy):
    """
    Translation-oriented rewrite strategy.

    Optimizes Chinese text for machine translation by:
    - Breaking down complex sentences
    - Making subjects and logical relationships explicit
    - Stabilizing terminology
    - Avoiding rhetorical or Chinese-specific expressions
    - Maintaining Markdown structure
    - Preserving code blocks
    """

    def __init__(self, provider, config: Dict[str, Any] = None):
        """Initialize the translation-oriented rewrite strategy."""
        super().__init__(provider, config)
        self.prompt_manager = TranslationOrientedPromptManager()

    def get_strategy_name(self) -> str:
        return "translation_oriented"

    def get_strategy_description(self) -> str:
        return "Translation-optimized: rewrites Chinese text for better machine translation to English"

    def rewrite(self, source_markdown: str, context: RewriteContext) -> RewriteResult:
        """
        Rewrite document for translation optimization.

        Args:
            source_markdown: Original markdown content
            context: Rewrite context and configuration

        Returns:
            RewriteResult with rewritten content and metadata
        """
        start_time = time.time()
        logger.info(f"Starting translation-oriented rewrite for {len(source_markdown)} characters")

        # Parse document into processing units
        units = self._parse_translation_units(source_markdown)
        logger.info(f"Parsed {len(units)} units for translation-oriented rewrite")

        # Rewrite units
        rewritten_units = []
        rewritten_count = 0
        warnings = []

        for i, unit in enumerate(units, 1):
            try:
                # Show progress every 5 units
                if i % 5 == 1:
                    logger.info(f"Processing unit {i}/{len(units)}")

                # Skip empty units
                if not unit.strip():
                    rewritten_units.append(unit)
                    continue

                # Skip code and non-translatable content
                if self._should_preserve_as_is(unit):
                    rewritten_units.append(unit)
                    continue

                # Apply translation-oriented rewrite
                rewritten = self._rewrite_for_translation(unit, context)

                # Validate rewrite result
                if self._validate_translation_rewrite(unit, rewritten):
                    rewritten_units.append(rewritten)
                    if rewritten != unit:
                        rewritten_count += 1
                        logger.debug(f"Unit {i} optimized: '{unit[:30]}...' -> '{rewritten[:30]}...'")
                else:
                    rewritten_units.append(unit)
                    warnings.append(f"Unit {i}: Rewrite validation failed, using original")

            except Exception as e:
                logger.warning(f"Failed to rewrite unit {i}: {e}")
                rewritten_units.append(unit)
                warnings.append(f"Unit {i}: Rewrite failed, using original")

        # Reconstruct document
        rewritten_markdown = self._reconstruct_document(rewritten_units, source_markdown)

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        logger.info(f"Translation-oriented rewrite completed: {rewritten_count}/{len(units)} units optimized")

        return RewriteResult(
            rewritten_markdown=rewritten_markdown,
            original_markdown=source_markdown,
            units_processed=len(units),
            units_rewritten=rewritten_count,
            strategy_name=self.get_strategy_name(),
            processing_time_ms=processing_time_ms,
            warnings=warnings,
            metadata={
                "strategy_description": self.get_strategy_description(),
                "provider_used": self.provider.get_name(),
                "context": {
                    "intent": context.document_intent,
                    "target_audience": context.target_audience,
                    "tone": context.tone,
                    "domain": context.domain
                },
                "optimization_applied": [
                    "sentence_simplification",
                    "explicit_subjects",
                    "logical_clarity",
                    "terminology_stabilization",
                    "rhetorical_reduction"
                ]
            }
        )

    def supports_document_type(self, document_type: str) -> bool:
        """Supports markdown and plain text documents."""
        return document_type in ["markdown", "plain_text"]

    def _determine_section_type(self, unit: str) -> str:
        """Determine the type of content unit."""
        unit_stripped = unit.strip()

        if not unit_stripped:
            return "empty"

        if unit_stripped.startswith('```'):
            return "code_block"

        if unit_stripped.startswith('#'):
            return "header"

        if unit_stripped.startswith(('-', '*', '+')):
            return "list_item"

        if unit_stripped.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            return "numbered_list"

        if unit_stripped.startswith('>'):
            return "blockquote"

        if '|' in unit and unit.count('|') >= 2:
            return "table_row"

        if unit_stripped.startswith('!['):
            return "image"

        if '](' in unit_stripped:
            return "link"

        if '`' in unit and unit.count('`') >= 2:
            return "inline_code"

        # If it's a longer text, it's likely a paragraph
        if len(unit_stripped) > 50:
            return "paragraph"

        return "text"

    def _parse_translation_units(self, text: str) -> List[str]:
        """
        Parse document into translation units.

        Improved logic for better paragraph-level processing while preserving structure.
        """
        units = []
        lines = text.split('\n')
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            line_stripped = line.strip()

            # Handle code blocks (preserve as-is)
            if line_stripped.startswith('```'):
                # Find end of code block
                code_fence = line_stripped
                code_content = [line]
                i += 1

                while i < n:
                    code_content.append(lines[i])
                    if lines[i].strip().startswith('```'):
                        break
                    i += 1

                units.append('\n'.join(code_content))
                i += 1
                continue

            # Handle headers (separate units)
            if line_stripped.startswith('#'):
                units.append(line)
                i += 1
                continue

            # Handle list items (group consecutive list items)
            if (line_stripped.startswith(('-', '*', '+')) or
                re.match(r'^\d+\.', line_stripped)):
                list_items = [line]
                i += 1

                # Collect consecutive list items
                while i < n:
                    next_line_stripped = lines[i].strip()
                    if (next_line_stripped.startswith(('-', '*', '+')) or
                        re.match(r'^\d+\.', next_line_stripped) or
                        next_line_stripped.startswith('  ')):  # Indented continuation
                        list_items.append(lines[i])
                        i += 1
                    else:
                        break

                units.append('\n'.join(list_items))
                continue

            # Handle blockquotes
            if line_stripped.startswith('>'):
                units.append(line)
                i += 1
                continue

            # Handle tables (preserve as-is)
            if '|' in line and line.count('|') >= 2:
                units.append(line)
                i += 1
                continue

            # Handle empty lines
            if not line_stripped:
                units.append(line)
                i += 1
                continue

            # Handle paragraphs (collect consecutive text lines)
            paragraph_lines = [line]
            i += 1

            while i < n:
                next_line = lines[i]
                next_line_stripped = next_line.strip()

                # Stop on structural elements
                if (next_line_stripped.startswith('#') or
                    next_line_stripped.startswith('```') or
                    next_line_stripped.startswith(('-', '*', '+')) or
                    next_line_stripped.startswith('>') or
                    re.match(r'^\d+\.', next_line_stripped) or
                    (next_line_stripped and '|' in next_line and next_line.count('|') >= 2) or
                    not next_line_stripped):  # Empty line
                    break

                # Continue paragraph
                paragraph_lines.append(next_line)
                i += 1

            # Join paragraph lines
            paragraph = '\n'.join(paragraph_lines)
            units.append(paragraph)

        return units

    def _should_preserve_as_is(self, unit: str) -> bool:
        """Check if unit should be preserved without modification."""
        unit_stripped = unit.strip()

        # Preserve empty units
        if not unit_stripped:
            return True

        # Preserve very short content (likely structural)
        if len(unit_stripped) < 10:
            return True

        # Preserve code blocks
        if unit_stripped.startswith('```'):
            return True

        # Preserve URLs and links
        if 'http://' in unit or 'https://' in unit or '](' in unit:
            return True

        # Preserve image references
        if unit_stripped.startswith('!['):
            return True

        # Preserve inline code (only if it's primarily code)
        if '`' in unit and unit.count('`') >= 2:
            # Check if it's mostly code vs text with code
            code_length = len([c for c in unit if c == '`']) * 2  # Rough estimate
            if code_length / len(unit) > 0.3:  # More than 30% code
                return True

        # Preserve table markers
        if '|' in unit and unit.count('|') >= 2:
            return True

        # Preserve YAML front matter
        if unit_stripped.startswith('---') and unit_stripped.endswith('---'):
            return True

        # Preserve quotes that are very short
        if unit_stripped.startswith('"') and unit_stripped.endswith('"') and len(unit_stripped) < 20:
            return True

        return False

    def _rewrite_for_translation(self, unit: str, context: RewriteContext) -> str:
        """Rewrite a unit for translation optimization."""
        # Determine section type for better prompt
        section_type = self._determine_section_type(unit)

        # Build translation-oriented prompt using prompt manager
        prompt = self.prompt_manager.build_prompt(
            content=unit,
            context=context,
            section_type=section_type
        )

        # Set up timeout handling
        def timeout_handler(signum, frame):
            raise TimeoutError("AI provider call timed out")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(context.timeout_seconds)

        try:
            logger.debug(f"Optimizing for translation: {unit[:50]}...")

            response = self.provider.translate(
                prompt,
                source_lang="zh",
                target_lang="zh"
            )

            signal.alarm(0)  # Cancel timeout

            # Extract optimized unit from response
            optimized = self._extract_optimized_unit(response, unit)

            logger.debug(f"Extracted optimized unit: {optimized[:50] if optimized != unit else 'unchanged'}...")

            return optimized

        except TimeoutError as e:
            logger.error(f"AI provider timeout: {e}")
            return unit

        except Exception as e:
            logger.error(f"Translation optimization failed: {e}")
            return unit

        finally:
            signal.alarm(0)  # Ensure timeout is cancelled

    # Old prompt building method removed - now using TranslationOrientedPromptManager

    def _extract_optimized_unit(self, response: str, original: str) -> str:
        """Extract optimized unit from AI response."""
        # Clean response
        optimized = response.strip()

        # Multiple extraction strategies
        extraction_patterns = [
            "改写后的内容：",
            "改写：",
            "优化后：",
            "原文改写为：",
            "改写结果："
        ]

        for pattern in extraction_patterns:
            if pattern in optimized:
                optimized = optimized.split(pattern)[-1].strip()
                break

        # If response is too long, try to extract relevant part
        if len(optimized) > len(original) * 1.5:
            lines = optimized.split('\n')
            # Try to find the first substantial line that looks like rewritten content
            for line in lines:
                line_stripped = line.strip()
                if (line_stripped and
                    not any(marker in line_stripped for marker in [
                        '原则：', '目标：', '上下文信息：', '- ',
                        '改写要求：', '原文：', '示例', '注意：',
                        'Constraints:', 'Rules:', 'Examples:'
                    ])):
                    optimized = line_stripped
                    break

        # More specific cleaning for Chinese content
        # Remove common AI response artifacts
        import re
        cleanup_patterns = [
            r'以下是改写后的内容：?\s*',
            r'改写结果：?\s*',
            r'根据上述原则，改写如下：?\s*',
            r'按照改写要求，原文改写为：?\s*'
        ]

        for pattern in cleanup_patterns:
            optimized = re.sub(pattern, '', optimized).strip()

        # Final validation and fallback
        if not optimized or len(optimized) < len(original) * 0.3:
            logger.debug(f"Failed to extract valid rewritten content from response")
            return original

        # Check if the optimized content is too similar to original
        # Calculate similarity based on character overlap
        original_chars = set(original)
        optimized_chars = set(optimized)

        if len(original_chars) > 20:  # Only check for longer content
            similarity = len(original_chars & optimized_chars) / len(original_chars)
            if similarity > 0.95:  # Too similar, probably no real rewrite
                logger.debug(f"Rewrite result too similar to original (similarity: {similarity:.2f})")
                return original

        return optimized

    def _validate_translation_rewrite(self, original: str, rewritten: str) -> bool:
        """
        Validate that the rewritten content is appropriate for translation.
        More lenient validation while maintaining quality standards.
        """
        # Basic existence and minimum length check
        if not rewritten or len(rewritten.strip()) == 0:
            return False

        # More lenient length requirement - allow significant reduction
        if len(rewritten) < len(original) * 0.4:  # Changed from 0.5 to 0.4
            return False

        # Allow significant expansion but not excessive
        if len(rewritten) > len(original) * 3.0:  # Changed from 2.0 to 3.0
            return False

        # Remove common punctuation for word analysis
        original_clean = re.sub(r'[^\w\s]', ' ', original)
        rewritten_clean = re.sub(r'[^\w\s]', ' ', rewritten)

        original_words = set(original_clean.split())
        rewritten_words = set(rewritten_clean.split())

        # Enhanced semantic preservation check
        if len(original_words) > 8:  # Only check for meaningful content
            common_words = original_words & rewritten_words
            overlap_ratio = len(common_words) / len(original_words)

            # More flexible overlap requirement
            if overlap_ratio < 0.5:  # Changed from 0.6 to 0.5
                return False

        # Check for simple duplication or minimal changes
        if rewritten.strip() == original.strip():
            return False

        # Avoid patterns that suggest poor translation quality
        poor_patterns = [
            rewritten.startswith(original[:10]),  # Simple prefix copying
            rewritten.endswith(original[-10:]),   # Simple suffix copying
            "翻译" in rewritten and "原文" in rewritten,  # Meta-commentary
            "[Mock" in rewritten  # Mock provider artifacts
        ]

        if any(poor_patterns):
            return False

        # Check for English content - this should be Chinese rewrite only
        english_words = re.findall(r'\b[A-Za-z]+\b', rewritten)
        if english_words:
            # Remove common English words that might appear in Chinese context
            allowed_english = {'OK', 'AI', 'API', 'URL', 'HTTP', 'HTTPS', 'HTML', 'CSS', 'JS', 'JSON', 'XML', 'SQL', 'IDE', 'UI', 'UX', 'CPU', 'GPU', 'RAM', 'SSD', 'HDD'}
            problematic_english = [word for word in english_words if word.upper() not in allowed_english and len(word) > 2]

            if problematic_english:
                logger.debug(f"English content detected in rewrite: {problematic_english}")
                return False

        # Check that essential structure is preserved (for headers and lists)
        if original.strip().startswith('#'):
            if not rewritten.strip().startswith('#'):
                return False

        if original.strip().startswith(('-', '*', '+')):
            if not any(rewritten.strip().startswith(marker) for marker in ['-', '*', '+']):
                return False

        return True

    def _reconstruct_document(self, units: List[str], original: str) -> str:
        """Reconstruct document from optimized units."""
        return '\n'.join(units)