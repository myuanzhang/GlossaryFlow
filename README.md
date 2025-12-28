# GlossaryFlow

> 🌿 **Glossary + Flow** - 智能术语表驱动的可控翻译流程

一个基于 LLM 的智能文档翻译系统，专注于**术语一致性**和**可控翻译流程**，完美支持 Markdown 格式的中英文翻译。

## ✨ 特性

- 🎯 **术语管理核心**: 支持自定义术语表，确保专业术语翻译一致性
- 🚀 **多模型支持**: OpenAI、DeepSeek、Mimo、通义千问、Ollama，支持自定义
- 📝 **格式保持**: 完美保留 Markdown 格式（表格、代码块、列表等）
- 💻 **友好界面**: 基于 React + Ant Design 的现代化 Web 界面
- 🌐 **多种使用方式**: Web 界面、命令行工具、API 调用
- 🔧 **可控流程**: 灵活的翻译配置和进度控制

## 📸 界面预览

> （可以添加项目截图）

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- API Keys (至少一个 LLM Provider)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/myuanzhang/GlossaryFlow.git
cd GlossaryFlow
```

2. **后端设置**
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入您的 API Keys
# 至少配置一个 Provider
```

4. **前端设置**
```bash
cd frontend
npm install
```

> ⚠️ **IDE 提示找不到模块？**
>
> 如果在 IDE 中看到 `找不到模块"react"` 等错误提示，这是正常的！
>
> 原因：项目删除了 `node_modules/` 以减小体积（从 314MB 减少到 1.7MB）
>
> 解决：运行 `cd frontend && npm install` 即可自动安装所有依赖，错误提示会消失
>
> 详见 [开发环境设置指南](docs/开发环境设置指南.md)

5. **启动服务**

**终端 1 - 启动后端**:

```bash
python main.py
# 后端运行在 http://localhost:8000
```

**终端 2 - 启动前端**:
```bash
cd frontend
npm run dev
# 前端运行在 http://localhost:5173
```

6. **访问应用**
打开浏览器访问 http://localhost:5173

## 📖 使用指南

### Web 界面翻译
1. 上传 Markdown 文档
2. 选择翻译服务商和模型
3. **（推荐）上传术语表文件** - 确保专业术语翻译一致性
4. 点击"开始翻译"
5. 查看翻译进度
6. 下载翻译结果

### 使用术语表（核心功能）

创建 JSON/YAML 格式的术语表文件：

**JSON 格式**：
```json
{
  "大语言模型": "Large language model"
}
```

**YAML 格式**：
```yaml
大语言模型: Large language model
```

在翻译时上传术语表文件，系统会自动应用这些术语翻译，确保整篇文档的术语一致性。

**为什么术语表很重要？**

- ✅ 确保专业术语翻译统一
- ✅ 避免同一词汇前后翻译不一致
- ✅ 提高技术文档翻译质量
- ✅ 符合行业术语规范

### 命令行使用
项目提供命令行工具 `translate.py`，适合批量处理或脚本化使用：

```bash
# 基础翻译
python translate.py input.md output.md --provider openai

# 指定模型
python translate.py input.md output.md --provider deepseek --model deepseek-reasoner

# 使用术语表
python translate.py input.md output.md --provider qwen --glossary data/glossary.json
```

## 🎯 核心优势

### 1. 术语一致性保证
- **问题**：普通翻译工具对同一术语可能翻译成不同词汇
- **解决**：GlossaryFlow 通过术语表强制统一翻译
- **效果**：整篇文档术语翻译 100% 一致

### 2. 可控翻译流程
- **实时进度**：WebSocket 推送，随时了解翻译状态
- **灵活配置**：选择最适合的 LLM 模型
- **质量保证**：支持术语表 + 多种翻译策略

### 3. 格式完美保持
- **Markdown 原样**：表格、代码块、列表、链接等
- **排版保持**：不破坏原文档结构
- **多格式支持**：JSON/YAML 术语表、Markdown 文档

## 🔧 配置说明

### 支持的翻译服务商

| Provider | 模型示例 | 说明 |
|----------|---------|:-----|
| OpenAI | GPT-4, GPT-3.5 | 在线API |
| DeepSeek | deepseek-chat, deepseek-reasoner | 在线API |
| Mimo | mimo-v2-flash | 在线API |
| Qwen | qwen-mt-flash, qwen3-max | 在线API |
| Ollama | llama2, mistral | 本地部署 |

🤖支持自定义所需大语言模型，集成新的 LLM 服务请参考[新增翻译服务商指南](docs/新增翻译服务商指南.md)。

### 环境变量配置

详见 `.env.example` 文件。

## 🏗️ 项目结构

```
glossary-flow/
├── src/              # 后端代码
│   ├── api/         # FastAPI 接口
│   ├── providers/   # LLM Provider 实现
│   ├── translator/  # 翻译核心逻辑
│   └── core/        # 核心功能
├── frontend/        # 前端代码
│   └── src/        # React 组件
├── prompts/         # LLM 提示词模板
├── docs/            # 项目文档
└── data/            # 示例数据和术语表
```

## 📚 文档

- [REST API 规范](docs/RESTAPI规范.md) - API 接口文档
- [提示词管理系统指南](docs/提示词管理系统指南.md) - 优化翻译效果

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](docs/CONTRIBUTING.md)。

### 开发规范
- 遵循现有代码风格
- 添加必要的测试
- 更新相关文档
- 确保所有测试通过

## 📝 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

* 感谢开源社区的支持

- 感谢各个 LLM Provider 提供的服务

## ⭐ Star History

如果 GlossaryFlow 对你有帮助，请给个 Star 支持！

---

**GlossaryFlow** - 让术语翻译保持一致性，让翻译流程更加可控。

**注意**: 请勿将包含真实 API Keys 的 `.env` 文件提交到 Git 仓库！
