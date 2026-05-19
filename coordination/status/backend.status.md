# backend status

## 当前任务

Worker A 已完成 FastAPI API 骨架与病例包基础读取。Worker B 已接入真实 RI 分析服务代码，等待安装后端 Python 依赖后复跑完整计算自测。

## 已完成

- 已阅读 `AGENT.md`、`detail plan.md`、`coordination/PROCESS_RULES.md`、`coordination/API_CONTRACT.md`、`coordination/CASE_PACKAGE_SPEC.md`、`coordination/modules/02_backend_module.md`、`coordination/tasks/backend_01_api_skeleton.md`。
- 已建立 FastAPI 项目骨架。
- 已实现 `GET /api/health`。
- 已实现 `GET /api/cases`，扫描 `data/cases/`，读取 `meta.json`，返回 `package_valid` 和 `ri_analysis_done`。
- 已实现 `GET /api/cases/{case_id}`，返回病例详情、文件完整性、预览图 URL 和 output 状态。
- 已实现 `GET /api/cases/{case_id}/preview/{image_name}`，仅允许 `preview/` 下 PNG/JPEG，并拦截路径穿越。
- 已实现 `POST /api/cases/{case_id}/simulate-super-resolution`，仅返回 `visual_demo_only` 演示流程和预存 `sr_dwi_patch.png` 路径。
- 已为 Worker B 预留 `POST /api/cases/{case_id}/run-ri-analysis` 边界，Worker B 已替换 501 占位并接入真实 RI 分析服务，不生成假结果。
- Worker B 已实现 `backend/services/ri_analysis.py`：读取 dMRI、bvec/bval、mask、depth samples、surface normals、ROI map 和参考范围；执行简化 DTI 拟合、V1 提取、11 深度点 RI 计算；生成五个 output 契约文件。
- Worker B 生成的 `report.json` 来自本次 metrics 和参考范围，不硬编码病例最终结论。

## 修改文件

- `backend/__init__.py`
- `backend/main.py`
- `backend/services/__init__.py`
- `backend/services/cases.py`
- `backend/services/ri_analysis.py`
- `backend/tests/test_api_skeleton.py`
- `backend/tests/test_ri_analysis.py`
- `backend/tests/ri_smoke.py`
- `backend/tests/ri_missing_input_check.py`
- `backend/requirements.txt`
- `coordination/status/backend.status.md`

## 自测结果

- `wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 -m compileall backend"`：通过。
- `wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 -m pytest backend/tests -q"`：未通过，原因是当前 Ubuntu Python 环境缺少 `pytest`。
- FastAPI TestClient 烟测未运行成功，原因是当前 Ubuntu Python 环境缺少 `fastapi`。
- 已新增 `backend/requirements.txt`，包含 `fastapi`、`uvicorn`、`pytest`。
- Worker B 已更新 `backend/requirements.txt`，补充 `numpy`、`pandas`、`scipy`、`nibabel`。
- Worker B 修改后 `wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 -m compileall backend"`：通过。
- `wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 backend/tests/ri_missing_input_check.py && test -f data/cases/case_HC_001/compute/sr_dwi_4d.nii.gz && echo restored"`：通过。临时移走 `sr_dwi_4d.nii.gz` 后返回明确缺文件错误，随后已恢复原文件。
- `wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 backend/tests/ri_smoke.py"`：未通过，原因是当前 Ubuntu Python 环境缺少 `nibabel`；完整三病例计算和“修改 mock dMRI 后结果变化”需安装依赖后复跑。
- 已检查新增后端文件，未发现 replacement character 或连续问号。

## 阻塞问题

- 当前 WSL Python 环境缺少 `fastapi`、`pytest`、`nibabel` 等后端依赖，且 `python3 -m pip` 与 `python3 -m ensurepip` 均不可用；需要先准备 pip/venv 并安装 `backend/requirements.txt` 后再运行接口测试和完整 RI 计算测试。
- 目录探查时曾出现 WSL 服务层 `Wsl/Service/E_UNEXPECTED`，随后使用固定 WSL 前缀继续执行；不作为业务阻塞。

## 需要母进程检查

- 检查 Worker A 返回结构是否满足前端读取预期。
- 安装后端依赖后重新运行 `python3 -m pytest backend/tests -q`。
- 安装后端依赖后重新运行 `python3 backend/tests/ri_smoke.py`，确认 HC/MCI/AD 三病例生成五个 output 文件。
- 安装后端依赖后重新运行 `backend/tests/test_ri_analysis.py`，确认修改 mock dMRI 后输出变化。
- 母进程检查 `POST /api/cases/{case_id}/run-ri-analysis` 的 422 错误映射是否符合 Worker C 的统一 API 错误处理方案。

## Worker C 更新（报告/曲线/指标读取 API）

## 当前任务

