"""
Line-by-Line Rewrite Strategy

Legacy strategy that rewrites documents line by line.
This is the original implementation preserved as a strategy.
"""

import logging
import signal
import time
from typing import Dict, List, Any

from .base import RewriteStrategy, RewriteResult, RewriteContext

logger = logging.getLogger(__name__)


class LineByLineRewriteStrategy(RewriteStrategy):
    """
    Legacy line-by-line rewrite strategy.

    Processes documents by splitting them into lines and rewriting each line
    individually. This preserves the original behavior while making it
    pluggable in the new architecture.
    """

    def get_strategy_name(self) -> str:
        return "line_by_line"

    def get_strategy_description(self) -> str:
        return "Legacy strategy: rewrites document line by line, preserving structure"

    def rewrite(self,
                source_markdown: str,
                context: RewriteContext) -> RewriteResult:
        """
        Rewrite document line by line.

        Args:
            source_markdown: Original markdown content
            context: Rewrite context and configuration

        Returns:
            RewriteResult with rewritten content and metadata
        """
        start_time = time.time()
        logger.info(f"Starting line-by-line rewrite for {len(source_markdown)} characters")

        # Parse document into lines (preserve original behavior)
        lines = self._parse_lines(source_markdown)
        logger.info(f"Parsed {len(lines)} lines for rewriting")

        # Rewrite lines
        rewritten_lines = []
        rewritten_count = 0
        warnings = []

        for i, line in enumerate(lines, 1):
            try:
                # Show progress every 10 lines
                if i % 10 == 1:
                    logger.info(f"Processing line {i}/{len(lines)}")

                # Skip empty lines
                if not line.strip():
                    rewritten_lines.append(line)
                    continue

                # Skip code content
                if self._is_code_content(line, source_markdown):
                    rewritten_lines.append(line)
                    continue

                # Rewrite line using AI
                rewritten = self._rewrite_line_with_ai(line, context)

                # Validate rewrite result
                if self._validate_rewrite(line, rewritten):
                    rewritten_lines.append(rewritten)
                    if rewritten != line:
                        rewritten_count += 1
                        logger.debug(f"Line {i} rewritten: '{line[:30]}...' -> '{rewritten[:30]}...'")
                else:
                    rewritten_lines.append(line)
                    warnings.append(f"Line {i}: Rewrite validation failed, using original")

            except Exception as e:
                logger.warning(f"Failed to rewrite line {i}: {e}")
                rewritten_lines.append(line)
                warnings.append(f"Line {i}: Rewrite failed, using original")

        # Reconstruct document
        rewritten_markdown = self._reconstruct_document(rewritten_lines)

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        logger.info(f"Line-by-line rewrite completed: {rewritten_count}/{len(lines)} lines rewritten")

        return RewriteResult(
            original_markdown=source_markdown,
            rewritten_markdown=rewritten_markdown,
            units_processed=len(lines),
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
                }
            }
        )

    def supports_document_type(self, document_type: str) -> bool:
        """Supports markdown and plain text documents."""
        return document_type in ["markdown", "plain_text"]

    def _parse_lines(self, text: str) -> List[str]:
        """Parse document into lines (preserve original behavior)."""
        lines = text.split('\n')
        # Keep empty lines to preserve structure
        return lines

    def _is_code_content(self, line: str, full_text: str) -> bool:
        """Check if line contains code that should not be rewritten."""
        # Check if line is a code block marker
        if line.strip().startswith('```'):
            return True

        # Check if line contains code indicators
        code_indicators = [
            'def ', 'class ', 'import ', 'from ', 'function', 'var ', 'let ', 'const ',
            'if ', 'for ', 'while ', 'return ', 'print(', 'console.log',
            '=>', '&&', '||', '++', '--', '/*', '*/', '//', '#include', '#define'
        ]

        line_stripped = line.strip()
        for indicator in code_indicators:
            if indicator in line_stripped:
                return True

        return False

    def _rewrite_line_with_ai(self, line: str, context: RewriteContext) -> str:
        """Rewrite a single line using AI."""
        # Build rewrite prompt (preserve original logic)
        prompt = self._build_rewrite_prompt(line, context)

        # Set up timeout handling
        def timeout_handler(signum, frame):
            raise TimeoutError("AI provider call timed out")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(context.timeout_seconds)

        try:
            logger.debug(f"Rewriting line with {self.provider.get_name()}: {line[:30]}...")

            response = self.provider.translate(
                prompt,
                source_lang="zh",
                target_lang="zh"
            )

            signal.alarm(0)  # Cancel timeout

            # Extract rewritten line from response
            rewritten = self._extract_rewritten_line(response, line)

            logger.debug(f"Extracted rewritten line: {rewritten[:30] if rewritten != line else 'unchanged'}...")

            return rewritten

        except TimeoutError as e:
            logger.error(f"AI provider timeout: {e}")
            return line

        except Exception as e:
            logger.error(f"AI rewrite failed: {e}")
            return line

        finally:
            signal.alarm(0)  # Ensure timeout is cancelled

    def _build_rewrite_prompt(self, line: str, context: RewriteContext) -> str:
        """Build rewrite prompt for a single line."""
        # Base rewrite prompt (preserve original behavior)
        prompt = f"""请改写以下中文句子，使其表达更加清晰、专业和优雅。

改写要求：
1. 保持原意完全不变
2. 优化表达方式，使其更专业
3. 提高语言的流畅性和精确性
4. 保持语句结构完整
5. 只返回改写后的句子，不要解释

原句：{line}

改写："""

        # Add context information if available
        context_parts = []
        if context.document_intent:
            context_parts.append(f"文档意图: {context.document_intent}")
        if context.target_audience:
            context_parts.append(f"目标读者: {context.target_audience}")
        if context.tone:
            context_parts.append(f"语气风格: {context.tone}")
        if context.domain:
            context_parts.append(f"领域: {context.domain}")

        if context_parts:
            context_text = "\n\n上下文信息：\n" + "\n".join(f"- {part}" for part in context_parts)
            prompt = prompt + context_text

        return prompt

    def _extract_rewritten_line(self, response: str, original: str) -> str:
        """Extract rewritten line from AI response."""
        # Clean response
        rewritten = response.strip()

        # Remove possible explanations
        if "改写：" in rewritten:
            rewritten = rewritten.split("改写：")[-1].strip()
        elif "Rewrite:" in rewritten:
            rewritten = rewritten.split("Rewrite:")[-1].strip()

        # If response is too long, try to extract first line
        if len(rewritten) > len(original) * 2:
            lines = rewritten.split('\n')
            if lines:
                rewritten = lines[0].strip()

        # If extracted line is empty or too short, return original
        if not rewritten or len(rewritten) < len(original) * 0.3:
            return original

        return rewritten

    def _validate_rewrite(self, original: str, rewritten: str) -> bool:
        """Validate that rewrite result is reasonable."""
        # Basic validation checks
        if not rewritten or len(rewritten) < len(original) * 0.3:
            return False

        if len(rewritten) > len(original) * 3:
            return False

        return True

    def _reconstruct_document(self, lines: List[str]) -> str:
        """Reconstruct document from rewritten lines."""
        return '\n'.join(lines)