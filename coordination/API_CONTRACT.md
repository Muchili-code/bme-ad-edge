# API 契约

后端基础地址：

```text
http://127.0.0.1:8000
```

前端必须只依赖本文件列出的 API，不自行发明接口。

## 1. `GET /api/health`

用途：检查后端是否在线。

返回：

```json
{
  "status": "ok",
  "service": "ad-edge-backend",
  "case_root_exists": true
}
```

## 2. `GET /api/cases`

用途：扫描本地病例包并返回列表。

返回：

```json
{
  "cases": [
    {
      "case_id": "case_HC_001",
      "group": "HC",
      "display_name": "健康对照示例",
      "data_mode": "mock",
      "package_valid": true,
      "ri_analysis_done": false
    }
  ]
}
```

## 3. `GET /api/cases/{case_id}`

用途：返回病例详情、文件完整性、预览图 URL、输出状态。

## 4. `GET /api/cases/{case_id}/preview/{image_name}`

用途：返回 `preview/` 下的 PNG/JPEG。后端必须防止路径穿越。

## 5. `POST /api/cases/{case_id}/simulate-super-resolution`

用途：局部超分流程展示，只返回演示步骤和预存超分图路径，不运行真实完整 DisC-Diff。

返回：

```json
{
  "case_id": "case_HC_001",
  "mode": "visual_demo_only",
  "message": "边缘端正在展示局部超分流程，输出图像来自本地预存结果。",
  "steps": [
    "读取低分辨 dMRI patch",
    "读取 T1 解剖先验 patch",
    "展示多模态特征编码过程",
    "展示反向扩散去噪过程",
    "加载预存超分后 patch"
  ],
  "result_preview": "/api/cases/case_HC_001/preview/sr_dwi_patch.png"
}
```

## 6. `POST /api/cases/{case_id}/run-ri-analysis`

用途：读取本地 `compute/`，真实执行简化 DTI/V1/RI 计算，写入 `output/`。

成功返回：

```json
{
  "case_id": "case_HC_001",
  "status": "completed",
  "elapsed_ms": 1260,
  "generated_files": [
    "output/ri_depth_profiles.json",
    "output/roi_ri_metrics.csv",
    "output/abnormal_regions.json",
    "output/sampled_vectors.json",
    "output/report.json"
  ]
}
```

失败时返回明确原因，不能静默成功。

## 7. `GET /api/cases/{case_id}/ri-profiles`

用途：读取 `output/ri_depth_profiles.json`。文件不存在时返回未完成状态，不返回假数据。

## 8. `GET /api/cases/{case_id}/metrics`

用途：读取 `output/roi_ri_metrics.csv` 并转换为 JSON。

## 9. `GET /api/cases/{case_id}/report`

用途：读取 `output/report.json`。文件不存在时返回“报告尚未生成”。前端不能硬编码报告。
