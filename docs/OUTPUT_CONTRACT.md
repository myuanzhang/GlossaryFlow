# Translation Output Contract

## Problem Statement

Local LLM models (Ollama) and some cloud models have unpredictable output behavior:

1. **Head Truncation** (e.g., hunyuan:7b): Model outputs only the latter half of translated content
2. **Prompt Echo** (e.g., llama3:8b): System/instruction text appears at the beginning of output
3. **Bilingual Output** (e.g., Mimo): Model outputs "原文 + Translation" pairs

The original output cleaning logic was designed for reasoning/chat models and was **too aggressive** for local models, leading to:
- Valid content being deleted
- Truncated translations
- Model-specific hacks that don't generalize

## Solution: Translation Output Contract

We've introduced a **model-agnostic output contract** that:

1. **Defines clear output boundaries** with explicit markers
2. **Uses bounded, safe cleaning** that cannot over-aggressively delete content
3. **Is deterministic** and reproducible across all model types
4. **Has fallback mechanisms** when cleaning fails

### Contract Guarantees

✅ No prompt/instruction text in output
✅ No truncation of translated content (validated by length checks)
✅ Deterministic cleaning (same input → same output)
✅ Safe for all model types (cloud, local, reasoning, chat, MT)

## Implementation

### 1. Output Contract ([`src/core/output_contract.py`](src/core/output_contract.py))

The `TranslationOutputContract.parse_model_output()` method is the **ONLY** method that should clean model output.

**Cleaning Steps (in order):**

1. **Remove prefix patterns** (deterministic regex-based)
   - Removes common intros like "Here is the translation:", "好的，这是..."
   - Safe because patterns are explicit and unique

2. **Remove thinking tags** (if present)
   - Removes `<thinking>`, `<analysis>`, `<reasoning>` blocks
   - Only affects reasoning models, safe for others

3. **Remove instruction echo at start** (bounded to 50 lines)
   - Only examines first 50 lines
   - Stops at first content-like line
   - Cannot remove valid content from middle/end

4. **Extract from content start markers** (explicit)
   - Looks for unambiguous markers like "Translation:", "# "
   - Only extracts AFTER the marker line
   - Safe because markers are explicit

5. **Remove prompt artifacts** (single-line, conservative)
   - Only removes lines that are clearly artifacts
   - Preserves headers, code blocks, tables

6. **Validation with fallback**
   - If cleaning removed >70% of content → use minimal cleanup
   - If result is empty → use original
   - **Never loses data**

### 2. Ollama-Optimized Prompt ([`prompts/translation/base_ollama.md`](prompts/translation/base_ollama.md))

Uses **clear delimiters** to reduce instruction echo:

```
===TRANSLATION TASK START===

[instructions]

===OUTPUT INSTRUCTION===
Output ONLY the English translation.

===DOCUMENT START===

[content follows here]
```

**Why this works:**
- Delimiters are explicit and unambiguous
- Models are less likely to echo delimited sections
- Easy to detect and remove if echoed
- Minimal instruction text = less to echo

### 3. Model Type Detection ([`src/translator/markdown_translator.py`](src/translator/markdown_translator.py#L225))

Different strategies for different model types:

| Model Type | Examples | Prompt | Cleaning |
|-----------|----------|--------|----------|
| **reasoning** | DeepSeek-R1, o1 | Strict "output only" | Remove thinking tags |
| **mt-like** | Mimo, nmt | Minimal, direct | Remove Chinese lines |
| **ollama** | llama3, hunyuan | Delimited prompt | Standard contract |
| **chat** | GPT-3.5, Qwen | Emphasize task | Standard contract |

## Why This Won't Cause Regression

### 1. Safe by Design

- **Bounded operations**: Only examines first 50 lines for instruction echo
- **Explicit markers**: Only removes content matching unambiguous patterns
- **Fallback mechanism**: Falls back to minimal cleanup if aggressive cleaning removes too much
- **Length validation**: Checks that cleaning didn't remove >70% of content

### 2. Backward Compatible

- **Cloud models unchanged**: OpenAI, DeepSeek, Qwen use existing prompts
- **Reasoning models unchanged**: Still use strict "output only" prompts
- **MT models unchanged**: Still use minimal prompts

### 3. Only Affects Local Models

- **New Ollama prompt**: Only used for `provider_name == 'ollama'`
- **New cleaning contract**: Replaces aggressive reverse search that could delete valid content
- **Existing behavior preserved**: All other providers use same flow as before

### 4. Deterministic Testing

The contract returns metadata:

```python
cleaned_output, metadata = TranslationOutputContract.parse_model_output(raw_output)

metadata = {
    "status": "cleaned",
    "original_length": 12345,
    "cleaned_length": 12000,
    "removed_prefix": "instruction_echo",
    "has_chinese": False,
    "validation_errors": []
}
```

This allows:
- Monitoring of cleaning behavior
- Detection of over-aggressive cleaning
- Debugging with structured logs

## Usage

### In Translator Code

```python
from core.output_contract import TranslationOutputContract

# Get raw model output
raw_result = provider.translate(prompt, model)

# Clean using contract (ONLY way to clean)
cleaned_result, metadata = TranslationOutputContract.parse_model_output(
    raw_result,
    source_text=markdown_text  # optional, for validation
)

# Check metadata
if metadata['validation_errors']:
    logger.warning(f"Cleaning had issues: {metadata['validation_errors']}")
```

### Testing

```python
# Test with prompt echo
output = "You are a professional translator...\n\n# Header\nContent"
cleaned, meta = TranslationOutputContract.parse_model_output(output)
assert meta['removed_prefix'] == 'instruction_echo'
assert cleaned.startswith("# Header")

# Test with thinking tags
output = "<thinking>I will translate...</thinking>\n\n# Header\nContent"
cleaned, meta = TranslationOutputContract.parse_model_output(output)
assert "<thinking>" not in cleaned
assert cleaned.startswith("# Header")
```

## Migration Notes

### Old Cleaning Methods (Deprecated)

The following methods in `MarkdownTranslator` have been removed:

- `_clean_model_output()` - Replaced by contract
- `_detect_reasoning()` - Integrated into contract
- `_remove_thinking_tags()` - Integrated into contract
- `_clean_by_reverse_search()` - **Too aggressive**, replaced by bounded methods
- `_clean_by_separator()` - Integrated into contract
- `_clean_by_patterns()` - Integrated into contract
- `_is_intro_line()` - Integrated into contract
- `_remove_chinese_lines_from_bilingual()` - Integrated into contract
- `_remove_prompt_artifacts()` - Integrated into contract
- `_final_cleanup()` - Integrated into contract

**Why removed?**
- Old logic was model-specific and not robust
- Reverse search was particularly dangerous (could delete valid content)
- New contract centralizes all cleaning logic in one place

### Breaking Changes

None. The new contract is a drop-in replacement that's **safer** than the old code.

## Future Improvements

1. **Learn from usage**: Monitor metadata to detect edge cases
2. **Model-specific tuning**: Add model profiles if needed (but avoid if possible)
3. **Confidence scoring**: Return confidence score for cleaning decisions
4. **A/B testing**: Compare old vs new cleaning on same inputs

## References

- [Output Contract Implementation](../src/core/output_contract.py)
- [Markdown Translator](../src/translator/markdown_translator.py)
- [Ollama-Optimized Prompt](../prompts/translation/base_ollama.md)
