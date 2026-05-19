# 香橙派 AIPro 20T

## 一、为什么选择香橙派 AIPro 20T

本项目的硬件 Demo 目标，不是现场完整复现论文中的全部科研计算管线，而是在低成本国产边缘计算设备上展示“临床 dMRI 输入 - AI 超分流程 - RI 皮层柱分析 - 可视化报告”的工程闭环。

在这个目标下，香橙派 AIPro 20T 的价值不在于“硬扛完整 DisC-Diff”，而在于：

- 具备国产 AI 平台属性，适合比赛展示
- 带有较完整的 Linux 生态
- 可以运行前端 App、后端服务和本地后处理流程
- 适合作为“PC 一次性打包后，板端继续独立完成后续链路”的载体

预算紧张时，优先购买 **12GB 内存版本** 就够用。因为当前方案里，板端不真实运行完整全脑 DisC-Diff，也不跑 FreeSurfer，而是负责：

- 前端展示
- 本地读取病例包
- 本地 DTI 拟合
- 本地 V1 提取
- 本地 RI 计算
- 本地报告生成

## 二、核心参数与项目意义

| 参数 | 含义 | 对本项目的意义 |
| :--- | :--- | :--- |
| AI 算力：20 TOPS | 常用于描述 NPU 的整数推理能力 | 有利于展示国产边缘 AI 平台定位；当前 Demo 不真实运行 DisC-Diff，而是做前端超分流程模拟与本地后处理 |
| AI 处理器：昇腾生态 NPU | 面向神经网络推理的国产 AI 加速单元 | 有利于强调国产化、边缘 AI、医疗数据本地处理 |
| 内存：12GB/24GB LPDDR4X | 用于系统、前后端服务和数据缓存 | 12GB 版可满足初版展示；前提是前端不整包加载 4D dMRI，后端按需读取计算包 |
| 存储：eMMC/M.2 SSD 支持 | 保存系统、App、病例数据包和可视化资源 | 建议加 M.2 SSD 或高速存储卡，把病例包和 4D dMRI 计算包放在本地 |
| HDMI / 显示接口 | 可外接便携触摸屏或显示器 | 适合做一体化医疗盒子 |
| USB / 网口 | 用于外接 U 盘、键鼠、触摸屏、局域网调试 | 方便模拟从医院工作站导入病例包 |
| Linux 系统支持 | 可运行 Ubuntu/openEuler 等系统 | 便于部署 Web 前端、Node/Python 后端和本地后处理程序 |

## 三、哪些任务适合放在香橙派上

适合在板端完成：

1. 前端 App 展示：病例选择、图像对比、流程动画、报告页面。
2. 局部超分流程演示：前端展示一个 3D patch 或代表性切片从低分辨率到超分结果的处理流程，输出图像来自预存结果，不在板端真实运行 DisC-Diff。
3. 加载标准化计算包：读取科研端提前生成的超分图像、超分后 4D dMRI、`bvec/bval`、表面法向量和采样规则。
4. 本地 DTI 拟合与 V1 提取：基于超分后 4D dMRI 和 `bvec/bval`，在板端继续完成 V1 计算。
5. RI 计算与报告生成：基于板端本地拟合出的 V1 和表面法向量计算 RI，并输出 AD/MCI/HC 对比、RI Skewness、RI Maximum、异常脑区和可视化结论。

不在板端完成：

1. FreeSurfer 全脑皮层重建。
2. MRtrix3/FSL/ANTs 的完整 dMRI 预处理和重新配准。
3. 完整全脑 4D dMRI 的 DisC-Diff 扩散模型超分。
4. 局部 3D patch 的真实 DisC-Diff 模型推理。
5. 任何需要 PC 端再次介入的数据回传或二次科研处理。

这套分工最重要的价值是：

**PC 端做一次，板端后续自己算，不需要 PC 再回来补一步。**

## 四、推荐的数据包结构

每个脱敏病例建议准备一份标准化数据包：

```text
case_HC_001/
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
    hc_ri_template.json
    roi_reference_ranges.csv
  output/
    ri_depth_profiles.json
    roi_ri_metrics.csv
    abnormal_regions.json
    sampled_vectors.json
  surface/
    brain_mesh.glb
    ri_texture.png
  report/
    report_template.json
```

这些目录分别对应：

- `preview/`：前端快速展示
- `compute/`：板端本地继续计算的输入
- `reference/`：参考模板
- `output/`：板端本地输出
- `surface/`：脑区可视化
- `report/`：报告模板

这里最关键的是 `compute/`：

- 只要 PC 端把这里准备完整，板端就能坚持“自己算 V1”
- 而不是再回头找 PC 要结果

## 五、为什么 12GB 版依然可行

12GB 版可行，但前提是工程策略要对。

正确做法不是：

- 让前端直接打开完整 4D NIfTI
- 让界面一次性吞下所有大体量数据

正确做法是：

1. **前端只读轻量展示资源**
   - PNG
   - JSON
   - CSV
   - GLB

2. **板端后端按需读取 4D dMRI 计算包**
   - 从本地 SSD 或高速存储中读取
   - 必要时结合 `analysis_mask.nii.gz`
   - 只在 RI 分析相关区域、采样邻域或目标 ROI 范围内做 DTI/V1

3. **前端只接收板端后端算好的中间结果**
   - V1 采样结果
   - RI 曲线
   - ROI 指标
   - 报告 JSON

也就是说，你们不是否认 4D dMRI 的存在，而是把它留给板端后端处理，而不是交给前端硬吃。

## 六、答辩时的推荐说法

可以这样表述：

> 我们选择香橙派 AIPro 20T 作为低成本国产边缘 AI 平台。完整的科研级管线中，FreeSurfer 皮层重建、dMRI 预处理、预配准和全脑 DisC-Diff 超分属于重型离线流程，先在 PC/工作站完成；随后把超分后 4D dMRI、bvec/bval 和皮层几何先验打包到板端。边缘盒子负责临床现场的数据接入、局部超分流程前端演示，并在本地完成 DTI 拟合、V1 提取、RI 计算、脑区可视化和报告生成。这样既符合医疗数据本地处理和隐私保护需求，也能在比赛现场稳定展示完整工程闭环。

不要说：

> 我们在香橙派上实时跑完整全脑 DisC-Diff，并实时完成全脑配准和皮层柱分析。

> 我们在香橙派上真实运行局部 DisC-Diff 超分模型。

这两句都会把你拖进算力、内存、模型权重、运行时间和工具链追问里。

## 七、总结

香橙派 AIPro 20T 在你这个项目里最合理的定位不是“科研工作站替代品”，而是：

**一个可以承接标准化病例包，在本地完成后半段医学影像后处理，并把整套流程讲清楚的国产边缘 AI 展示终端。**

只要你始终坚持下面这句，整套逻辑就稳：

**PC 端一次性完成预处理、预配准和全脑超分；板端接包后独立完成 DTI、V1、RI 和报告。**
