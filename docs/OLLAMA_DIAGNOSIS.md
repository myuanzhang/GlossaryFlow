# Ollama 模型翻译问题排查指南

## 问题现象

- ✅ **OpenAI / Qwen-MT / DeepSeek**: 翻译正常工作
- ❌ **Ollama 模型**: 无法生成翻译文档

## 诊断步骤（请按顺序执行）

### Step 1: 基础连接检查

```bash
# 1.1 检查 Ollama 服务是否运行
curl -s http://localhost:11434/api/tags | jq .

# 预期输出:
# {
#   "models": [
#     {"name": "llama2:7b", ...},
#     {"name": "llama3:8b", ...}
#   ]
# }

# 1.2 如果服务未运行，启动 Ollama
ollama serve

# 1.3 检查已安装的模型
ollama list

# 1.4 如果没有模型，拉取一个测试模型
ollama pull llama3:8b
```

**检查点**:
- [ ] Ollama 服务响应正常
- [ ] 至少有一个模型已安装
- [ ] 能看到模型列表

---

### Step 2: 模型能力检查

```bash
# 2.1 创建测试脚本
cat > /tmp/test_ollama.py << 'EOF'
import sys
sys.path.insert(0, 'src')

from providers.registry import provider_registry
from core.config import config

print("=" * 60)
print("Ollama Provider 诊断")
print("=" * 60)

# 检查配置
print(f"\n[配置检查]")
print(f"OLLAMA_BASE_URL: {config.ollama_base_url}")
print(f"OLLAMA_MODELS: {config.ollama_models}")
print(f"Default timeout: {config.default_timeout}s")

# 获取 provider
print(f"\n[Provider 初始化]")
try:
    provider = provider_registry.get_or_create("ollama")
    print(f"✅ Provider 创建成功: {provider}")
except Exception as e:
    print(f"❌ Provider 创建失败: {e}")
    sys.exit(1)

# 检查配置状态
print(f"\n[配置状态]")
is_configured = provider.is_configured()
print(f"is_configured(): {is_configured}")

# 健康检查
print(f"\n[健康检查]")
is_healthy, error_msg = provider.health_check()
print(f"is_healthy: {is_healthy}")
print(f"error_msg: {error_msg}")

# 获取模型列表
print(f"\n[可用模型]")
try:
    models = provider.get_available_models()
    print(f"可用模型数量: {len(models)}")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")
except Exception as e:
    print(f"❌ 获取模型列表失败: {e}")

# 模型信息
if models:
    print(f"\n[模型信息]")
    for model_name in models[:3]:  # 只检查前3个
        try:
            info = provider.get_model_info(model_name)
            if info:
                print(f"\n模型: {model_name}")
                print(f"  - max_tokens: {info.max_tokens}")
                print(f"  - capabilities: {info.capabilities}")
                print(f"  - supports_streaming: {info.supports_streaming}")
        except Exception as e:
            print(f"❌ 获取 {model_name} 信息失败: {e}")

print("\n" + "=" * 60)
EOF

# 2.2 运行诊断脚本
python /tmp/test_ollama.py
```

**检查点**:
- [ ] Provider 初始化成功
- [ ] `is_configured()` 返回 True
- [ ] 健康检查通过
- [ ] 能看到至少一个可用模型
- [ ] 模型信息正确显示（max_tokens, capabilities）

---

### Step 3: 基础生成能力测试

```bash
# 3.1 测试简单文本生成
cat > /tmp/test_ollama_generate.py << 'EOF'
import sys
sys.path.insert(0, 'src')

from providers.registry import provider_registry

provider = provider_registry.get_or_create("ollama")
models = provider.get_available_models()

if not models:
    print("❌ 没有可用模型")
    sys.exit(1)

model = models[0]
print(f"使用模型: {model}")
print("=" * 60)

# 测试 1: 简单问答
print("\n[测试 1: 简单问答]")
try:
    result = provider.generate(
        "What is the capital of France? Answer in one word.",
        model=model,
        temperature=0.3
    )
    print(f"✅ 生成成功")
    print(f"结果: {result[:100]}")
except Exception as e:
    print(f"❌ 生成失败: {e}")

# 测试 2: 中文文本
print("\n[测试 2: 中文输入]")
try:
    result = provider.generate(
        "请用一句话介绍北京。",
        model=model,
        temperature=0.3
    )
    print(f"✅ 生成成功")
    print(f"结果: {result[:100]}")
except Exception as e:
    print(f"❌ 生成失败: {e}")

# 测试 3: 长文本
print("\n[测试 3: 长文本]")
long_text = "请翻译以下段落：" + "这是一段测试文本。" * 50
try:
    result = provider.generate(
        long_text,
        model=model,
        temperature=0.3
    )
    print(f"✅ 生成成功")
    print(f"结果长度: {len(result)}")
    print(f"结果预览: {result[:200]}")
except Exception as e:
    print(f"❌ 生成失败: {e}")
    import traceback
    traceback.print_exc()

EOF

python /tmp/test_ollama_generate.py
```

