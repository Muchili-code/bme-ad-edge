# start_demo.sh 使用说明

`start_demo.sh` 用于在 WSL Ubuntu 内一键启动 AD dMRI 边缘端 Demo 的 FastAPI 后端和 Vite 前端。

## 运行方式

从 Windows 侧执行：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "./start_demo.sh"
```

或已经进入 WSL 并位于项目根目录时执行：

```bash
./start_demo.sh
```

脚本必须在 Linux/WSL 内运行。不要在 Windows PowerShell、CMD 或 Git Bash 中直接调用项目内的 Python、Node、npm、uvicorn 或 Vite。

## 启动前检查

脚本会读取 `.env` 中的以下配置：

```text
APP_HOST
BACKEND_PORT
FRONTEND_PORT
CASE_ROOT
OUTPUT_OVERWRITE
```

如果 `.env` 不存在，先从 `.env.example` 复制：

```bash
cp .env.example .env
```

脚本还会检查：

- `CASE_ROOT` 指向的病例包目录存在，并且至少包含一个病例目录。
- `.venv/bin/python` 存在，后端使用该虚拟环境启动。
- `.venv` 中已安装 `uvicorn`。
- `frontend/node_modules` 存在。
- `node` 和 `npm` 的实际解析结果，即 `command -v node` 与 `command -v npm`，必须是 Linux/WSL 路径，而不是 `/mnt/c` 或 `/mnt/d` 下的 Windows 工具。

如果你在交互式 WSL 终端中看到：

```bash
command -v node
command -v npm
type -a npm
```

其中 `command -v node` 和 `command -v npm` 指向 `/home/hp/.nvm/versions/node/...`，但 `type -a npm` 后面仍列出 `/mnt/...` 的 Windows npm，这是可以接受的。脚本只使用实际优先解析到的 Linux/WSL `node` 和 `npm`。

Codex App 或非交互 WSL shell 有时不会自动加载 nvm。`start_demo.sh` 会在找不到 Linux `node/npm` 时主动尝试把 `$HOME/.nvm/versions/node/*/bin` 中最新版本加入本次脚本 PATH。

## 启动结果

默认访问地址：

```text
Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:5173
```

启动后脚本会轮询 `/api/health`。按 `Ctrl+C` 会同时清理后端和前端子进程。

## Ctrl+C 后仍看到旧页面怎么办

`start_demo.sh` 会递归终止它启动的 FastAPI、npm 和 Vite 子进程。若按 `Ctrl+C` 后浏览器仍显示其他系统页面，例如旧的 CAPD 页面，先区分是“服务仍在运行”还是“浏览器缓存/其他端口服务”：

```bash
ss -ltnp '( sport = :8000 or sport = :5173 )'
curl -i --max-time 2 http://127.0.0.1:8000/api/health
curl -i --max-time 2 http://127.0.0.1:5173/
```

如果 `ss` 没有 8000/5173 监听，且 `curl` 连接失败或超时，说明本 Demo 已停止。此时浏览器里残留的页面通常来自旧标签页、缓存、service worker，或 Windows 宿主机/其他项目曾经运行过的服务。请强制刷新、关闭旧标签页，或在 Windows 侧用端口查询工具确认是否有其他进程占用 8000。

Windows 侧可在 PowerShell 中查看端口：

```powershell
netstat -ano | findstr ":8000 :5173"
```

## Demo 边界

本边缘端 Demo 读取赛前准备好的本地病例包，并在本地执行简化 DTI/V1/RI 后处理。它不会在边缘端真实运行完整 DisC-Diff、FreeSurfer 或全脑配准。
