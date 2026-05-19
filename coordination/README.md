# 分层串并结合协作入口

本目录用于组织 AD dMRI 边缘端 Demo 的多进程协作开发。协作方式采用三层结构：

```text
母进程 Master
  -> 模块负责人 Module Lead
    -> 任务执行进程 Task Worker
```

## 使用顺序

1. 第一个 Codex 进程作为母进程，先严格按照 `AGENT.md` 了解项目，并按其中要求实际阅读/提取阅读/查看项目指定文件。
2. 完成项目理解后，阅读：
   - `AGENT.md`
   - `detail plan.md`
   - `coordination/MASTER_CONTROL.md`
   - `coordination/PROCESS_RULES.md`
   - `coordination/IMPLEMENTATION_STATUS.md`
3. 母进程确认共享契约：
   - `API_CONTRACT.md`
   - `CASE_PACKAGE_SPEC.md`
   - `OUTPUT_FILE_SPEC.md`
   - `ACCEPTANCE_CHECKLIST.md`
4. 母进程按模块任务书创建或指挥子进程：
   - `modules/00_foundation_module.md`
   - `modules/01_data_module.md`
   - `modules/02_backend_module.md`
   - `modules/03_frontend_module.md`
   - `modules/04_deploy_module.md`
5. 每个子进程只按自己的任务文件工作，并更新对应 `status/*.status.md`。
6. 共享契约文件默认只由母进程修改。子进程如需修改契约，只在状态文件中提出建议。

## 核心原则

- 先契约，后实现。
- 先 mock 数据闭环，后真实数据替换。
- 先后端真实计算，后前端展示结果。
- 禁止程序虚跑：报告、曲线和指标必须来自后端输出文件。
- 依赖安装和项目运行固定在 WSL Ubuntu 内完成。
- 模块母进程以管理为主：拆分任务、下发 Task Worker 指令、汇总状态和验收产物；具体大块实现默认交给任务子进程完成。

## Codex App / WSL 注意事项

本工作区在 WSL Linux 文件系统内，Windows 侧路径为 `\\wsl.localhost\Ubuntu\home\hp\ad-edge-demo`，WSL 内路径为 `/home/hp/ad-edge-demo`。后续所有进程如果遇到 Codex App 默认 PowerShell、Node REPL 或沙箱命令报错：

```text
setup refresh failed with status exit code: 1
```

不要继续用 Windows 版 PowerShell、Node.js 或 Python 操作项目文件，也不要用 Windows 工具安装依赖。统一改用：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "<command>"
```

依赖安装、项目运行、测试、脚本执行、文件检查和代码生成都应固定在这个 WSL shell 内完成。中文 Markdown/JSON 的修改仍按 `PROCESS_RULES.md` 要求做 UTF-8 本体检查。
