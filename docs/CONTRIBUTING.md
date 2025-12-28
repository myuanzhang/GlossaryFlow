# 贡献指南

感谢您对 GlossaryFlow 项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告 Bug
1. 在 [Issues](https://github.com/myuanzhang/glossaryflow/issues) 中搜索是否已有相同问题
2. 如果没有，创建新的 Issue，包含：
   - 清晰的标题
   - 详细的复现步骤
   - 期望行为
   - 实际行为
   - 环境信息（OS、Python 版本等）

### 提交代码
1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 开发规范
- 遵循现有代码风格
- Python 代码遵循 PEP 8
- TypeScript/React 代码使用 ESLint 配置
- 添加必要的测试
- 更新相关文档
- 确保所有测试通过

### 新增翻译服务商
请参考 [新增翻译服务商指南](docs/新增翻译服务商指南.md)。

## 代码审查

所有 PR 都需要经过代码审查，请确保：
- 代码清晰易读
- 有适当的注释
- 通过所有测试
- 文档已更新
- 提交信息清晰明确

## 行为准则

- 尊重所有贡献者
- 欢迎不同观点
- 建设性讨论
- 关注问题而非个人
- 保持友好和专业

## 获取帮助

- 查看 [文档](docs)
- 在 [Discussions](https://github.com/myuanzhang/glossaryflow/discussions) 中提问
- 查看 [已有 Issues](https://github.com/myuanzhang/glossaryflow/issues)

## 开发环境设置

1. Fork 并克隆仓库
2. 创建虚拟环境并安装依赖
3. 创建分支进行开发
4. 运行测试确保功能正常
5. 提交 PR 并描述您的更改

### 测试
```bash
# 运行 Python 测试（如果有）
pytest tests/

# 运行前端测试（如果有）
cd frontend
npm test
```

## Pull Request 模板

提交 PR 时，请包含：
- 描述更改的目的
- 相关的 Issue 编号
- 更改的截图（如适用）
- 测试说明

## 许可证

通过贡献代码，您同意您的贡献将使用与项目相同的 MIT 许可证。
