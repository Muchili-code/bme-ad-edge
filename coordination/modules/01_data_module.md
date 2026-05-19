# 模块 01：mock 病例包与数据校验

## 目标

在没有真实科研数据时，生成可被后端真实计算的小型病例包，并提供校验脚本。

## 写入范围

- `scripts/generate_mock_cases.py`
- `scripts/validate_case_package.py`
- `data/cases/`
- 数据相关测试文件

## 依赖契约

- `coordination/CASE_PACKAGE_SPEC.md`
- `coordination/OUTPUT_FILE_SPEC.md`

## 任务

1. 生成 HC / MCI / AD 三个 mock 病例。
2. 每个病例包含预览 PNG、4D NIfTI、bvec/bval、mask、法向量、深度采样点、ROI 映射、参考文件。
3. mock 4D dMRI 要支持后端真实 DTI/V1/RI 计算。
4. 校验脚本检查文件存在性、字段、volume 数量、ROI 深度点数量。
5. 更新 `coordination/status/data.status.md`。

## 验收

- 三个病例生成成功。
- 校验脚本通过。
- 修改 mock 数据后，后端未来重新计算结果应能变化。
