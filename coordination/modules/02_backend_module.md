# 模块 02：FastAPI 后端与 DTI/V1/RI 计算

## 目标

实现边缘端后端服务，确保病例读取、局部超分演示接口、真实 DTI/V1/RI 计算和报告输出可用。

## 写入范围

- `backend/`
- 后端测试文件

## 依赖契约

- `coordination/API_CONTRACT.md`
- `coordination/CASE_PACKAGE_SPEC.md`
- `coordination/OUTPUT_FILE_SPEC.md`

## 任务

1. 实现 FastAPI 项目骨架。
2. 实现 `GET /api/health`。
3. 实现病例扫描和详情接口。
4. 实现预览图安全读取。
5. 实现局部超分流程演示接口。
6. 实现 `run-ri-analysis`：读取 NIfTI、bvec/bval、采样点和法向量，简化 DTI 拟合，提取 V1，计算 RI。
7. 生成所有 output 文件。
8. 实现报告、曲线、指标读取接口。
9. 更新 `coordination/status/backend.status.md`。

## 验收

- API 符合 `API_CONTRACT.md`。
- 删除计算输入时分析失败并给出明确错误。
- 输出文件符合 `OUTPUT_FILE_SPEC.md`。
