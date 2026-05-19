# Foundation Status

## 当前任务

Foundation 01：创建工程骨架。

## 已完成

- 已确认 00 Foundation 写入范围和共享契约限制。
- 已创建基础目录：`frontend/`、`backend/`、`scripts/`、`data/cases/`、`docs/`。
- 已创建 `.env.example`，使用相对病例路径，不含个人绝对路径。
- 已创建基础 `README.md`，说明 WSL Ubuntu 运行原则、Windows 侧命令格式、依赖目录限制和 Demo 边界。

## 修改文件

- `.env.example`
- `README.md`
- `coordination/status/foundation.status.md`

## 自测结果

- 已检查基础目录存在。
- 已检查 `.env.example` 不包含 `/home/`、`C:\` 或 `\\wsl` 等个人绝对路径。
- 已确认未创建 `node_modules/`、`.venv/`、`dist/`、`build/`。
- 已检查中文 Markdown 文件本体，不含 replacement character 和连续问号。

## 阻塞问题

暂无。

## 需要母进程检查

- 请检查基础 README 对 WSL 运行原则和 Demo 边界的表述是否符合当前项目口径。
