# 总实现状态

母进程维护本文件。子进程不要直接修改，除非母进程明确授权。

## 当前阶段

阶段 4：03 Frontend 已完成，准备启动 04 Deploy WSL 部署、一键启动与验收测试。

## 模块状态

| 模块 | 状态 | 负责人进程 | 备注 |
| :--- | :--- | :--- | :--- |
| 00 Foundation | 已完成 | 模块 00 Foundation 母进程 | 工程骨架、`.env.example`、基础 README 已通过母进程检查 |
| 01 Data | 已完成 | 模块 01 Data 母进程 | mock 病例包、生成脚本、校验脚本已通过母进程检查 |
| 02 Backend | 已完成 | 模块 02 Backend 母进程 | FastAPI、真实 DTI/V1/RI、结果读取 API 与测试已通过 |
| 03 Frontend | 已完成 | 模块 03 Frontend 母进程 | React 页面、后端 API 对接、ECharts 展示与构建已通过 |
| 04 Deploy | 待启动 | 待分配 | WSL、一键启动、最终验收；下一步按三层协作启动模块母进程 |

## 最近决策

- 开发和运行固定在 WSL Ubuntu。
- 共享契约由母进程维护。
- 前端不能硬编码报告、曲线和指标。
- 第一版只做 RI、RI Skewness、RI Maximum。
- 阶段 0 已核对 `detail plan.md`、协作规则、API 契约、病例包契约、输出文件契约和验收清单，当前契约完整且与实施计划一致。
- 后续推进采用“分层串并结合”：先 00 Foundation，再 01 Data，随后 02 Backend 与 03 Frontend 在契约稳定后局部并行，最后 04 Deploy 和反虚跑验收。
- 板端边界保持不变：不实现也不声称真实运行完整 DisC-Diff、FreeSurfer、全脑配准或科研级预处理；后端必须真实读取 mock 4D dMRI 并执行简化 DTI/V1/RI。
- 已补充 Codex App / WSL 兼容性处理规则：遇到 `setup refresh failed with status exit code: 1` 时，后续进程统一使用 `wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "<command>"`，不再反复尝试 Windows 侧 PowerShell、Node.js 或 Python。
- 00 Foundation 检查通过：基础目录存在，`.env.example` 使用相对病例路径，README 明确 WSL 运行原则和 Demo 边界，未发现 `node_modules/`、`.venv/`、`dist/`、`build/`。
- 01 Data 检查通过：三组 mock 病例包均通过 `validate_case_package.py`，NIfTI 维度为 `(32, 32, 16, 13)`，bvec/bval 与 volume 数匹配，每例 6 个 ROI 且每个 ROI 有 11 个深度点。
- 已修正协作规则：模块母进程以管理、拆分、汇总和验收为主；大块实现默认下发给 Task Worker。
- GitHub 远端 `origin` 指向 `git@github.com:Muchili-code/bme-ad-edge.git`，远端 `main` 可访问；已补充 `.gitignore` 并将 Python `.pyc` 缓存从 Git 索引移除，便于版本更新与回退。
- 02 Backend 检查通过：`python -m pytest backend/tests -q` 为 14 passed，`python backend/tests/ri_smoke.py` 三病例均完成；后端真实读取 mock 4D dMRI 与 bvec/bval 执行简化 DTI/V1/RI，输出 API 从 `output/` 读取，缺文件测试覆盖反虚跑。
- 03 Frontend 检查通过：前端对接真实后端 API，病例、预览图、RI 曲线、metrics 和 report 均来自后端；`npm run build` 通过，仅有 Vite chunk size warning；未发现禁用诊断文案或前端硬编码报告/曲线/指标。

## 阻塞问题

暂无。

## 下一步

启动 04 Deploy 模块母进程。模块母进程先拆分并下发部署、启动脚本、断网和反虚跑验收 Task Worker 指令。
