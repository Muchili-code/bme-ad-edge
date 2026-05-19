# Data 模块状态

## 当前任务

01 Data：mock 病例包生成与病例包校验。

## 已完成

- 已实现 `scripts/generate_mock_cases.py`。
- 已生成 HC / MCI / AD 三个 mock 病例包：
  - `data/cases/case_HC_001`
  - `data/cases/case_MCI_001`
  - `data/cases/case_AD_001`
- 每个病例包含 preview PNG、4D NIfTI、analysis mask、bvec/bval、surface normals、depth samples、ROI map、registration、参考 CSV/JSON 和可写 `output/` 目录。
- mock dMRI 为空间尺寸 `32 x 32 x 16`、13 个 volume（1 个 b0 + 12 个 diffusion volumes），可作为后端简化 DTI/V1/RI 计算输入。
- 已实现 `scripts/validate_case_package.py`，检查必需文件、meta 字段、NIfTI volume 数、bvec/bval 数量、ROI 深度点、核心 JSON 字段和 `output/` 可写性。

## 修改文件

- `scripts/generate_mock_cases.py`
- `scripts/validate_case_package.py`
- `data/cases/case_HC_001/`
- `data/cases/case_MCI_001/`
- `data/cases/case_AD_001/`
- `coordination/status/data.status.md`

## 自测结果

- `python3 scripts/generate_mock_cases.py`：通过，生成三个病例包。
- `python3 scripts/validate_case_package.py`：通过，三个病例均返回 OK。
- `python3 -m py_compile scripts/generate_mock_cases.py scripts/validate_case_package.py`：通过。
- 额外检查：三个病例 `sr_dwi_4d.nii.gz` 维度均为 `(32, 32, 16, 13)`；`grad.bval` 数量均为 13；每例 6 个 ROI，每个 ROI 均为 11 个深度点。
- UTF-8 本体检查：已检查本模块修改的 `.py`、`.json`、`.md`、`.csv` 文件，无 replacement character 和连续问号。

## 阻塞问题

暂无。

## 需要母进程检查

请母进程检查 mock 病例包结构、校验脚本覆盖范围，以及 mock dMRI 是否满足后端后续简化 DTI/V1/RI 计算接入需求。
