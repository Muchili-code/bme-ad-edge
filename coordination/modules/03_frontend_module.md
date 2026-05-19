# 模块 03：React 前端与展示流程

## 目标

实现 5 个边缘端页面，所有报告、曲线和指标均来自后端接口，不硬编码最终结果。

## 写入范围

- `frontend/`
- 前端测试文件

## 依赖契约

- `coordination/API_CONTRACT.md`
- `coordination/OUTPUT_FILE_SPEC.md`

## 页面

1. 病例选择页。
2. 输入概览页。
3. 局部超分流程演示页。
4. RI 分析页。
5. 报告页。

## 任务

1. 建立 React + Vite + TypeScript 项目。
2. 实现后端连接状态。
3. 实现病例列表和病例状态展示。
4. 实现预览图展示。
5. 实现局部超分演示流程。
6. 实现调用后端 RI 分析并展示进度。
7. 使用 ECharts 展示 RI 深度曲线和指标。
8. 报告页读取 `report.json` 对应 API。
9. 做 1024x600 触摸屏适配。
10. 更新 `coordination/status/frontend.status.md`。

## 文案边界

- 允许：“局部超分流程展示”“边缘端本地完成 DTI/V1/RI”。
- 禁止：“边缘端真实运行完整 DisC-Diff”“确诊 AD”。

## 验收

- 后端停止时不能显示硬编码报告。
- 报告文件缺失时显示未生成。
- 关键按钮在 1024x600 下不被遮挡。
