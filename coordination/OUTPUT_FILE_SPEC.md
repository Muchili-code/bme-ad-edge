# 输出文件契约

后端 `run-ri-analysis` 必须写入病例 `output/` 目录。前端只能读取这些输出，不允许硬编码最终结果。

## 1. `ri_depth_profiles.json`

```json
{
  "case_id": "case_HC_001",
  "profiles": [
    {
      "roi_id": "ROI_001",
      "roi_name": "Superior Parietal",
      "depth_percent": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
      "ri_values": [0.42, 0.50, 0.61, 0.70, 0.77, 0.82, 0.79, 0.71, 0.60, 0.51, 0.43]
    }
  ]
}
```

## 2. `roi_ri_metrics.csv`

固定列名：

```text
case_id,group,roi_id,roi_name,network,hemisphere,ri_skewness,ri_maximum,risk_level,pattern
```

## 3. `abnormal_regions.json`

```json
{
  "case_id": "case_AD_001",
  "regions": [
    {
      "roi_id": "ROI_004",
      "roi_name": "Inferior Parietal",
      "risk_level": "high",
      "pattern": "mixed_pattern",
      "explanation": "该 ROI 同时表现出 RI Skewness 升高和 RI Maximum 降低的影像特征。"
    }
  ]
}
```

## 4. `sampled_vectors.json`

用于 RI 点积演示，至少包含：

```json
{
  "case_id": "case_HC_001",
  "samples": [
    {
      "sample_id": "ROI_001_depth_50",
      "roi_id": "ROI_001",
      "depth_percent": 50,
      "v1": [0.1, 0.2, 0.97],
      "normal": [0.0, 0.0, 1.0],
      "ri": 0.97
    }
  ]
}
```

## 5. `report.json`

```json
{
  "case_id": "case_AD_001",
  "group": "AD",
  "title": "边缘端 RI 皮层柱辅助分析报告",
  "summary": "本报告基于本地病例包完成 DTI/V1/RI 后处理，结果仅作为影像特征辅助分析。",
  "key_findings": [
    "部分后部网络 ROI 出现 RI Skewness 升高。",
    "部分额叶/顶叶 ROI 出现 RI Maximum 降低。"
  ],
  "disclaimer": "本系统不输出临床确诊结论，仅用于竞赛 Demo 与影像特征展示。"
}
```
