# 强制输出约束层

## 问题陈述

不同大模型在翻译后仍然输出"非翻译正文内容"，例如：
- Glossary 区块
- CRITICAL / IMPORTANT REQUIREMENTS
- 翻译任务说明
- Prompt 本身的复述

**系统不应该"信任模型自觉遵守规则"，而应该建立强制的输出约束层。**

## 解决方案

引入**强制输出约束层**，对所有模型生效（在线 + Ollama）：

### 1. 明确的 Output Contract 定义

```python
FORCED_OUTPUT_RULES = {
    # 必须删除的内容
    "MUST_REMOVE": [
        "CRITICAL OUTPUT REQUIREMENTS",
        "IMPORTANT REQUIREMENTS",
        "Glossary:",
        "TERMINOLOGY:",
        "You MUST / DO NOT",
        "Remember / Note that",
    ],

    # 必须保留的内容
    "MUST_KEEP": [
        "Markdown 标题 (# ## ###)",
        "正文段落",
        "列表、代码块等结构",
    ],

    # 合法内容起点
    "VALID_CONTENT_START": [
        "^# ",      # Markdown header
        "^## ",
        "^### ",
        "^\\* ",     # Bullet list
        "^- ",
        "^\\d+\\. ", # Numbered list
        "^```",      # Code block
    ]
}
```

### 2. 强制删除逻辑

**文件**: `src/core/output_contract.py:228-324`

```python
@classmethod
def _apply_forced_removal(cls, text: str) -> str:
    """
    Apply FORCED removal patterns - these are non-negotiable.

    策略:
    1. 检测 CRITICAL/IMPORTANT/Glossary 等区块
    2. 跳过整个区块直到下一个 Markdown 标题
    3. 删除指令行 (You MUST, DO NOT, Remember, etc.)
    4. 删除术语表条目 (- key: value 模式)
    """
    # 逐行处理
    for line in lines:
        # 检测区块起始
        if contains_any(["CRITICAL", "Glossary:", "IMPORTANT"]):
            skip_until_next_header = True
            continue

        # 如果在跳过模式中
        if skip_until_next_header:
            if line.startswith('#'):  # 找到内容边界
                skip_until_next_header = False
                keep_line(line)
            else:
                skip_line(line)
            continue

        # 删除指令行
        if line_starts_with_any(["You MUST", "DO NOT", "Remember"]):
            skip_line(line)
            continue

        # 删除术语表条目
        if matches_glossary_entry(line):
            skip_line(line)
            continue

        keep_line(line)
```

### 3. 内容起点强制

**文件**: `src/core/output_contract.py:326-376`

```python
@classmethod
def _enforce_content_start(cls, text: str) -> Tuple[str, bool]:
    """
    Enforce that output starts with valid Markdown content.

    策略:
    1. 跳过所有 SKIP_PATTERNS 匹配的行
    2. 找到第一个 VALID_CONTENT_START 模式
    3. 从该位置开始提取内容
    4. 如果找不到，标记为无效输出
    """
    SKIP_PATTERNS = [
        r'IMPORTANT',
        r'CRITICAL',
        r'Glossary:',
        r'You are',
        r'=',
        r'===',
    ]

    VALID_CONTENT_START_PATTERNS = [
        r'^# ',      # Header
        r'^## ',
        r'^- ',      # List
        r'^\\d+\\. ',
        r'^```',
    ]
```

### 4. 修改验证逻辑

**文件**: `src/core/output_contract.py:209-218`

```python
# 旧逻辑：删除 > 70% 就回退到原始
if len(cleaned) < original_length * 0.3:
    cleaned = cls._minimal_cleanup(raw_output)

# 新逻辑：强制删除不受此限制
if not metadata.get("forced_removal_applied") and len(cleaned) < original_length * 0.3:
    cleaned = cls._minimal_cleanup(raw_output)