**检查点**:
- [ ] 简单问答测试通过
- [ ] 中文输入测试通过
- [ ] 长文本测试通过（无截断）
- [ ] 所有测试都在合理时间内完成（< 2分钟）

---

### Step 4: 翻译功能对比测试

```bash
# 4.1 创建对比测试脚本
cat > /tmp/test_translation_compare.py << 'EOF'
import sys
sys.path.insert(0, 'src')

from providers.registry import provider_registry

# 测试文本
test_text = """# 测试文档

这是一个测试文档。

## 功能特点

- 特点1
- 特点2

## 总结

本文档测试翻译功能。
"""

print("=" * 60)
print("翻译功能对比测试")
print("=" * 60)

# 测试 Ollama
print("\n[Ollama Provider]")
try:
    ollama_provider = provider_registry.get_or_create("ollama")
    ollama_models = ollama_provider.get_available_models()

    if ollama_models:
        model = ollama_models[0]
        print(f"使用模型: {model}")

        result = ollama_provider.translate(
            test_text,
            source_lang="zh",
            target_lang="en",
            model=model
        )

        print(f"✅ 翻译成功")
        print(f"结果长度: {len(result)}")
        print(f"结果预览:\n{result[:300]}")

        # 检查结果质量
        if result == test_text:
            print("⚠️ 警告: 返回原文（翻译失败）")
        elif not result.strip():
            print("❌ 错误: 返回空字符串")
        else:
            chinese_chars = sum(1 for c in result if '\u4e00' <= c <= '\u9fff')
            chinese_ratio = chinese_chars / len(result) if result else 0
            print(f"中文字符比例: {chinese_ratio:.2%}")

            if chinese_ratio > 0.5:
                print("⚠️ 警告: 中文比例过高，可能未翻译")
            else:
                print("✅ 翻译质量良好")
    else:
        print("❌ 没有可用的 Ollama 模型")

except Exception as e:
    print(f"❌ 翻译失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

# 测试 OpenAI（如果配置了）
print("\n[OpenAI Provider - 对比]")
try:
    openai_provider = provider_registry.get_or_create("openai")

    if openai_provider.is_configured():
        print(f"✅ OpenAI 已配置")

        result = openai_provider.translate(
            test_text,
            source_lang="zh",
            target_lang="en",
            model="gpt-3.5-turbo"
        )

        print(f"✅ 翻译成功")
        print(f"结果长度: {len(result)}")
        print(f"结果预览:\n{result[:300]}")
    else:
        print("⊘ OpenAI 未配置，跳过测试")

except Exception as e:
    print(f"❌ OpenAI 翻译失败: {e}")

EOF

python /tmp/test_translation_compare.py
```

**检查点**:
- [ ] Ollama 翻译调用不抛出异常
- [ ] Ollama 返回非空结果
- [ ] 结果不完全是原文
- [ ] 中文比例 < 50%
- [ ] 如果 OpenAI 可用，对比两者的结果差异

---

### Step 5: Prompt 检测逻辑对比

