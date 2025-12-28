# REST API 规范

本文档定义了连接前端 Web 界面与现有 Python TranslationAgent 契约的 REST API 层。所有 API 端点严格遵循现有数据契约和状态管理模式。

## 目录

- [API 概述](#api-概述)
- [身份认证](#身份认证)
- [核心端点](#核心端点)
- [系统状态](#系统状态)
- [错误响应](#错误响应)
- [WebSocket 事件](#websocket-事件)
- [请求/响应示例](#请求响应示例)

---

## API 概述

### 基础 URL
```
http://localhost:8000/api/v1
```

### Content-Type
除非另有说明,所有请求必须使用 `application/json`。

### 契约合规性
此 REST API 严格封装现有的 `TranslationAgent` Python 接口。除核心 API 契约中定义的内容外,不引入任何新字段或行为。

---

## 身份认证

### 当前状态：未实现
根据项目约束,身份认证**明确排除**在当前范围之外。

### 请求头（未来使用）
```http
Authorization: Bearer <token>
X-Request-ID: <uuid>
```

---

## 核心端点

### 1. 开始翻译

启动新的翻译任务并返回用于进度跟踪的任务 ID。

```http
POST /api/v1/translate
```

**请求体：**
```json
{
  "source_markdown": "string",
  "glossary": {"中文术语": "英文翻译"},
  "llm_config": {
    "provider": "openai|ollama",
    "model": "string",
    "temperature": 0.3,
    "extra_options": {}
  }
}
```

**响应：**
```json
{
  "success": true,
  "job_id": "uuid-v4-string",
  "estimated_duration_ms": 30000
}
```

**验证错误（400）：**
```json
{
  "success": false,
  "error": {
    "code": "INPUT_EMPTY",
    "message": "输入文件为空",
    "details": {}
  }
}
```

### 2. 获取翻译状态

获取翻译任务的当前状态和进度。

```http
GET /api/v1/translate/{job_id}/status
```

**响应：**
```json
{
  "success": true,
  "status": "idle|validating|translating|completed|error",
  "progress": 85,
  "start_time": "2025-01-19T10:30:00Z",
  "estimated_completion": "2025-01-19T10:31:00Z",
  "warnings": ["检测到大文档"],
  "result": {
    "translated_markdown": "string",
    "metadata": {
      "provider_used": "openai",
      "model_used": "gpt-4",
      "glossary_applied": true,
      "warnings": []
    }
  }
}
```

**任务未找到（404）：**
```json
{
  "success": false,
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "翻译任务未找到"
  }
}
```

### 3. 获取翻译结果

下载最终的翻译 Markdown 文件。

```http
GET /api/v1/translate/{job_id}/result
```

**响应（Content-Type: text/markdown）：**
```markdown
# English Title
Translated content...
```

**响应头：**
```http
Content-Disposition: attachment; filename="translated.md"
X-Job-Metadata: {"provider_used": "openai", "duration_ms": 25000}
```

### 4. 取消翻译

取消正在进行的翻译任务。

```http
DELETE /api/v1/translate/{job_id}
```

**响应：**
```json
{
  "success": true,
  "message": "翻译任务已取消"
}
```

---

## 系统状态

### 1. 获取可用服务商

返回可用的 LLM 服务商列表。

```http
GET /api/v1/providers
```

**响应：**
```json
{
  "success": true,
  "providers": ["openai", "ollama"]
}
```

### 2. 检查服务商状态

检查特定服务商是否可用且已配置。

```http
GET /api/v1/providers/{provider_name}/status
```

**响应：**
```json
{
  "success": true,
  "available": true,
  "provider": "openai",
  "model": "gpt-4",
  "configuration_status": "configured"
}
```

### 3. 系统健康检查

整体系统健康状态。

```http
GET /api/v1/health
```

**响应：**
```json
{
  "success": true,
  "status": "healthy|degraded|down",
  "available_providers": ["openai", "ollama"],
  "provider_status": {
    "openai": true,
    "ollama": false
  }
}
```

---

## 错误响应

所有错误响应遵循契约定义的格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "用户友好的错误消息",
    "details": {}
  }
}
```

### HTTP 状态码
- `200`: 成功
- `400`: 验证错误
- `404`: 资源未找到
- `500`: 系统错误
- `503`: 服务商不可用

### 错误码映射
| 契约错误码 | HTTP 状态 | 描述 |
|---------------------|-------------|-------------|
| `INPUT_EMPTY` | 400 | 源 Markdown 为空 |
| `INPUT_TOO_LARGE` | 400 | 文档超过 8000 字符 |
| `GLOSSARY_INVALID` | 400 | 术语表格式无效 |
| `PROVIDER_UNCONFIGURED` | 503 | 服务商未配置 |
| `PROVIDER_UNAVAILABLE` | 503 | 服务商暂时不可用 |
| `TRANSLATION_FAILED` | 500 | LLM 翻译错误 |
| `FILE_NOT_FOUND` | 404 | 任务 ID 未找到 |
| `FILE_WRITE_ERROR` | 500 | 结果生成失败 |

---

## WebSocket 事件

用于翻译期间的实时进度更新。

### 连接
```
ws://localhost:8000/ws/translate/{job_id}
```

### 事件类型

#### 1. 状态更新
```json
{
  "type": "status_update",
  "job_id": "uuid",
  "status": "translating",
  "progress": 45,
  "timestamp": "2025-01-19T10:30:30Z"
}
```

#### 2. 警告
```json
{
  "type": "warning",
  "job_id": "uuid",
  "message": "检测到大文档（>50,000 字符）",
  "timestamp": "2025-01-19T10:30:15Z"
}
```

#### 3. 完成
```json
{
  "type": "completed",
  "job_id": "uuid",
  "result": {
    "translated_markdown": "string",
    "metadata": {}
  },
  "timestamp": "2025-01-19T10:31:00Z"
}
```

#### 4. 错误
```json
{
  "type": "error",
  "job_id": "uuid",
  "error": {
    "code": "TRANSLATION_FAILED",
    "message": "翻译服务错误",
    "details": {}
  },
  "timestamp": "2025-01-19T10:30:45Z"
}
```

---

## 请求/响应示例

### 完整翻译流程

#### 1. 开始翻译
```bash
curl -X POST http://localhost:8000/api/v1/translate \
  -H "Content-Type: application/json" \
  -d '{
    "source_markdown": "# 中文标题\n这是中文内容",
    "glossary": {"证书中心": "Certificate Center"},
    "llm_config": {
      "provider": "openai",
      "model": "gpt-4"
    }
  }'
```

#### 2. 接收响应
```json
{
  "success": true,
  "job_id": "12345678-1234-1234-1234-123456789abc",
  "estimated_duration_ms": 30000
}
```

#### 3. 连接 WebSocket 获取进度
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/translate/12345678-1234-1234-1234-123456789abc');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'status_update') {
    updateProgressUI(data.progress);
  }
};
```

#### 4. 最终状态检查
```bash
curl http://localhost:8000/api/v1/translate/12345678-1234-1234-1234-123456789abc/status
```

#### 5. 下载结果
```bash
curl http://localhost:8000/api/v1/translate/12345678-1234-1234-1234-123456789abc/result \
  -o translated.md
```

---

## 后端实现说明

### FastAPI 集成
REST API 应使用 FastAPI 实现,具有以下结构：

```python
from fastapi import FastAPI, WebSocket
from src.agents import TranslationAgent, TranslationInput

app = FastAPI()
translation_agent = TranslationAgent()

@app.post("/api/v1/translate")
async def start_translation(request: TranslationRequest):
    # 将 REST 请求转换为 TranslationInput
    input_data = TranslationInput(...)
    # 启动异步翻译并跟踪任务
    job_id = await translation_service.start_translation(input_data)
    return {"success": True, "job_id": job_id}
```

### 任务管理
- 当前阶段使用内存任务存储
- 任务 ID: UUID v4
- 任务状态机遵循契约规范
- 1 小时后自动清理

### 速率限制
- 当前阶段无速率限制
- 未来阶段将添加

---

## GlossaryFlow 特性说明

### 术语表驱动的翻译
REST API 完全支持 GlossaryFlow 的核心特性：

```json
{
  "glossary": {
    "虚拟私有云": "Virtual Private Cloud",
    "负载均衡器": "Load Balancer",
    "安全组": "Security Group"
  }
}
```

### 多服务商支持
支持的 Provider（通过 `/api/v1/providers` 获取）：
- `openai` - OpenAI GPT 系列
- `deepseek` - DeepSeek 系列
- `mimo` - Mimo 专业翻译模型
- `qwen` - 通义千问系列
- `ollama` - 本地部署模型

### 翻译质量保证
API 确保翻译过程中：
- ✅ 术语翻译一致性（通过 glossary 参数）
- ✅ 格式保持完整（Markdown 结构）
- ✅ 实时进度反馈（WebSocket）
- ✅ 错误处理详细（错误码和消息）

---

**API 版本**: 1.0.0
**契约合规**: 完全符合 TranslationAgent 接口规范
**最后更新**: 2025-01-19

## 相关资源

- [新增服务商指南](新增翻译服务商指南.md) - 集成新的 LLM 服务
- [提示词管理指南](prompt-management-guide.md) - 优化翻译效果
- [贡献指南](../CONTRIBUTING.md) - 如何参与贡献

---

**REST API 规范** - 连接前端与翻译核心的桥梁。
