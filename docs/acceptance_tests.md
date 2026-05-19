# 最终验收测试说明

本文档用于 04 Deploy / Worker C 的最终验收。所有命令必须在 WSL Ubuntu 项目根目录 `/home/hp/ad-edge-demo` 内执行；从 Windows 侧调用时统一使用：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "<command>"
```

不要使用 Windows 版 Node、npm、Python、pip、Vite 或 uvicorn 操作本项目依赖。

## 1. 一键脚本

自动化验收脚本：

```bash
bash scripts/run_acceptance.sh
```

从 Windows PowerShell 执行：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "bash scripts/run_acceptance.sh"
```

脚本默认使用 `case_HC_001`，可通过环境变量切换病例：

```bash
ACCEPTANCE_CASE_ID=case_AD_001 bash scripts/run_acceptance.sh
```

脚本会对会破坏病例包的检查做备份和恢复，包括：

- 临时移动 `compute/sr_dwi_4d.nii.gz` 后再恢复。
- 临时移动 `output/report.json` 后再恢复。
- 修改 mock dMRI 数据前备份原始 NIfTI，结束后恢复。
- 备份并恢复 `output/` 下已有结果。

## 2. 已脚本化验收项

`scripts/run_acceptance.sh` 覆盖以下项目：

- 基础启动：检查当前目录是 WSL 项目根；如存在可执行 `./start_demo.sh`，尝试启动并轮询 `GET /api/health`，要求返回 `status: ok`。
- 后端健康检查：使用 `.venv/bin/python -m uvicorn backend.main:app` 启动临时后端，调用 `GET /api/health`，要求 `status` 为 `ok` 且病例根目录存在。
- 前端连接状态：检查前端源码中存在 `BackendBadge`、后端离线状态和报告页无假报告提示。前端视觉效果仍需人工验收。
- 断网验收：检查本文档写明“已安装好依赖”后的断网启动方式，并扫描运行时代码中是否存在直接访问远端 API 的硬编码端点。
- 反虚跑验收：先运行 `POST /api/cases/{case_id}/run-ri-analysis` 生成后端结果，再检查报告 API 可读取真实 `report.json`。
- 停止后端：杀掉临时后端后，报告 API 必须不可访问。对应前端表现需人工确认：前端不能生成报告。
- 缺失 dMRI 输入：临时移走 `data/cases/{case_id}/compute/sr_dwi_4d.nii.gz` 后，RI 分析必须返回非 200。
- 缺失报告：临时移走 `data/cases/{case_id}/output/report.json` 后，报告 API 必须返回 `not_completed`，且响应中不包含硬编码结论、报告标题、风险分布或 `key_findings`。
- mock dMRI 变化：修改备份后的 `sr_dwi_4d.nii.gz`，重新运行 RI 分析，要求 `ri_depth_profiles.json` 的哈希与修改前不同。
- Git 状态：执行 `git status --short`，并确认 `.venv`、`node_modules`、`frontend/node_modules`、`dist`、`build`、`frontend/dist` 没有被 Git 跟踪。
- 文案边界：扫描前端、后端、README、docs 与病例包，不能出现“边缘端真实运行完整 DisC-Diff”“边缘端实时完成 FreeSurfer”“边缘端实时完成全脑配准”“确诊 AD”。

如果 `start_demo.sh` 暂未由 Worker B 写入，脚本会把一键启动项标为失败，但仍会使用 `.venv/bin/python -m uvicorn` 拉起后端继续完成 API 与反虚跑验收。

## 3. 断网验收步骤

断网验收的前提是依赖已经在 WSL 内安装完成：

```bash
test -x .venv/bin/python
test -d frontend/node_modules
test -d data/cases
```

断开外网后执行：

```bash
./start_demo.sh
```

如果只需要验证后端，可执行：

```bash
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

验收标准：

- 启动过程不执行 `pip install`、`npm install`、`git pull` 或下载模型/数据。
- 后端只读取本地 `data/cases/` 病例包。
- 运行过程中不需要访问远端 API。
- 局部超分页面只展示本地预存低分辨和超分预览图，不把边缘端写成真实运行完整 DisC-Diff。
- RI 分析由后端读取本地 NIfTI、bvec/bval、mask、采样点、法向量和参考范围后生成结果。

## 4. 1024x600 触摸屏人工验收

这部分不能完全依赖脚本。请在目标触摸屏或浏览器开发者工具中设置 1024x600 视口后检查：

1. 打开浏览器访问 `http://127.0.0.1:5173`；如果在板端或局域网设备访问，使用 `start_demo.sh` 输出的前端地址。
2. 浏览器缩放先设为 100%，再设为 90%。两种缩放下都检查顶栏、侧栏、病例表格、按钮、图表和报告区域。
3. 点击刷新连接、刷新病例、选择病例、局部超分展示、RI 分析、刷新报告、主题切换按钮，确认触摸点击可用且不会误触。
4. 检查纵向滚动能到达所有内容，横向滚动只应出现在表格或图表等固定宽度区域。
5. 检查后端停止时前端显示离线状态，病例选择以外入口锁定，报告页不能生成替代结论。
6. 检查 RI 深度曲线、ROI 指标图、图例和坐标轴在 1024x600 下可读。
7. 检查页面没有文字重叠、按钮文字溢出、图表遮挡操作区或报告内容超出不可滚动区域。

可选自动化方式：如果项目后续安装 Linux/WSL 内 Playwright，可在 WSL 内运行浏览器测试并设置 viewport 为 `{ width: 1024, height: 600 }`。不要使用 Windows 版 Node 或 Windows 浏览器依赖操作 WSL 项目。

## 5. 文案边界

验收时页面、报告和文档必须保持以下边界：

- 不写边缘端真实运行完整 DisC-Diff。
- 不写边缘端实时完成 FreeSurfer。
- 不写边缘端实时完成全脑配准。
- 报告不写确诊 AD。
- 报告只使用“辅助分析”“风险提示”“影像特征”“竞赛 Demo”等表述。

当前 Demo 的正确口径是：边缘端接收赛前准备好的标准化病例包，本地完成简化 DTI/V1/RI 后处理、指标生成、报告输出和可视化展示。

## 6. Git 状态检查

提交或回报前执行：

```bash
git status --short
git ls-files .venv node_modules frontend/node_modules dist build frontend/dist
```

验收标准：

- 能看到自己的文档和脚本改动。
- `.venv`、`node_modules`、`frontend/node_modules`、`dist`、`build`、`frontend/dist` 不应出现在 `git ls-files` 输出中。
- 不要提交依赖目录、构建产物或临时验收备份文件。
