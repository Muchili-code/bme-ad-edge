# 模块 00：工程骨架与共享配置

## 目标

建立边缘端工程基础结构，让数据、后端、前端、部署模块可以按契约并行推进。

## 写入范围

- `ad-edge-demo/` 根结构
- `.env.example`
- 基础 README
- 必要的空目录

## 任务

1. 创建工程根目录结构。
2. 创建 `frontend/`、`backend/`、`scripts/`、`data/cases/`、`docs/`。
3. 创建 `.env.example`，字段符合 `detail plan.md`。
4. 创建最小 README，说明 WSL 运行原则。
5. 不安装依赖，不写完整业务代码。

## 验收

- 目录结构存在。
- `.env.example` 不含个人绝对路径。
- README 明确依赖安装和运行在 WSL 内完成。