- Worker C 已完成 `ri-profiles`、`metrics`、`report` 读取接口实现与后端测试补充；当前环境缺依赖，完整 pytest/API 运行仍需安装 `backend/requirements.txt`。

## 已完成

- 已实现 `GET /api/cases/{case_id}/ri-profiles`，读取 `output/ri_depth_profiles.json`；文件不存在时返回 `status=not_completed` 和明确未完成信息，不返回假曲线。
- 已实现 `GET /api/cases/{case_id}/metrics`，读取 `output/roi_ri_metrics.csv` 并按固定列转换 JSON；文件不存在时返回 `status=not_completed` 和空 metrics。
- 已实现 `GET /api/cases/{case_id}/report`，读取 `output/report.json`；文件不存在时返回 `status=not_completed` 与“报告尚未生成。”，不返回硬编码结论。
- 已检查错误响应路径：病例不存在返回 404，非法 case_id/输出 JSON 或 CSV 结构错误返回明确错误；`run-ri-analysis` 缺输入仍映射为 422。
- 已更新 API 测试覆盖 health、cases list、case detail、preview path traversal、防非图片预览、simulate-super-resolution visual_demo_only、run-ri-analysis 生成 output、缺失 `sr_dwi_4d.nii.gz` 失败、删除 `report.json` 后 report 不返回硬编码结论、metrics/ri-profiles 从 output 文件读取与缺文件状态。

## 修改文件

- `backend/main.py`
- `backend/services/results.py`
- `backend/tests/test_api_skeleton.py`
- `coordination/status/backend.status.md`

## 自测结果

- `wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 -m compileall backend"`：通过。
- `wsl -d Ubuntu --cd /home/hp/ad-edge-demo -- bash -lc "python3 -m pytest backend/tests -q"`：未运行通过，当前系统 Python 缺少 `pytest`。
- FastAPI TestClient 烟测：未运行通过，当前系统 Python 缺少 `fastapi`。
- `run_ri_analysis("case_HC_001")` 服务级检查：未运行通过，当前系统 Python 缺少 `nibabel`。
- 结果读取服务级缺文件检查已通过：`ri-profiles`、`metrics`、`report` 在 output 文件缺失时均返回 `status=not_completed`，且 report 不包含 `key_findings` 等硬编码结论字段。
- 已检查 `backend/main.py`、`backend/services/results.py`、`backend/tests/test_api_skeleton.py`，未发现 replacement character 或连续问号。

## 阻塞问题

- 当前 WSL Python 环境没有安装 `backend/requirements.txt` 中的依赖，缺少 `pytest`、`fastapi`、`nibabel`，因此完整后端 pytest、自测 API 和真实 RI output 生成需要依赖安装后复跑。

## 需要母进程检查

- 安装依赖后复跑 `python3 -m pytest backend/tests -q`，确认新增 API 测试和 Worker B RI 计算测试整体通过。
- 安装依赖后复跑用户给定 TestClient 三接口检查，确认 `run-ri-analysis` 生成 output 后 `ri-profiles`、`metrics`、`report` 均返回 200 且读取真实 output。
- 检查前端是否按 `status=not_completed` 处理报告/曲线/指标未生成状态，避免前端硬编码兜底结论。

## 模块母进程检查更新

## 当前任务

Worker A/B/C 产物已完成代码层检查；当前剩余阻塞为 WSL Python 环境缺 pip/venv 依赖安装能力，导致完整 pytest 与真实 RI 计算验收尚不能在本机跑通。

## 已完成

- 已检查 `backend/main.py`、`backend/services/cases.py`、`backend/services/results.py`、`backend/services/ri_analysis.py` 和主要测试文件。
- 已确认 API 路由覆盖 `API_CONTRACT.md` 中的 health、cases、case detail、preview、simulate-super-resolution、run-ri-analysis、ri-profiles、metrics、report。
- 已确认 RI 分析实现真实读取 `compute/sr_dwi_4d.nii.gz`、`grad.bvec`、`grad.bval`、mask、depth samples、surface normals、ROI map 和 reference ranges，并执行简化 DTI/V1/RI 后写入五个 output 文件。
- 已确认报告、曲线和指标读取接口从 `output/` 读取；缺失 output 时返回 `status=not_completed`，不返回硬编码结论。
- 已做模块母进程小修：`cases.py`、`results.py`、`ri_analysis.py` 的 `CASE_ROOT` 解析统一为项目根目录基准，并保留环境变量覆盖，避免从非项目根目录启动时读错病例包。

## 修改文件

- `backend/services/cases.py`
- `backend/services/results.py`
- `backend/services/ri_analysis.py`
- `coordination/status/backend.status.md`

## 自测结果

