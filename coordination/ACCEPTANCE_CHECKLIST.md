# 验收清单

## 1. 基础运行

- [ ] WSL Ubuntu 中可安装依赖。
- [ ] WSL Ubuntu 中可运行 `./start_demo.sh`。
- [ ] 后端 `GET /api/health` 返回 `ok`。
- [ ] 前端能显示后端连接状态。

## 2. mock 病例包

- [ ] `generate_mock_cases.py` 能生成 HC / MCI / AD 三个病例。
- [ ] `validate_case_package.py` 能校验三个病例通过。
- [ ] 每个病例包含 `compute/sr_dwi_4d.nii.gz`、`grad.bvec`、`grad.bval`。
- [ ] 每个 ROI 有 11 个深度采样点。

## 3. 后端计算

- [ ] `POST /api/cases/{case_id}/run-ri-analysis` 会真实读取 NIfTI 和 bvec/bval。
- [ ] 后端生成 `ri_depth_profiles.json`。
- [ ] 后端生成 `roi_ri_metrics.csv`。
- [ ] 后端生成 `abnormal_regions.json`。
- [ ] 后端生成 `sampled_vectors.json`。
- [ ] 后端生成 `report.json`。

## 4. 前端流程

- [ ] 病例选择页显示病例包状态。
- [ ] 输入概览页展示 dMRI、T1、预存超分图。
- [ ] 局部超分页明确标注为流程展示。
- [ ] RI 分析页必须等待后端计算完成后显示曲线。
- [ ] 报告页读取后端 `report.json`。

## 5. 反虚跑

- [ ] 停止后端后，前端不能生成报告。
- [ ] 删除 `sr_dwi_4d.nii.gz` 后，RI 分析必须失败。
- [ ] 删除 `output/report.json` 后，报告页不能显示硬编码结论。
- [ ] 修改 mock dMRI 数据后，重新计算的 RI 输出应发生变化。

## 6. 文案边界

- [ ] 页面不写“边缘端真实运行完整 DisC-Diff”。
- [ ] 页面不写“边缘端实时完成 FreeSurfer”。
- [ ] 页面不写“边缘端实时完成全脑配准”。
- [ ] 报告不写“确诊 AD”。
- [ ] 报告只使用“辅助分析”“风险提示”“影像特征”等表述。

## 7. WSL 环境

- [ ] `which node`、`which npm`、`which python3`、`which pip` 均指向 WSL 内路径。
- [ ] `.venv/` 和 `node_modules/` 由 WSL 内工具生成。
- [ ] 没有用 Windows 版 Node/Python 操作 WSL 项目依赖。