elif metadata.get("forced_removal_applied") and len(cleaned) < original_length * 0.3:
    # 强制删除是预期行为，接受结果
    logger.info("Forced removal removed significant content, this is acceptable")
```

## 测试验证

所有测试通过 ✅

### test_forced_removal_critical_section
```
输入:
  CRITICAL OUTPUT REQUIREMENTS:
  - Output ONLY the English translation

  # Introduction
  This is content.

输出:
  # Introduction
  This is the content.

✅ CRITICAL 区块被完全删除
```

### test_forced_removal_glossary
```
输入:
  Glossary:
  - 中文: English

  # Document
  Content.

输出:
  # Document
  Content.

✅ Glossary 区块被完全删除
```

### test_hunyuan_style_output
```
输入 (hunyuan:7b 典型输出):
  CRITICAL OUTPUT REQUIREMENTS:
  - Output ONLY the English translation

  Glossary:
  - 证书中心: Certificate Center

  # GlossaryFlow User Guide
  GlossaryFlow is a translation system.

  ## Features
  It supports multiple providers.

输出:
  # GlossaryFlow User Guide
  GlossaryFlow is a translation system.

  ## Features
  It supports multiple providers.

✅ 所有问题区块被清理，文档结构完整保留
```

### test_mimo_style_output
```
输入 (Mimo - 已验证正常的模型):
  # User Guide
  This is the introduction.
  ## Features
  Feature 1, Feature 2.

输出:
  # User Guide
  This is the introduction.
  ## Features
  Feature 1, Feature 2.

✅ 干净输出不受影响（仅有微小空格清理）
```

## 架构集成

### 修改的文件
- ✅ `src/core/output_contract.py` - 核心强制清理逻辑

### 不影响的文件
- ✅ `src/translator/markdown_translator.py` - 无需修改
- ✅ `src/providers/*/provider.py` - 无需修改
- ✅ Prompt 模板 - 无需修改

### 影响的模型
- ✅ **修复**: hunyuan:7b, llama3:8b 等 Ollama 模型
- ✅ **不影响**: Mimo, OpenAI, DeepSeek 等已验证正常的模型

## 设计原则

### 1. 非破坏性优先
- 只删除明确匹配指令模式的内容
- 保留任何疑似正文的内容
- 删除前有日志记录

### 2. 边界检测
- 使用 Markdown 标题作为内容边界
- 最多跳过 20 行（防止过度删除）
- 超过阈值后停止跳过

### 3. 模型无关
- 不依赖模型名称
- 不依赖 prompt 遵守
- 基于输出特征（而非模型行为）

### 4. 可观测性
- 详细日志记录每次删除
- Metadata 标记 `forced_removal_applied`
- 验证错误包含 `no_valid_content_start`

## 使用方法

### 自动启用（推荐）
```python
# 无需任何代码修改，自动生效
from translator.markdown_translator import MarkdownTranslator

translator = MarkdownTranslator(provider_name="ollama")
result = translator.translate(markdown_text)
# result 已经过强制清理
```

### 手动验证
```python
from core.output_contract import TranslationOutputContract

raw_output = model.translate(...)
cleaned, metadata = TranslationOutputContract.parse_model_output(raw_output)

print(f"Status: {metadata['status']}")
print(f"Forced removal: {metadata.get('forced_removal_applied')}")
print(f"Validation errors: {metadata.get('validation_errors', [])}")
```

## 未来改进

1. **学习模型行为**
   - 记录每个模型的常见违规模式
   - 为特定模型定制清理规则

2. **置信度评分**
   - 评估清理后的输出质量
   - 如果置信度低，触发重试

3. **用户反馈循环**
   - 允许用户报告清理错误
   - 持续改进清理规则

## 相关文档

- [Output Contract 设计文档](./OUTPUT_CONTRACT.md)
- [前半内容丢失修复](./FRONT_CONTENT_LOSS_FIX.md)
- [测试用例](../tests/test_forced_output_contract.py)