- `python3 -m compileall backend`：通过。
- 后端 Python/状态文件 UTF-8 本体检查：通过，未发现 replacement character 或连续问号。
- 当前系统 Python 依赖检查：`fastapi`、`pytest`、`nibabel`、`numpy`、`pandas`、`scipy` 均未安装。
- `python3 -m pip --version`：失败，系统 Python 无 pip。
- `python3 -m venv .venv`：失败，Ubuntu 缺 `ensurepip`，提示需要安装 `python3.12-venv`。
- 尝试 `sudo apt-get update && sudo apt-get install -y python3.12-venv python3-pip` 时非交互会话卡住，已终止相关进程；需要用户在交互式 WSL 中输入 sudo 密码或由最高级母进程安排环境安装。

## 阻塞问题

- 需要先在 WSL Ubuntu 中安装 `python3.12-venv` 和 `python3-pip`，再创建 `.venv` 并安装 `backend/requirements.txt`。
- 因依赖未安装，本轮无法完成 `pytest`、FastAPI TestClient、三病例 RI 真实计算和修改 mock dMRI 后输出变化验收。

## 需要母进程检查

- 环境依赖安装后，复跑：
  - `source .venv/bin/activate && python -m pytest backend/tests -q`
  - `source .venv/bin/activate && python backend/tests/ri_smoke.py`
  - 用户指定的 FastAPI TestClient 烟测。

## 模块母进程环境复测更新

## 当前任务

用户已在 WSL 中重建 `.venv` 并安装主要后端依赖；RI 烟测已跑通，pytest 收集阶段发现缺少 TestClient 依赖 `httpx`。

## 已完成

- `python backend/tests/ri_smoke.py` 已成功完成 HC/MCI/AD 三病例 RI 分析，并生成五个 output 文件。
- 已分析 pytest 报错：`starlette.testclient` 需要 `httpx`，但原 `backend/requirements.txt` 未包含。
- 已将 `httpx` 补充进 `backend/requirements.txt`。

## 修改文件

- `backend/requirements.txt`
- `coordination/status/backend.status.md`

## 自测结果

- 用户侧 `python backend/tests/ri_smoke.py`：通过，三病例均返回 `status=completed`。
- 用户侧 `python -m pytest backend/tests -q`：未通过，原因是缺少 `httpx`；已补 requirements，等待安装后复跑。

## 阻塞问题

- 当前 `.venv` 需要执行 `python -m pip install -r backend/requirements.txt` 以安装新增 `httpx`。

## 需要母进程检查

- 安装 `httpx` 后复跑 `python -m pytest backend/tests -q`。

## 模块母进程 API 测试修复更新

## 当前任务

用户安装 `httpx` 后 pytest 已运行到 14 个测试，剩余 1 个失败为 preview 路由对编码斜杠的匹配行为。

## 已完成

- 已分析失败原因：`/preview/..%2Fmeta.json` 在进入处理函数前被路由层解码为含斜杠路径，原 `{image_name}` 参数无法匹配，导致 Starlette 返回 404，而测试期望进入安全检查后返回 400。
- 已将 preview 路由从 `{image_name}` 改为 `{image_name:path}`，让路径穿越请求进入 `preview_image_path()`，由服务层统一返回 400。

## 修改文件

- `backend/main.py`
- `coordination/status/backend.status.md`

## 自测结果

- 用户侧 `python -m pytest backend/tests -q`：13 passed，1 failed；失败点已修复，等待复跑。

## 阻塞问题

- 暂无业务阻塞。

## 需要母进程检查

- 复跑 `python -m pytest backend/tests -q`，确认全部通过。

## 模块母进程最终验收更新

## 当前任务

02 Backend 模块已完成 Worker A/B/C 代码实现、依赖补齐、RI 烟测和后端 pytest 验收。

## 已完成

- 用户已确认 `python -m pytest backend/tests -q` 测试通过。
- `python backend/tests/ri_smoke.py` 已确认 HC/MCI/AD 三病例均完成 RI 分析并生成 output 文件。
- 已修复 TestClient 缺少 `httpx` 的依赖问题。
- 已修复 preview 路由对编码斜杠路径穿越测试返回 404 的问题，现在由服务层安全检查处理。
- 后端 API、病例读取、预览图读取、局部超分演示、真实 RI 分析、报告/曲线/指标读取、缺文件错误处理和反虚跑测试均已覆盖。

## 修改文件

- `backend/`
- `backend/requirements.txt`
- `coordination/status/backend.status.md`

## 自测结果

- `python backend/tests/ri_smoke.py`：通过。
- `python -m pytest backend/tests -q`：通过。

## 阻塞问题

暂无。

## 需要母进程检查

- 建议最高级母进程确认 02 Backend 模块验收通过。
- 下一步可启动 03 Frontend 模块，按 `coordination/API_CONTRACT.md` 对接后端真实 API。
