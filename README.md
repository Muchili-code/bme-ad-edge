# AD dMRI 边缘端 Demo

本项目是 AD dMRI 边缘端 Demo，用于在低成本边缘设备展示从标准化病例包读取数据、执行板端后处理、生成 RI 指标与报告的闭环流程。

## 开发环境原则

开发、依赖安装、运行和测试固定在 WSL Ubuntu 内完成。本项目当前 WSL 路径为：

```text
/home/hp/ad-edge-demo
```

从 Windows 侧运行命令时统一使用：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "<command>"
```

不要使用 Windows 版 Node.js、Python、npm、pip、Vite 或 uvicorn 直接操作本项目的依赖目录。后续生成的 `.venv/`、`node_modules/`、`dist/`、`build/` 等目录应只由 WSL 内工具创建和维护。

## 当前 Demo 边界

边缘端 Demo 不在板端真实运行完整 DisC-Diff、FreeSurfer、全脑配准或科研级预处理。这些流程属于赛前 PC/科研端准备范围。

当前边缘端只接收 `data/cases/` 下的标准化病例包，并围绕病例选择、流程展示、简化 DTI/V1/RI 计算、指标生成、报告输出和可视化展示完成工程闭环。

## 基础目录

```text
frontend/
backend/
scripts/
data/cases/
docs/
```