```bash
# 5.1 检查 full prompt 检测
cat > /tmp/test_prompt_detection.py << 'EOF'
import sys
sys.path.insert(0, 'src')

# 测试文本
test_prompts = {
    "简单翻译": "请翻译以下文本：\n\n测试文本",
    "完整Prompt": """You are a professional translator. Translate ALL Chinese text to English.

IMPORTANT REQUIREMENTS:
1. Translate EVERY Chinese text including:
   - Headings and paragraphs

2. Preserve ALL Markdown formatting exactly

# 测试标题

这是测试内容。"""
}

print("=" * 60)
print("Prompt 检测逻辑测试")
print("=" * 60)

for name, text in test_prompts.items():
    print(f"\n[{name}]")
    print(f"文本长度: {len(text)}")
    print(f"预览: {text[:100]}...")

    # Ollama 检测逻辑
    text_lower = text.lower()
    is_full_prompt_ollama = any(keyword in text_lower for keyword in [
        'translate all chinese text',
        'you are a professional translator',
        'important requirements',
        'preserve all markdown formatting'
    ])

    print(f"Ollama 检测 (is_full_prompt): {is_full_prompt_ollama}")

    # OpenAI 检测逻辑（包含更多关键词）
    is_full_prompt_openai = any(keyword in text_lower for keyword in [
        'translate all chinese text',
        'you are a professional translator',
        'important requirements',
        'preserve all markdown formatting',
        'translate the following markdown document',
        'critical output requirements'
    ])

    print(f"OpenAI 检测 (is_full_prompt): {is_full_prompt_openai}")

    if is_full_prompt_ollama != is_full_prompt_openai:
        print("⚠️ 警告: 两个 Provider 的检测结果不同！")

print("\n" + "=" * 60)
EOF

python /tmp/test_prompt_detection.py
```

**检查点**:
- [ ] 简单翻译文本被正确识别为非 full prompt
- [ ] 完整 Prompt 被正确识别为 full prompt
- [ ] Ollama 和 OpenAI 的检测逻辑一致

---

### Step 6: 翻译器集成测试

```bash
# 6.1 测试完整的翻译器流程
cat > /tmp/test_translator_integration.py << 'EOF'
import sys
import logging
sys.path.insert(0, 'src')

# 启用详细日志
logging.basicConfig(level=logging.INFO)

from translator.markdown_translator import MarkdownTranslator
from core.config import config

print("=" * 60)
print("翻译器集成测试")
print("=" * 60)

# 测试文档
test_doc = """# GlossaryFlow 快速开始

GlossaryFlow 是一个智能翻译系统。

## 安装

使用 pip 安装依赖。

## 配置

配置 API Key。

## 使用

开始翻译文档。
"""

# 测试 Ollama
print("\n[测试 Ollama Provider]")
try:
    translator = MarkdownTranslator(
        provider_name="ollama",
        model_name=None  # 使用默认模型
    )

    print(f"Provider: {translator.provider_name}")
    print(f"Model: {translator.model_name}")
    print(f"Model type: {translator.model_type}")

    result = translator.translate(test_doc)

    print(f"\n✅ 翻译完成")
    print(f"结果长度: {len(result)}")
    print(f"结果预览:\n{result[:400]}")

    # 验证结果
    if result:
        chinese_chars = sum(1 for c in result if '\u4e00' <= c <= '\u9fff')
        chinese_ratio = chinese_chars / len(result)

        print(f"\n[质量检查]")
        print(f"中文字符数: {chinese_chars}")
        print(f"中文比例: {chinese_ratio:.2%}")

        if chinese_ratio < 0.3:
            print("✅ 翻译质量: 良好")
        elif chinese_ratio < 0.7:
            print("⚠️ 翻译质量: 一般（部分未翻译）")
        else:
            print("❌ 翻译质量: 差（基本未翻译）")

    else:
        print("❌ 错误: 返回空结果")

except Exception as e:
    print(f"❌ 翻译失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 OpenAI（对比）
print("\n" + "=" * 60)
print("\n[测试 OpenAI Provider - 对比]")
try:
    translator_openai = MarkdownTranslator(
        provider_name="openai",
        model_name="gpt-3.5-turbo"
    )

    if translator_openai.provider.is_configured():
        result_openai = translator_openai.translate(test_doc)

        print(f"✅ OpenAI 翻译完成")
        print(f"结果长度: {len(result_openai)}")
        print(f"结果预览:\n{result_openai[:400]}")
    else:
        print("⊘ OpenAI 未配置，跳过对比")

except Exception as e:
    print(f"❌ OpenAI 翻译失败: {e}")

print("\n" + "=" * 60)
EOF

python /tmp/test_translator_integration.py
```

**检查点**:
- [ ] Ollama 翻译器初始化成功
- [ ] `model_type` 正确识别（应该是 'chat' 或 'reasoning'）
- [ ] 翻译不抛出异常
- [ ] 返回非空结果
- [ ] 中文比例合理（< 50%）
- [ ] 如果 OpenAI 可用，结果结构相似

