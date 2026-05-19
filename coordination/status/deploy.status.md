# deploy status

## 当前任务

04 Deploy 模块已完成部署脚本、部署文档、验收脚本和脚本化最终验收。剩余工作仅为 1024x600 触摸屏人工验收。

Worker A：WSL 环境说明、依赖安装说明、`.env` 使用规则、GitHub 推拉注意事项已完成文档编写，等待母进程检查。

Worker C：最终验收脚本与验收文档已完成，`scripts/run_acceptance.sh` 已通过。

当前拆分：

1. Worker A：WSL 环境说明、依赖安装说明、`.env` 使用规则、GitHub 推拉注意事项。
2. Worker B：`start_demo.sh` 一键启动脚本，负责 WSL/Linux 检查、`.env` 检查、病例包检查、`.venv` 与 Node 依赖检查、后端和前端启动、访问地址输出。
3. Worker C：最终验收脚本/文档，覆盖断网、后端停止、缺失 `sr_dwi_4d.nii.gz`、缺失 `report.json`、mock 输入变化导致输出变化、1024x600 触摸屏检查、Git 状态检查。

## 已完成

- [x] 母进程已阅读所有契约文件、规则文件和任务说明。
- [x] 模块拆分与可复制指令已生成。
- [x] 确认 04 Deploy 写入范围：`start_demo.sh`、`.env.example`、`docs/`、部署相关测试脚本、`coordination/status/deploy.status.md`。
- [x] Worker A 已编写 `docs/wsl_setup.md`，覆盖 WSL 固定命令、项目位置确认、`.env` 创建与字段说明、后端 `.venv/bin/python` 依赖安装、前端 WSL 内 `npm install`、GitHub 推拉注意事项、Codex App / WSL 兼容规则。
- [x] Worker C 已编写 `docs/acceptance_tests.md`，覆盖基础启动、断网、反虚跑、1024x600 触摸屏人工检查、Git 状态与文案边界。
- [x] Worker C 已编写 `scripts/run_acceptance.sh`，脚本化检查健康接口、后端停止、缺失 dMRI、缺失报告、mock dMRI 修改导致 RI 输出变化、Git 跟踪目录与文案边界。

## 修改文件

- `coordination/status/deploy.status.md`
- `docs/wsl_setup.md`
- `docs/acceptance_tests.md`
- `scripts/run_acceptance.sh`

## 自测结果

Worker A 自测通过：

```text
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "test -f docs/wsl_setup.md && sed -n '1,220p' docs/wsl_setup.md"
```

结果：命令退出码 0，已输出 `docs/wsl_setup.md` 前 220 行。

```text
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 - <<'PY'
from pathlib import Path
for p in ['docs/wsl_setup.md', '.env.example', 'coordination/status/deploy.status.md']:
    s = Path(p).read_text('utf-8')
    assert '\ufffd' not in s
    assert ('?' * 3) not in s
print('utf8-ok')
PY"
```

结果：命令退出码 0，输出 `utf8-ok`。

Worker C 自测结果：

```text
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "bash -n scripts/run_acceptance.sh"
```

结果：命令退出码 0。

```text
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "test -f docs/acceptance_tests.md && sed -n '1,260p' docs/acceptance_tests.md"
```

结果：命令退出码 0，已输出 `docs/acceptance_tests.md` 前 260 行。

```text
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 - <<'PY'
from pathlib import Path
for p in ['docs/acceptance_tests.md', 'scripts/run_acceptance.sh', 'coordination/status/deploy.status.md']:
    s = Path(p).read_text('utf-8')
    assert '\ufffd' not in s
    assert ('?' * 3) not in s
print('utf8-ok')
PY"
```

结果：命令退出码 0，输出 `utf8-ok`。

```text
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "bash scripts/run_acceptance.sh"
```

结果：命令退出码 1。除 `./start_demo.sh can start and expose GET /api/health status ok` 失败外，其余脚本化验收均通过：

- fallback 后端用 `.venv/bin/python -m uvicorn` 启动成功。
- `GET /api/health` 返回 ok。
- 前端源码包含后端连接状态与报告页无假报告状态。
- 断网启动说明与无远端 API 硬编码检查通过。
- RI 分析、报告读取、停止后端阻断报告 API、缺失 `sr_dwi_4d.nii.gz` 失败、缺失 `report.json` 返回 `not_completed`、修改 mock dMRI 后 RI 输出变化均通过。
- Git 生成目录未被跟踪、文案边界检查通过。

