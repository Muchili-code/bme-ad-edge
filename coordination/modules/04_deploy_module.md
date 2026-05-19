# 模块 04：WSL 部署、一键启动与验收测试

## 目标

确保项目能在 WSL Ubuntu 中安装、启动、测试，并为树莓派 5 / 香橙派迁移保留一致路径和脚本。

## 写入范围

- `start_demo.sh`
- `.env.example`
- `docs/`
- 部署相关测试脚本

## 依赖契约

- `coordination/PROCESS_RULES.md`
- `coordination/ACCEPTANCE_CHECKLIST.md`

## 任务

1. 编写 WSL 安装说明。
2. 编写 `start_demo.sh`。
3. 检查脚本是否在 Linux/WSL 环境执行。
4. 启动后端和前端。
5. 输出本地访问地址。
6. 编写断网测试、反虚跑测试、触摸屏测试说明。
7. 更新 `coordination/status/deploy.status.md`。

## 验收

- WSL 中可一键启动。
- Windows shell 直接运行时能提示改用 WSL。
- `.env` 可切换病例目录。
- 反虚跑测试步骤清晰可执行。
