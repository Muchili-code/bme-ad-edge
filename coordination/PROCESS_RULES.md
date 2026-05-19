# 多进程协作规则

## 1. 通用规则

1. 所有进程先阅读 `AGENT.md`、`detail plan.md` 和自己的任务文件。
2. 所有中文文件按 UTF-8 读写。
3. 修改中文 Markdown/JSON 时优先使用 Node.js `fs/promises`，显式指定 `utf8`。
4. 修改后必须检查文件本体内容，确认没有 replacement character 和连续问号。
5. 不允许子进程直接修改不属于自己写入范围的文件。
6. 不允许跳过后端真实计算直接在前端硬编码结果。
7. 不允许实现或声称边缘端真实运行完整 DisC-Diff、FreeSurfer、全脑配准或科研级预处理。

## 2. 状态回写规则

每个任务完成或遇到阻塞时，更新对应状态文件，格式如下：

```text
## 当前任务

## 已完成

## 修改文件

## 自测结果

## 阻塞问题

## 需要母进程检查
```

状态文件只写事实，不写长篇推测。

## 3. WSL 执行规则

项目实际实现阶段放在 WSL Ubuntu Linux 文件系统中，例如：

```text
/home/<user>/ad-edge-demo
```

依赖安装和项目运行必须在 WSL 内完成。从 Windows 侧下发命令时使用：

```powershell
wsl -d Ubuntu --cd /home/<user>/ad-edge-demo -- bash -lc "<command>"
```

禁止在 Windows PowerShell 中直接对 WSL 项目运行 Windows 版 `npm install`、`pip install`、`python`、`uvicorn` 或 `vite`。

### 3.1 Codex App 与 WSL 兼容性处理

本项目当前目录位于 `\\wsl.localhost\Ubuntu\home\hp\ad-edge-demo`。Codex App 在 Windows 侧启动默认 PowerShell 命令、Node REPL 或沙箱内命令时，可能出现：

```text
setup refresh failed with status exit code: 1
```

遇到该错误时，不要反复尝试 Windows PowerShell、Windows Node.js、Windows Python 或 Codex Node REPL 来读写 WSL 项目文件。正确处理方式：

1. 立即切换为 WSL 命令执行路径。
2. 从 Windows 侧统一使用以下前缀：

```powershell
wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "<command>"
```

3. 所有依赖安装、项目运行、测试、脚本执行、代码生成和文件检查都必须在该 WSL shell 内完成。
4. 如果命令因 Codex 沙箱兼容性失败，需要请求允许执行上述固定 WSL 前缀；获得允许后，后续同类命令都使用该前缀。
5. 中文 Markdown/JSON 文件的读写仍需显式 UTF-8。若需要脚本修改中文文件，应在 WSL 内使用 Node.js `fs/promises` 或 Python 读取外部脚本文件，修改后检查文件本体是否包含 replacement character 或连续问号。
6. 子进程状态文件中如遇到该兼容性问题，只记录实际错误和已切换到 WSL 前缀，不把它当作业务阻塞。

## 4. 反虚跑规则

任何模块都必须支持最终通过这些检查：

1. 停止后端后，前端不能生成报告。
2. 删除 `sr_dwi_4d.nii.gz` 后，RI 分析必须失败。
3. 删除 `output/report.json` 后，报告页不能显示硬编码结论。
4. 修改 mock dMRI 数据后，重新计算的 RI 输出应发生变化。