---

### Step 7: 超时和性能检查

```bash
# 7.1 检查超时配置
cat > /tmp/test_timeout.py << 'EOF'
import sys
sys.path.insert(0, 'src')

from providers.registry import provider_registry
import time

provider = provider_registry.get_or_create("ollama")
models = provider.get_available_models()

if not models:
    print("❌ 没有可用模型")
    sys.exit(1)

model = models[0]
print(f"测试模型: {model}")
print("=" * 60)

# 测试不同长度的文本
test_cases = [
    ("短文本", "测试文本。" * 10),
    ("中文本", "测试文本。" * 100),
    ("长文本", "测试文本。" * 500),
]

for name, text in test_cases:
    print(f"\n[{name}]")
    print(f"输入长度: {len(text)} 字符")

    try:
        start = time.time()
        result = provider.generate(
            f"请翻译以下文本为英文：\n\n{text}",
            model=model,
            temperature=0.3
        )
        elapsed = time.time() - start

        print(f"✅ 完成")
        print(f"耗时: {elapsed:.2f} 秒")
        print(f"输出长度: {len(result)} 字符")
        print(f"速度: {len(result)/elapsed:.1f} 字符/秒")

        if elapsed > 60:
            print("⚠️ 警告: 耗时超过 60 秒")
        if elapsed > 120:
            print("❌ 错误: 耗时超过 120 秒（可能超时）")

    except Exception as e:
        print(f"❌ 失败: {e}")

print("\n" + "=" * 60)
EOF

python /tmp/test_timeout.py
```

**检查点**:
- [ ] 短文本在 10 秒内完成
- [ ] 中文本在 60 秒内完成
- [ ] 长文本不超时（120 秒内）
- [ ] 性能合理（> 10 字符/秒）

---

### Step 8: 日志级别检查

```bash
# 8.1 启用调试日志重新测试
cat > /tmp/test_with_logging.sh << 'EOF'
#!/bin/bash

cd /Users/bytedance/Documents/02-Project/glossary-flow

export LOG_LEVEL=DEBUG

python -c "
import sys
import logging
sys.path.insert(0, 'src')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from translator.markdown_translator import MarkdownTranslator

test_doc = '''# 测试

这是测试内容。'''

print('启用 DEBUG 日志进行翻译测试...')
print('=' * 60)

translator = MarkdownTranslator(provider_name='ollama')
result = translator.translate(test_doc)

print('=' * 60)
print(f'结果长度: {len(result)}')
print(f'结果: {result}')
" 2>&1 | tee /tmp/translation_debug.log

echo ""
echo "完整日志已保存到: /tmp/translation_debug.log"
echo "请检查日志中的以下关键信息："
echo "  - Translation attempt"
echo "  - Raw translation result"
echo "  - Output cleaning"
echo "  - Translation validation"
EOF

chmod +x /tmp/test_with_logging.sh
/tmp/test_with_logging.sh
```

**检查点**:
- [ ] 日志显示 "Translation attempt 1"
- [ ] 日志显示 "Raw translation result: length=XXX"
- [ ] 日志显示 "Output cleaning: status=cleaned"
- [ ] 日志中没有 "Translation failed"
- [ ] 日志显示 "Translation validation: Chinese ratio < 30%"

---

## 常见问题诊断

### 问题 A: 连接失败

**症状**:
```
❌ Provider 创建失败: ...
❌ is_healthy: False
❌ error_msg: Failed to connect to Ollama
```

**解决方案**:
```bash
# 1. 检查 Ollama 服务
ps aux | grep ollama

# 2. 如果没运行，启动服务
ollama serve &

# 3. 等待服务启动
sleep 5

# 4. 验证服务
curl http://localhost:11434/api/tags
```

---

### 问题 B: 没有可用模型

**症状**:
```
❌ 没有可用的 Ollama 模型
❌ 可用模型数量: 0
```

**解决方案**:
```bash
# 列出已安装的模型
ollama list

# 如果列表为空，拉取一个模型
ollama pull llama3:8b

# 或拉取更大的模型
ollama pull llama3:70b

# 验证模型已安装
ollama list | grep llama3
```

---

### 问题 C: 翻译返回原文

**症状**:
```
✅ 翻译成功
结果长度: 200
中文比例: 100.00%
⚠️ 翻译质量: 差（基本未翻译）
```

