# Bug Fix: Missing Front Content in Translated Documents

## 问题症状

翻译后的文档缺少**前面的一部分内容**，而不是后半部分截断。

## 根本原因

### 问题 1: Markdown 标题被误判为"内容起始标记"

**位置**: `src/core/output_contract.py:29-43`

**原始代码**:
```python
CONTENT_START_MARKERS = [
    # ...
    # Markdown document start (strong signal)
    '# ',  # ⚠️ 问题：这是一个合法的内容模式！
    # ...
]
```

**问题机制**:

1. 当翻译结果正常输出时（无 prompt echo），第一个标题（如 `# Introduction`）会被检测到
2. `_extract_from_start_marker()` 方法检测到这一行包含 `'# '`
3. **跳过这一行**（`result_start = i + 1`），再跳过空行
4. 从下一个标题开始提取
5. **结果**: 第一个标题及其内容全部丢失

**示例**:
```markdown
# Introduction          ← 被当作 marker，跳过
This is the intro...     ← 随之丢失

# Chapter 1              ← 从这里开始提取
Content here...
```

### 问题 2: 短段落被误判为指令文本

**位置**: `src/core/output_contract.py:184-244`

**原始代码**:
```python
looks_like_content = (
    line.startswith('#') or
    len(line) > 50 or  # ⚠️ 太严格！50 字符的阈值太高
    any(marker in line for marker in ['```', '**', '*', '[', ']'])
)

if looks_like_content:
    break

# Short line without content markers - probably still instruction
content_start_idx = i + 1  # ⚠️ 跳过了这一行！
```

**问题机制**:

1. 如果第一个段落短于 50 个字符（如 `Some introductory text without a header.`）
2. 不以 `#` 开头，不包含 markdown 符号
3. 被误判为"指令文本"，跳过
4. **结果**: 第一个段落丢失

## 修复方案

### 修复 1: 移除 Markdown 标题作为标记

**文件**: `src/core/output_contract.py:27-43`

```diff
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
-
-     # Markdown document start (strong signal)
-     '# ',
  ]

+ # ⚠️ DO NOT include '# ' (markdown headers) as markers!
+ # Headers are legitimate content, not instruction boundaries.
```

**原理**: 只有**明确的指令分隔符**才能作为标记，Markdown 标题是合法内容。

### 修复 2: 改进内容识别逻辑（保守策略）

**文件**: `src/core/output_contract.py:184-274`

**改进点**:

1. **降低长度阈值**: 从 50 字符 → 30 字符
2. **添加保守原则**: 宁可保留指令 echo，不删除合法内容
3. **添加连续指令计数**: 只有连续多行指令才继续跳过
4. **添加边界检查**: 检查删除行数（< 20 行）

```python
# Content indicators (conservative check):
# - Starts with Markdown header (# ## ###)
# - Is reasonably long (> 30 chars, was 50)  ← 放宽
# - Contains markdown patterns (```, **, *, [, etc.)
# - Is NOT a short numbered list item
looks_like_content = (
    line.startswith('#') or
    len(line) > 30 or  # Relaxed from 50 to 30
    (any(marker in line for marker in ['```', '**', '*', '[', ']']) and len(line) > 20)
)

# Additional safety: only skip if we've seen multiple instruction lines
if consecutive_instruction_lines >= 2:
    content_start_idx = i + 1
    continue

# Otherwise, be conservative and assume this is content
break
```

### 修复 3: 标记匹配改为"行首匹配"

**文件**: `src/core/output_contract.py:263-267`

```diff
  for marker in cls.CONTENT_START_MARKERS:
-     if marker in line_lower:  # ⚠️ 包含匹配，会误判
+     if line_lower.startswith(marker.lower()):  # ✅ 行首匹配，更精确
```

**原理**: 只有**行首**匹配标记的才是指令分隔符，避免在内容中误匹配。

## 验证

### 测试用例

所有测试通过 ✅

1. **`test_first_header_not_treated_as_marker`**
   - 第一个标题 `# Introduction` 被正确保留
   - 标题下的内容不丢失

2. **`test_explicit_marker_still_works`**
   - 明确的指令标记 `Translation:` 仍能被检测和移除
   - 不影响原有的 prompt echo 清理功能

3. **`test_header_in_middle_of_text`**
   - 中间的标题不被误判
   - 短段落（< 50 字符）不被误删

4. **`test_real_world_scenario`**
   - 真实翻译文档的完整流程验证
   - 所有章节内容完整保留

### 回归测试

```bash
python tests/test_output_contract_fix.py
```

结果：✅ ALL TESTS PASSED

## 影响范围

### 修改的文件

- `src/core/output_contract.py` - 核心修复

### 不影响的文件

- `src/translator/markdown_translator.py` - 无需修改
- `src/providers/*/provider.py` - 无需修改
- 其他翻译流程代码 - 无需修改

### 影响的模型类型

✅ **修复了以下模型的前半内容丢失问题**:
- Ollama 本地模型（llama3, hunyuan, 等）
- 所有输出以 Markdown 标题开头的模型

✅ **不影响以下已验证正常工作的模型**:
- OpenAI（GPT-3.5, GPT-4）
- DeepSeek
- 其他云服务模型

## 设计原则

### 1. 保守策略

**宁可保留指令 echo，不删除合法内容**

- 如果不确定是否为内容，假设它是内容
- 只删除**明确匹配**的指令模式
- 避免过于激进的启发式判断

### 2. 边界检查

- 限制删除行数（< 20 行）
- 验证删除后内容长度（> 20 字符）
- 如果删除太多（> 70%），回退到最小清理

### 3. 明确模式

**只使用"指令专用"模式作为标记**:
- ✅ `Translation:`, `翻译结果：` 等 - 明确的指令分隔
- ❌ `# `, `##` 等 - 合法的 Markdown 内容

## 未来改进

1. **基于长度的智能检测**
   - 如果源文档有 10 个标题，输出也应该有 ~10 个
   - 验证标题数量一致性

2. **基于位置的检测**
   - 检测删除是否发生在文档开头
   - 如果第一个标题丢失，触发警告

3. **模型行为学习**
   - 记录每个模型的输出模式
   - 为特定模型定制清理策略

## 相关文档

- [Output Contract 设计文档](./OUTPUT_CONTRACT.md)
- [翻译 Pipeline 架构](../src/translator/README.md)
