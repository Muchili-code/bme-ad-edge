# WSL Ubuntu 环境与依赖安装说明

本文档面向 AD dMRI 边缘端 Demo 的开发、部署和协作。所有项目命令都固定在 WSL Ubuntu 内执行，当前项目根目录为：

```text
/home/hp/ad-edge-demo
```

从 Windows 侧调用时，统一使用以下格式：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "<command>"
```

不要在 Windows PowerShell 中直接使用 Windows 版 Node.js、Python、npm、pip、Vite 或 uvicorn 操作本项目。`.venv/`、`node_modules/`、`dist/`、`build/` 等目录只能由 WSL 内工具创建和维护。

## 1. 确认项目位置

在 Windows PowerShell 中执行：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "pwd && test -f README.md && test -d backend && test -d frontend"
```

期望输出第一行为：

```text
/home/hp/ad-edge-demo
```

如果命令提示目录不存在，说明项目没有放在约定的 WSL Linux 文件系统路径。请先把项目放到 WSL 内的 `/home/hp/ad-edge-demo`，不要放在 Windows 盘符路径下再混用 Windows 工具安装依赖。

如果已经进入 WSL 终端，也可以在项目根目录执行：

```bash
pwd
test -f README.md && test -d backend && test -d frontend
```

同样应确认 `pwd` 为 `/home/hp/ad-edge-demo`。

## 2. Codex App / WSL 兼容规则

本项目在 Codex App 中可能显示类似错误：

```text
setup refresh failed with status exit code: 1
```

或 WSL 服务返回异常。遇到这类问题后，立即切换到固定 WSL 命令，不要反复尝试 Windows PowerShell、Windows Node.js、Windows Python 或 Codex Node REPL 来读写 WSL 项目文件。

固定命令格式为：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "<command>"
```

依赖安装、项目运行、测试、脚本执行、代码生成和文件检查都应通过这个 WSL Ubuntu 前缀完成。

## 3. 创建 `.env`

第一次运行前，从 `.env.example` 复制生成本地 `.env`：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "cp .env.example .env"
```

`.env` 是本机运行配置，不应提交到 Git。当前关键配置如下：

```text
CASE_ROOT=./data/cases
BACKEND_PORT=8000
FRONTEND_PORT=5173
OUTPUT_OVERWRITE=true
```

字段说明：

| 字段 | 说明 |
| :--- | :--- |
| `CASE_ROOT` | 病例包根目录。默认 `./data/cases`，表示从项目根目录下读取标准化病例包。迁移到板端时优先改 `.env`，不要改业务代码。 |
| `BACKEND_PORT` | FastAPI 后端端口。默认 `8000`。如端口被占用，可在 `.env` 中改为其他端口。 |
| `FRONTEND_PORT` | Vite 前端端口。默认 `5173`。如端口被占用，可在 `.env` 中调整。 |
| `OUTPUT_OVERWRITE` | 是否允许后端刷新病例 `output/` 下的计算结果。开发阶段通常为 `true`；如需保留已有输出，可改为 `false` 后再运行。 |

不要把个人 Windows 路径、WSL 用户名路径或板端绝对路径写死到代码里。路径差异应通过 `.env` 管理。

## 4. 安装后端依赖

后端依赖必须安装到 WSL 内项目虚拟环境。请在 Windows PowerShell 中执行：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 -m venv .venv"
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc ".venv/bin/python -m pip install -r backend/requirements.txt"
```

后续运行后端脚本、测试或 uvicorn 时，也应使用 `.venv/bin/python` 或 `.venv/bin/uvicorn`，不要裸跑 `python`、`pip`、`pytest` 或 `uvicorn`。

示例：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc ".venv/bin/python -m pytest backend/tests -q"
```

## 5. 安装前端依赖

前端依赖必须在 WSL 内从项目根目录进入 `frontend/` 后安装：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "cd frontend && npm install"
```

不要从 Windows PowerShell 直接进入 `\\wsl.localhost\Ubuntu\home\hp\ad-edge-demo\frontend` 后运行 Windows 版 `npm install`。这样会把 Windows 平台依赖写入 WSL 项目，后续在 Linux/板端运行时容易出现二进制包、软链接、权限或路径问题。

如果你使用 nvm 安装 Node.js，在交互式 WSL 终端里应看到：

```bash
command -v node
command -v npm
```

均指向 `/home/hp/.nvm/versions/node/...`。`type -a npm` 可能还会列出 `/mnt/...` 下的 Windows npm，只要 `command -v npm` 的第一解析结果是 Linux/WSL 路径即可。非交互脚本不会依赖 Windows npm；`start_demo.sh` 会尝试自动发现 nvm 下的 Linux Node/npm。

## 6. GitHub 推拉注意事项

每次拉取、提交或推送前，先在 WSL 内查看状态：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "git status"
```

协作时注意：

1. 不要提交 `.venv/`、`node_modules/`、`dist/`、`build/`。
2. 不要提交病例输出缓存，例如 `data/cases/*/output/` 中由本地运行生成、且不属于任务要求的临时结果。
3. 提交前检查 diff，只提交自己任务范围内的文件。
4. 拉取或合并遇到冲突时，不要用覆盖式操作处理他人修改；先查看冲突内容，再让对应模块负责人或母进程确认。
5. 不要使用 `git reset --hard`、强制 checkout 或强推来清理协作现场，除非母进程明确要求。

推荐检查命令：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "git status --short"
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "git diff -- docs/wsl_setup.md coordination/status/deploy.status.md"
```

## 7. 常见正确命令汇总

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "pwd"
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "cp .env.example .env"
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 -m venv .venv"
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc ".venv/bin/python -m pip install -r backend/requirements.txt"
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "cd frontend && npm install"
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "git status"
```
