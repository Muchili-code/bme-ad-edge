# 第一个 Codex 进程启动指令

请把下面整段复制给新开的第一个 Codex 进程。该进程作为母进程运行。

```text
请你作为本项目的“母进程 Master”启动多进程协作开发。

第一步必须严格按照当前工作目录的 AGENT.md 了解项目：先阅读 AGENT.md，并按其中要求实际阅读/提取阅读/查看项目指定文件，包括论文、工作流图片、教学 PDF、展示方案、Question、香橙派 AIPro 说明等。阅读完成后，先在回复中列出你实际阅读过的文件清单，并标明每个文件是“全文阅读 / 提取正文阅读 / 实际查看图片”。如果需要读取中文 Markdown/JSON，请遵守 AGENT.md 中关于 UTF-8、Node.js fs/promises 和文件本体检查的要求。

完成 AGENT.md 要求的项目理解后，再阅读以下协作文件：

1. detail plan.md
2. coordination/README.md
3. coordination/MASTER_CONTROL.md
4. coordination/PROCESS_RULES.md
5. coordination/IMPLEMENTATION_STATUS.md
6. coordination/API_CONTRACT.md
7. coordination/CASE_PACKAGE_SPEC.md
8. coordination/OUTPUT_FILE_SPEC.md
9. coordination/ACCEPTANCE_CHECKLIST.md

你的职责不是立刻写完整工程代码，而是在充分理解项目后执行阶段 0：检查协作文件和共享契约是否完整、是否和 detail plan.md 一致，然后更新 coordination/IMPLEMENTATION_STATUS.md。确认无问题后，按照“分层串并结合”的方式推进：先工程骨架，再 mock 数据，再后端，再前端，最后部署和反虚跑验收。

请注意：
- 项目实现阶段应迁移到 WSL Ubuntu 的 Linux 文件系统中。
- 依赖安装和项目运行必须固定在 WSL 内完成。
- 从 Windows 侧执行命令时使用 wsl -d Ubuntu --cd /home/<user>/ad-edge-demo -- bash -lc "<command>"。
- 本工作区实际 WSL 路径是 /home/hp/ad-edge-demo；如果 Codex App 默认 PowerShell、Node REPL 或沙箱命令出现 setup refresh failed with status exit code: 1，不要反复尝试 Windows 侧命令，立即切换到 wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "<command>"。
- 不允许 Windows 版 Node/Python 直接操作 WSL 项目的 node_modules 或 .venv。
- 共享契约文件默认只由母进程维护。
- 子进程只修改自己的写入范围，并通过 coordination/status/*.status.md 汇报。
- 前端不能硬编码报告、曲线或指标。
- 后端必须真实读取 mock 4D dMRI 并执行简化 DTI/V1/RI 计算。
- 不实现也不声称边缘端真实运行完整 DisC-Diff、FreeSurfer、全脑配准或科研级预处理。

现在请先完成阶段 0 检查，并给出下一步要启动的模块/任务顺序。
```
