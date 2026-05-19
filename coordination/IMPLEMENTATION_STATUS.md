# 总实现状态

母进程维护本文件。子进程不要直接修改，除非母进程明确授权。

## 当前阶段

阶段 1：00 Foundation 已完成，准备启动 01 Data mock 病例包与数据校验。

## 模块状态

| 模块 | 状态 | 负责人进程 | 备注 |
| :--- | :--- | :--- | :--- |
| 00 Foundation | 已完成 | 模块 00 Foundation 母进程 | 工程骨架、`.env.example`、基础 README 已通过母进程检查 |
| 01 Data | 待启动 | 待分配 | mock 病例包和校验；下一步优先执行 |
| 02 Backend | 未开始 | 待分配 | FastAPI、DTI/V1/RI |
| 03 Frontend | 未开始 | 待分配 | React 页面和联调 |
| 04 Deploy | 未开始 | 待分配 | WSL、一键启动、验收 |

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

## 阻塞问题

暂无。

## 下一步

启动 01 Data：生成可计算 mock 病例包与校验脚本。01 Data 完成后再启动后端核心 API 与计算模块。