**可能原因**:
1. Prompt 检测逻辑错误
2. 模型能力不足
3. Temperature 设置过高

**调试步骤**:
```bash
# 检查 prompt 检测
python /tmp/test_prompt_detection.py

# 检查翻译器集成
python /tmp/test_translator_integration.py

# 尝试降低 temperature
export DEFAULT_TEMPERATURE=0.1
python /tmp/test_translator_integration.py
```

---

### 问题 D: 翻译结果为空

**症状**:
```
✅ 生成成功
结果长度: 0
❌ 错误: 返回空字符串
```

**可能原因**:
1. max_tokens 设置过低
2. 模型输出被截断
3. Output contract 清理过度

**调试步骤**:
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python /tmp/test_translator_integration.py

# 检查日志中的 "Raw translation result"
# 检查日志中的 "Output cleaning removed too much"
```

---

### 问题 E: 超时错误

**症状**:
```
❌ 翻译失败: timeout
❌ 耗时超过 120 秒
```

**解决方案**:
```bash
# 增加超时时间
export DEFAULT_TIMEOUT=300  # 5 分钟
python /tmp/test_translator_integration.py

# 或使用更小的模型
ollama pull llama3:8b  # 使用 8b 而不是 70b
```

---

### 问题 F: 对比 OpenAI 差异巨大

**症状**:
- OpenAI: 完美翻译
- Ollama: 返回原文或乱码

**诊断步骤**:

```bash
# 1. 运行对比测试
python /tmp/test_translation_compare.py

# 2. 对比 Prompt 检测
python /tmp/test_prompt_detection.py

# 3. 检查模型信息
ollama show llama3:8b

# 4. 尝试不同模型
export OLLAMA_MODELS=["llama3:8b", "qwen2:7b"]
python /tmp/test_translator_integration.py
```

---

## 配置对比清单

| 配置项 | OpenAI (正常) | Ollama (问题) | 检查方法 |
|--------|---------------|---------------|----------|
| **API 连接** | OpenAI API | 本地服务 | `curl localhost:11434` |
| **模型列表** | 配置文件 | 动态获取 | `ollama list` |
| **超时设置** | 120s | 600s | `echo $DEFAULT_TIMEOUT` |
| **Prompt 检测** | 6 个关键词 | 4 个关键词 | [Step 5](#step-5-prompt-检测逻辑对比) |
| **API 调用** | `chat.completions` | `/api/generate` | 代码对比 |
| **消息格式** | `{"role": "user", ...}` | `{"prompt": ...}` | 代码对比 |
| **max_tokens** | 动态计算 | 固定或未设置 | [Step 2](#step-2-模型能力检查) |

---

## 快速诊断命令汇总

```bash
# 一键完整诊断
cat > /tmp/full_diagnosis.sh << 'EOF'
#!/bin/bash
echo "================================"
echo "Ollama 翻译问题一键诊断"
echo "================================"
echo ""

echo "[1/7] 基础连接检查"
curl -s http://localhost:11434/api/tags | jq '.models | length' || echo "❌ Ollama 服务未运行"
echo ""

echo "[2/7] 模型列表检查"
ollama list
echo ""

echo "[3/7] 基础生成测试"
python /tmp/test_ollama_generate.py
echo ""

echo "[4/7] 翻译功能对比"
python /tmp/test_translation_compare.py
echo ""

echo "[5/7] Prompt 检测逻辑"
python /tmp/test_prompt_detection.py
echo ""

echo "[6/7] 翻译器集成"
python /tmp/test_translator_integration.py
echo ""

echo "[7/7] 超时和性能"
python /tmp/test_timeout.py
echo ""

echo "================================"
echo "诊断完成"
echo "================================"
EOF

chmod +x /tmp/full_diagnosis.sh
/tmp/full_diagnosis.sh 2>&1 | tee /tmp/ollama_diagnosis_report.txt
```

---

## 下一步

完成上述所有检查后，请提供以下信息：

1. **诊断报告摘要**: `/tmp/ollama_diagnosis_report.txt` 的内容
2. **具体失败步骤**: 哪一步测试失败
3. **错误日志**: 完整的错误堆栈
4. **环境信息**:
   - Ollama 版本: `ollama --version`
   - 使用的模型: `ollama list`
   - Python 版本: `python --version`

这样我才能进一步分析问题的根本原因。
