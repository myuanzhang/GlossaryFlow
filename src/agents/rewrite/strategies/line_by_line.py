"""
Line-by-Line Rewrite Strategy

Legacy line-by-line rewrite strategy preserved as a pluggable strategy.
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

    def rewrite(self, source_markdown: str, context: RewriteContext) -> RewriteResult:
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
        logger.info(f"Parsed {len(lines)} lines for line-by-line rewrite")

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

                # Apply rewrite logic from original implementation
                rewritten = self._rewrite_line(line, context)

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
        rewritten_markdown = '\n'.join(rewritten_lines)

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        logger.info(f"Line-by-line rewrite completed: {rewritten_count}/{len(lines)} lines rewritten")

        return RewriteResult(
            rewritten_markdown=rewritten_markdown,
            original_markdown=source_markdown,
            units_processed=len(lines),
            units_rewritten=rewritten_count,
            strategy_name=self.get_strategy_name(),
            processing_time_ms=processing_time_ms,
            warnings=warnings,
            metadata={
                "strategy_description": self.get_strategy_description(),
                "provider_used": self.provider.get_name(),
                "context": {
                    "document_intent": context.document_intent,
                    "target_audience": context.target_audience,
                    "tone": context.tone,
                    "domain": context.domain
                }
            }
        )

    def _parse_lines(self, text: str) -> List[str]:
        """
        Parse document into lines (preserve original behavior).

        Args:
            text: Input text

        Returns:
            List of lines
        """
        return text.split('\n')

    def _rewrite_line(self, line: str, context: RewriteContext) -> str:
        """
        Rewrite a single line.

        Args:
            line: Line to rewrite
            context: Rewrite context

        Returns:
            Rewritten line
        """
        # Set up timeout handling
        def timeout_handler(signum, frame):
            raise TimeoutError("AI provider call timed out")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(context.timeout_seconds)

        try:
            logger.debug(f"Rewriting line: {line[:50]}...")

            # Use the provider to rewrite the line
            # Construct a simple rewrite prompt
            rewrite_prompt = f"""请将以下内容进行改写，使其更清晰、更流畅：

{line}

要求：
1. 保持原意不变
2. 使用更自然的表达
3. 只返回改写后的内容"""

            response = self.provider.generate(
                rewrite_prompt,
                model="default",  # Provider will use default model
                temperature=context.temperature
            )

            signal.alarm(0)  # Cancel timeout

            # Clean up response
            rewritten = self._clean_provider_response(response)
            logger.debug(f"Line rewritten to: {rewritten[:50] if rewritten != line else 'unchanged'}...")

            return rewritten

        except TimeoutError as e:
            logger.error(f"AI provider timeout: {e}")
            return line

        except Exception as e:
            logger.error(f"Line rewrite failed: {e}")
            return line

        finally:
            signal.alarm(0)  # Ensure timeout is cancelled

    def _clean_provider_response(self, response: str) -> str:
        """
        Clean provider response to extract just the rewritten content.

        Args:
            response: Raw provider response

        Returns:
            Cleaned rewritten content
        """
        if not response:
            return ""

        # Remove any leading/trailing whitespace
        cleaned = response.strip()

        # Remove common response artifacts
        artifacts = [
            "改写后的内容：",
            "改写结果：",
            "根据要求，改写如下：",
            "以下是改写后的内容：",
            "改写后的文本：",
            "改写结果如下："
        ]

        for artifact in artifacts:
            if cleaned.startswith(artifact):
                cleaned = cleaned[len(artifact):].strip()
                break

        return cleaned

    def _validate_rewrite(self, original: str, rewritten: str) -> bool:
        """
        Validate that the rewrite is reasonable.

        Args:
            original: Original line
            rewritten: Rewritten line

        Returns:
            Whether rewrite is valid
        """
        # Basic checks
        if not rewritten or len(rewritten.strip()) == 0:
            return False

        # Length check - not too different
        original_len = len(original.strip())
        rewritten_len = len(rewritten.strip())

        if original_len > 0:
            ratio = rewritten_len / original_len
            if ratio < 0.5 or ratio > 3.0:  # Allow significant but reasonable changes
                return False

        # Not identical
        if rewritten.strip() == original.strip():
            return False

        # Simple duplicate check
        if rewritten.startswith(original[:10]) and rewritten.endswith(original[-10:]):
            return False

        return True

    def supports_document_type(self, document_type: str) -> bool:
        """Supports markdown and plain text documents."""
        return document_type in ["markdown", "plain_text"]

    def __repr__(self) -> str:
        return f"<LineByLineRewriteStrategy(provider={self.provider.get_name()})>"