## 阻塞问题

Worker A 暂无。

当前已解决前置问题：

- 项目根目录已创建本地 `.env`，来源为 `.env.example`；`.env` 是本机运行配置，不提交 Git。
- 已修复 `start_demo.sh` 在非交互 WSL shell 中找不到 nvm Node/npm 的问题：脚本会自动尝试加入 `$HOME/.nvm/versions/node/*/bin` 中最新 Linux Node。
- 已澄清 Node/npm 判定口径：`command -v node` 与 `command -v npm` 必须指向 Linux/WSL 路径；`type -a npm` 后续列出 `/mnt/*` Windows npm 仅表示 PATH fallback，不代表实际使用 Windows npm。

Worker C 暂无业务阻塞；`scripts/run_acceptance.sh` 已全部通过。

## 需要母进程检查

Worker A 需要母进程检查：

- `docs/wsl_setup.md` 是否满足 04 Deploy 模块口径。
- 是否需要进一步补充 `.env.example` 注释；Worker A 当前未修改 `.env.example`，将变量解释集中写入 `docs/wsl_setup.md`。

等待以下 Worker 任务产物：

1. Worker A：`docs/wsl_setup.md`，必要时补充 `.env.example` 注释或相关部署说明。
2. Worker B：`start_demo.sh`，必要时补充 `docs/start_demo.md`。
3. Worker C：`docs/acceptance_tests.md` 与部署相关测试脚本，例如 `scripts/run_acceptance.sh`。

Worker C 需要母进程检查：

- `scripts/run_acceptance.sh` 是否满足最终验收脚本口径。
- `docs/acceptance_tests.md` 中 1024x600 触摸屏人工验收步骤是否足够比赛现场执行。
- Worker B 完成 `start_demo.sh` 后，需要重新运行 `bash scripts/run_acceptance.sh` 验证一键启动项。

母进程后续验收重点：

- 所有运行命令固定在 WSL Ubuntu 内。
- Windows shell 直接运行 `start_demo.sh` 时能提示改用 `wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "./start_demo.sh"`。
- 后端使用 `.venv/bin/python` 或 `.venv/bin/uvicorn`。
- 前端使用 WSL/Linux Node 与 npm。
- 一键启动能同时启动 FastAPI 和 Vite 或生产静态服务。
- 最终验收覆盖反虚跑清单和 1024x600 触摸屏检查。

---

## Worker B 状态：Deploy 02 一键启动脚本

## 当前任务

Worker B 已完成 `start_demo.sh` 一键启动脚本与启动说明。

## 已完成

- [x] 新增 `start_demo.sh`，要求在 Linux/WSL 内运行。
- [x] Windows/非 Linux 环境提示使用 `wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "./start_demo.sh"`。
- [x] 脚本从自身所在目录切换到项目根，不要求用户把 `--cd` 指到 `frontend`。
- [x] 检查 `.env` 是否存在；不存在时提示从 `.env.example` 复制。
- [x] 读取并导出 `APP_HOST`、`BACKEND_PORT`、`FRONTEND_PORT`、`CASE_ROOT`、`OUTPUT_OVERWRITE`。
- [x] 检查 `CASE_ROOT` 存在且至少包含一个病例目录。
- [x] 检查 `.venv/bin/python`，后端用 `.venv/bin/python -m uvicorn backend.main:app` 启动。
- [x] 检查 `frontend/node_modules`，并拒绝 `/mnt/c`、`/mnt/d` 下的 Windows `node`/`npm`。
- [x] 启动后轮询 `/api/health`，失败时输出后端日志片段。
- [x] 前端从项目根进入 `frontend` 后执行 `npm run dev -- --host "$APP_HOST" --port "$FRONTEND_PORT"`。
- [x] 使用 `trap` 在 `Ctrl+C` 或退出时清理后端和前端子进程。
- [x] 输出后端和前端访问地址，并说明边缘端不真实运行完整 DisC-Diff、FreeSurfer 或全脑配准。

## 修改文件

- `start_demo.sh`
- `docs/start_demo.md`
- `coordination/status/deploy.status.md`

## 自测结果

- `bash -n start_demo.sh`：通过。
- `chmod +x start_demo.sh && ./start_demo.sh --help || true`：通过，输出 WSL 启动命令。
- `grep -n '.venv/bin/python\|.venv/bin/uvicorn\|frontend\|npm run dev\|wsl -d Ubuntu' start_demo.sh`：通过，命中后端虚拟环境、前端命令和 WSL 提示。
- `./start_demo.sh || true`：当前按预期停止在 `.env` 缺失检查，并提示 `cp .env.example .env`。

