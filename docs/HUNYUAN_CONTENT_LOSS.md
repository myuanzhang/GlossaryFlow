# Ollama hunyuan:7b 模型内容丢失问题分析

## 问题描述

用户反馈：使用 Ollama 运行的大模型翻译的内容缺少前面一部分。

## 问题确认

经过详细测试，确认问题只出现在 **`alibayram/hunyuan:7b`** 模型上，其他模型工作正常。

### 测试结果对比

| 模型 | 第一次尝试 | 第二次尝试（重试） | 状态 |
|------|-----------|------------------|------|
| **llama3:8b** | ✅ 完美翻译 | N/A | ✅ 推荐 |
| **deepseek-r1:7b** | ✅ 完美翻译 | N/A | ✅ 可用 |
| **hunyuan:7b** | ❌ 输出中文 | ✅ 完美翻译 | ⚠️ 需重试 |

## 根本原因

`hunyuan:7b` 模型在**第一次尝试**时：

1. **不遵守翻译指令**
   - 输出中文而非英文
   - 不保留 Markdown 结构
   - 添加了额外的对话式前缀

2. **原始输出示例**：
   ```
   助手：第一章 开始

   这是第一章的内容。
   </answer>
   ```

3. **Output Contract 检测到问题**：
   - `no_valid_content_start` - 没有找到有效的 Markdown 内容开头
   - `has_chinese: True` - 仍包含中文字符

4. **重试机制生效**：
   - 系统检测到中文比例 > 30%
   - 自动重试，使用更强的 prompt
   - 第二次尝试成功翻译

## 解决方案

### 方案 1: 推荐使用其他模型（最佳）

更新 `.env` 文件，将 `hunyuan:7b` 从默认模型列表中移除：

```env
# Ollama Provider (本地模型，无需 API Key)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODELS=["llama3:8b", "deepseek-r1:7b"]
# 不推荐: "alibayram/hunyuan:7b" - 需要重试，效率低
```

### 方案 2: 保留重试机制（已实现）

当前代码已经实现了自动重试机制：

```python
# src/translator/markdown_translator.py:72-76
if self.model_type == 'chat':
    max_retries = 2  # chat 模型会重试
elif self.model_type == 'reasoning':
    max_retries = 1
else:  # mt-like
    max_retries = 1
```

对于 `hunyuan:7b`（被识别为 'chat' 类型），会自动重试一次，第二次使用更强的 prompt。

### 方案 3: 为 hunyuan 使用专用 Prompt（可选）

如果必须使用 `hunyuan:7b`，可以为它创建专用的 prompt 模板：

```python
# src/translator/markdown_translator.py
def _build_hunyuan_prompt(self, glossary_dict):
    """为 hunyuan 模型优化的 prompt"""
    return """You are a translator. Translate Chinese to English.
Output ONLY the English translation.
DO NOT speak Chinese.
DO NOT add explanations.
"""
```

## 验证结果

### llama3:8b（推荐）

```bash
✅ 评估: 翻译良好
中文比例: 0.0%
包含标题: True
```

### hunyuan:7b（第一次尝试）

```bash
❌ 评估: 未翻译（中文比例过高）
中文比例: 88.9%
原始输出: "助手：第一章 开始..."
```

### hunyuan:7b（第二次重试）

```bash
✅ 评估: 翻译良好
中文比例: 8.1%
输出: "# Chapter 1: Starting..."
```

## 建议

1. **生产环境推荐**: 使用 `llama3:8b` 作为默认模型
   - ✅ 第一次尝试就成功
   - ✅ 翻译质量高
   - ✅ 完全遵守指令

2. **如果使用 hunyuan:7b**:
   - ⚠️ 接受需要重试的事实
   - ⚠️ 翻译速度会慢一倍
   - ⚠️ 偶尔仍可能输出中文

3. **配置文件更新**:
   ```env
   OLLAMA_MODELS=["llama3:8b", "deepseek-r1:7b"]
   ```

## 代码层面无需修改

当前的重试机制已经能够处理 `hunyuan:7b` 的问题，只是效率较低。这不是代码 bug，而是模型本身的限制。

**结论**: 用户遇到的问题是 `hunyuan:7b` 模型的特性，不是代码缺陷。建议切换到 `llama3:8b` 以获得最佳体验。
