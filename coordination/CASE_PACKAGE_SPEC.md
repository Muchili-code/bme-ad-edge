# 病例包结构契约

每个病例目录必须位于：

```text
data/cases/case_xxx/
```

固定结构：

```text
case_xxx/
  meta.json
  preview/
    lowres_dwi_slice.png
    lowres_dwi_patch.png
    t1_slice.png
    t1_patch.png
    sr_dwi_slice.png
    sr_dwi_patch.png
  compute/
    sr_dwi_4d.nii.gz
    grad.bvec
    grad.bval
    analysis_mask.nii.gz
    surface_normals.json
    depth_samples.json
    roi_map.json
    registration.json
  reference/
    roi_reference_ranges.csv
    hc_ri_template.json
  output/
    ri_depth_profiles.json
    roi_ri_metrics.csv
    abnormal_regions.json
    sampled_vectors.json
    report.json
```

## 1. `meta.json` 最小字段

```json
{
  "case_id": "case_HC_001",
  "group": "HC",
  "display_name": "健康对照示例",
  "data_mode": "mock",
  "description": "科研数据未到前使用的小型可计算模拟病例",
  "scan_protocol": "mock_dMRI_b1000_12dir",
  "processing_status": {
    "external_package_ready": true,
    "board_dti_done": false,
    "board_ri_done": false,
    "board_report_done": false
  }
}
```

## 2. `compute/` 语义

- `sr_dwi_4d.nii.gz`：后端本地计算输入，mock 阶段为小体积模拟 4D dMRI。
- `grad.bvec`：扩散方向，数量必须与 4D dMRI volume 数匹配。
- `grad.bval`：b 值，数量必须与 4D dMRI volume 数匹配。
- `analysis_mask.nii.gz`：计算 mask。
- `surface_normals.json`：采样点对应皮层法向量。
- `depth_samples.json`：每个 ROI 的 11 个深度采样点。
- `roi_map.json`：ROI 编号、名称、网络、半球。
- `registration.json`：外部数据包空间信息说明；边缘端不重新配准。

## 3. mock 数据要求

- 生成 HC / MCI / AD 三个病例。
- 建议空间尺寸 `32 x 32 x 16`。
- 建议方向数量为 1 个 b0 + 12 个 diffusion volumes。
- 建议 ROI 数量为 6。
- 每个 ROI 固定 11 个深度点。
- 输出结果必须能随着输入 mock dMRI 改变而改变。