## 阻塞问题

- 当前仓库没有 `.env`，未在 Worker B 写入范围内创建 `.env`。
- 当前 WSL 环境中 `node` 不在 PATH，`npm` 解析为 `/mnt/d/Program Files (x86)/nodejs/npm`，脚本会拒绝使用该 Windows npm。因此未实际启动前端。

## 需要母进程检查

- 创建或确认 `.env` 后，在安装 Linux/WSL Node/npm 的环境中执行完整启动。
- 完整启动后确认：
  - `Backend: http://127.0.0.1:8000`
  - `Frontend: http://127.0.0.1:5173`
  - `/api/health` 返回 `status: ok`

---

## 母进程检查结论

检查时间：2026-05-19。

结论：Worker A/B/C 的部署产物已通过模块母进程初检，但 04 Deploy 尚未进入最终完成状态；当前剩余问题是运行环境未满足一键启动条件，需要修复 `.env` 与 WSL/Linux Node/npm 后复验。

已检查产物：

1. Worker A：`docs/wsl_setup.md` 符合 04 Deploy 口径，已覆盖 WSL 固定入口、依赖安装、`.env` 字段、避免 Windows/WSL 依赖混用、GitHub 推拉注意事项。不强制要求继续修改 `.env.example`。
2. Worker B：`start_demo.sh` 符合一键启动脚本口径，已检查 Linux/WSL、`.env`、病例包、`.venv/bin/python`、`frontend/node_modules`、Linux/WSL Node/npm，并能拒绝 Windows npm/Node。脚本用 `.venv/bin/python -m uvicorn` 启动后端，从项目根进入 `frontend` 启动 Vite，并输出访问地址。
3. Worker C：`docs/acceptance_tests.md` 与 `scripts/run_acceptance.sh` 覆盖断网、后端停止、缺失 `sr_dwi_4d.nii.gz`、缺失 `report.json`、mock 输入变化导致输出变化、Git 状态检查和 1024x600 触摸屏人工验收。

母进程复查结果：

- `bash -n start_demo.sh`：通过。
- `bash -n scripts/run_acceptance.sh`：通过。
- `git ls-files .venv node_modules frontend/node_modules dist build frontend/dist`：无输出，未跟踪依赖或构建目录。
- 文案边界扫描只命中文档中的禁止/否定表述，以及 `docs/start_demo.md` 中“不会在边缘端真实运行完整 DisC-Diff、FreeSurfer 或全脑配准”的边界说明；未发现正向越界宣称。

当前阻塞：

暂无脚本化业务阻塞。母进程复查过程中偶发 WSL 服务层错误 `Wsl/Service/0x8007274c` 或 `Wsl/Service/E_UNEXPECTED`，重试固定 WSL 前缀后可继续。

最高级母进程复验更新：

1. 已执行 `cp .env.example .env` 创建本地运行配置；`.env` 不提交 Git。
2. 已修复 `start_demo.sh` 的 nvm Node/npm 探测逻辑，非交互 WSL shell 中也能使用 `/home/hp/.nvm/versions/node/v24.15.0/bin` 下的 Linux Node/npm。
3. 已更新 `docs/start_demo.md` 与 `docs/wsl_setup.md`，说明 `command -v node/npm` 是判定依据；`type -a npm` 后续出现 `/mnt/*` 仅表示 PATH fallback。
4. 已复测 `timeout 12s ./start_demo.sh`：后端 `/api/health` 通过，前端启动并输出访问地址；timeout 结束导致退出码非 0 属于预期终止。
5. 已复测 `bash scripts/run_acceptance.sh`：退出码 0，所有脚本化验收通过。
6. 针对 Ctrl+C 后浏览器仍显示旧 CAPD 页面的问题，已从 WSL 与 Windows 两侧检查当前 `127.0.0.1:8000`：未发现本项目服务残留监听，Windows `curl` 也无法连接；判断更可能是旧页面/缓存或其他历史服务造成的混淆。已加固 `start_demo.sh`，退出时递归终止前后端子进程树，并在 `docs/start_demo.md` 增加端口排查说明。

后续复验步骤：

1. 按 `docs/acceptance_tests.md` 完成 1024x600 触摸屏人工验收。
2. 人工验收通过后，由 Overall Master 更新总状态并提交部署阶段改动。
