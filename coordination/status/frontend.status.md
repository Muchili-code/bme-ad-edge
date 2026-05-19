# frontend status

## 当前任务

Worker A/B/C 已完成前端骨架、输入概览、局部超分流程、RI 分析、报告页与 ECharts 接入。模块母进程已完成源码审查、后端测试、API 抽样和前端生产构建复验。

## 已完成

- Worker A 完成 React + Vite + TypeScript 骨架、基础布局、主题切换、后端连接状态、病例选择页和共享 API client。
- Worker B 完成输入概览页与局部超分流程演示页：病例详情来自 `GET /api/cases/{case_id}`，预览图使用后端返回路径，局部超分展示实际调用 `POST /api/cases/{case_id}/simulate-super-resolution`。
- Worker C 完成 RI 分析页、报告页和 ECharts 图表：点击 RI 分析实际调用 `POST /api/cases/{case_id}/run-ri-analysis`，完成后读取 `ri-profiles`、`metrics`、`report`。
- 前端文案保持 Demo 边界：只表达局部超分流程展示、预存超分结果对比、边缘端本地 DTI/V1/RI 后处理；未声称边缘端真实运行完整 DisC-Diff、FreeSurfer、全脑配准或科研级预处理。
- 报告页读取后端 report API；`report.json` 缺失或未完成时显示“报告尚未生成”，不生成假报告。
- 后端离线、未选择病例、病例详情未同步或病例包无效时，后续流程入口禁用或展示锁定状态，不进入假演示流程。
- 模块母进程已补充 `detail plan.md` 的 WSL 直接运行命令说明：进入 WSL 不等于自动激活 `.venv`，后端测试应使用 `.venv/bin/python`。
- 模块母进程已在 Linux Node 环境下生成 `frontend/package-lock.json` 并完成前端依赖安装与生产构建复验。

## 修改文件

- `detail plan.md`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/tsconfig.json`
- `frontend/tsconfig.app.json`
- `frontend/tsconfig.node.json`
- `frontend/vite.config.ts`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/src/types.ts`
- `frontend/src/api/client.ts`
- `frontend/src/hooks/useBackendStatus.ts`
- `frontend/src/hooks/useCases.ts`
- `frontend/src/hooks/useCaseDetail.ts`
- `coordination/status/frontend.status.md`

## 自测结果

- `.venv/bin/python -m pytest backend/tests -q`：14 passed。
- FastAPI TestClient 抽样通过：`GET /api/health`、`GET /api/cases`、`POST /api/cases/case_HC_001/run-ri-analysis`、`GET /ri-profiles`、`GET /metrics`、`GET /report`；报告 API 返回 `status: completed`。
- 使用 Linux Node `/home/hp/.nvm/versions/node/v24.15.0/bin` 执行 `npm install` 成功，生成 `frontend/package-lock.json`。
- 使用同一 Linux Node 环境执行 `npm run build` 成功；仅有 Vite chunk size warning。
- 源码搜索确认 `frontend/src` 中没有禁用文案“确诊 AD”“临床诊断结论”，没有硬编码 `key_findings`、病例结果、RI 曲线数组或 ROI 指标数值。
- UTF-8 本体检查确认 `detail plan.md` 和 `coordination/status/frontend.status.md` 无 replacement character，无连续问号。

## 阻塞问题

暂无业务阻塞。

备注：Codex App 调用 WSL 时仍偶发 `setup refresh failed` 或 WSL 服务层中断；重试后可继续，不属于前端实现问题。

## 需要母进程检查

建议 Overall Master 后续进入 04 Deploy 阶段，补充一键启动脚本和最终 1024x600 浏览器实机验收。
