# AD dMRI 边缘端 App 与板端后处理实施计划

## 1. 文档定位

本文档只规划边缘端需要实现的内容，对应《三人小组工作计划.md》中边缘 App 前端与可视化、边缘后端与部署集成相关任务。

本实施计划的目标是：在科研数据暂未到位的情况下，先在 WSL Ubuntu 环境中完成一套可迁移到树莓派 5 / 香橙派 AIPro 的边缘端 Demo。Demo 必须具备真实后端逻辑，能够读取本地标准化病例包，执行 mock 数据上的 DTI 拟合、V1 提取、RI 计算、指标生成和报告生成，避免只做前端页面导致程序虚跑。

本文档不规划 PC/科研端实施任务。PC/科研端只作为外部数据包来源出现，用来说明边缘端最终接收的数据结构。本文档不写 FreeSurfer、MRtrix3、FSL、ANTs、预配准、真实 DisC-Diff 训练或推理、真实科研统计分析的实施步骤。

## 2. 边界与总原则

### 2.1 本文档负责的边缘端范围

边缘端需要实现以下能力：

1. 在 WSL Ubuntu 中完成前后端开发，后续迁移到树莓派 5 / 香橙派 AIPro。
2. 实现 React 前端 App，用于病例选择、流程展示、RI 分析和报告展示。
3. 实现 FastAPI 后端服务，用于病例包扫描、文件校验、NIfTI/JSON/CSV 读取、本地计算和报告输出。
4. 从本地 `data/cases/` 读取标准化病例包。
5. 在本地完成简化版 DTI 拟合、V1 提取、RI 计算。
6. 生成 RI 深度曲线、RI Skewness、RI Maximum、异常脑区和报告 JSON。
7. 支持 1024x600 触摸屏展示，后续可部署到树莓派 5 / 香橙派 AIPro。

### 2.2 本文档不负责的内容

边缘端不实现以下内容：

1. 不实现 FreeSurfer 皮层重建。
2. 不实现 MRtrix3 / FSL / ANTs 的 dMRI 重预处理。
3. 不实现 dMRI 与 T1 的重新配准。
4. 不实现真实完整 DisC-Diff 全脑超分。
5. 不实现真实 DisC-Diff 模型训练、模型转换或 NPU 推理。
6. 不实现真实临床诊断结论。

这些内容在比赛系统中属于外部科研流程或赛前数据准备结果。边缘端只接收已经整理好的标准化病例包，并在此基础上完成后半段本地分析与展示。

### 2.3 科研数据未到时的开发策略

科研负责人还未提供真实数据时，边缘端先使用小型 mock 病例包开发。mock 病例包必须满足以下要求：

1. 包含 HC、MCI、AD 三个示例病例。
2. 包含小体积 4D dMRI、bvec/bval、采样点、法向量、ROI 映射、预览图片和参考文件。
3. 能被后端真实读取并执行简化 DTI/V1/RI 计算。
4. 输出结果由后端计算生成，不允许前端硬编码。
5. 后续真实数据到位后，只替换 `data/cases/` 中病例包，不重写前后端架构。

mock 数据生成脚本属于边缘端开发辅助工具，不代表 PC/科研端处理流程。

## 3. 推荐工程目录

边缘端工程建议单独建立为 `ad-edge-demo/`，目录如下：

```text
ad-edge-demo/
  frontend/
  backend/
  data/
    cases/
      case_HC_001/
      case_MCI_001/
      case_AD_001/
  scripts/
    generate_mock_cases.py
    validate_case_package.py
  start_demo.sh
  .env.example
  README.md
```

各目录职责：

| 路径 | 职责 |
| :--- | :--- |
| `frontend/` | React + Vite + TypeScript 前端 App。 |
| `backend/` | FastAPI 后端服务，负责病例读取、计算和报告生成。 |
| `data/cases/` | 本地病例包目录，虚拟机、树莓派、香橙派上保持同一结构。 |
| `scripts/generate_mock_cases.py` | 生成开发用小型 mock 病例包。 |
| `scripts/validate_case_package.py` | 校验病例包文件是否完整、字段是否满足契约。 |
| `start_demo.sh` | 一键启动前端和后端。 |
| `.env.example` | 配置示例，避免写死个人路径。 |

## 4. 技术栈

### 4.1 前端

前端固定使用：

```text
React + Vite + TypeScript + ECharts
```

用途：

1. React：构建病例选择、流程步骤、报告页面。
2. Vite：快速开发和打包。
3. TypeScript：约束 API 返回结构，减少字段对不齐。
4. ECharts：绘制 RI 深度曲线、ROI 指标柱状图和风险分布图。

前端禁止直接解析完整 4D NIfTI。前端只读取后端返回的 JSON、CSV 转换结果、PNG/JPEG 预览图和必要的轻量可视化资源。

### 4.2 后端

后端固定使用：

```text
FastAPI + NumPy + SciPy + nibabel + pandas
```

用途：

1. FastAPI：提供本地 HTTP API。
2. NumPy：矩阵计算、DTI 最小二乘拟合、向量点积。
3. SciPy：统计量、偏度计算等辅助计算。
4. nibabel：读取 `.nii.gz` 4D dMRI 和 mask。
5. pandas：读取和写入 ROI 指标 CSV。

### 4.3 配置原则

所有路径通过 `.env` 配置，不写死 Windows 路径、WSL 用户名路径或板端用户名路径。

建议 `.env.example`：

```text
APP_ENV=development
APP_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_PORT=5173
CASE_ROOT=./data/cases
OUTPUT_OVERWRITE=true
```

后续迁移到树莓派 5 / 香橙派时，只修改 `.env`，不改业务代码。

### 4.4 WSL 开发环境约束

开发阶段优先把工程放在 WSL Ubuntu 的 Linux 文件系统中，例如：

```text
/home/<user>/ad-edge-demo
```

Windows 侧可通过 Codex App 或 VSCode 访问 WSL 目录，但依赖安装和项目运行必须固定在 WSL 内完成：

```powershell
wsl -d Ubuntu --cd /home/<user>/ad-edge-demo -- bash -lc "npm install"
wsl -d Ubuntu --cd /home/<user>/ad-edge-demo -- bash -lc "python3 -m venv .venv"
wsl -d Ubuntu --cd /home/<user>/ad-edge-demo -- bash -lc "source .venv/bin/activate && pip install -r backend/requirements.txt"
wsl -d Ubuntu --cd /home/<user>/ad-edge-demo -- bash -lc "./start_demo.sh"
```

禁止在 Windows PowerShell 中直接对 WSL 项目运行 Windows 版 `npm install`、`pip install`、`python`、`uvicorn` 或 `vite`。项目中的 `.venv/`、`node_modules/`、`dist/`、`build/` 应只由 WSL 内的 Python/Node 工具生成。这样可以避免软链接、二进制依赖、路径分隔符和权限差异导致迁移失败。

如果已经进入 WSL 终端并位于项目根目录，后端测试不要裸跑 `python`、`pytest`、`uvicorn`。统一使用项目虚拟环境：

```bash
.venv/bin/python -m pytest backend/tests -q
.venv/bin/python backend/tests/ri_smoke.py
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

进入 WSL 不等于自动激活 `.venv`。除非明确执行 `source .venv/bin/activate`，否则 Python 命令都应写成 `.venv/bin/python` 或 `.venv/bin/uvicorn`。

## 5. 边缘端病例包契约

每个病例必须放在 `data/cases/case_xxx/` 下。第一版固定结构如下：

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

### 5.1 `meta.json`

`meta.json` 至少包含：

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

说明：

1. `external_package_ready` 只表示边缘端已收到本地标准化病例包。
2. `board_dti_done`、`board_ri_done`、`board_report_done` 由边缘端运行后更新。
3. 页面文案不能把外部数据包准备过程写成边缘端实时完成。

### 5.2 `preview/`

`preview/` 只给前端展示使用：

1. `lowres_dwi_slice.png`：低分辨 dMRI 代表性切片。
2. `lowres_dwi_patch.png`：低分辨局部 patch。
3. `t1_slice.png`：T1 代表性切片。
4. `t1_patch.png`：T1 局部 patch。
5. `sr_dwi_slice.png`：预存超分后 dMRI 代表性切片。
6. `sr_dwi_patch.png`：预存超分后局部 patch。

这些图片用于展示局部超分流程和结果对比，不代表边缘端真实运行完整 DisC-Diff。

### 5.3 `compute/`

`compute/` 是后端本地计算的输入：

1. `sr_dwi_4d.nii.gz`：超分后 4D dMRI，mock 阶段使用小体积模拟数据。
2. `grad.bvec`：扩散方向。
3. `grad.bval`：b 值。
4. `analysis_mask.nii.gz`：计算 mask，限制后端计算范围。
5. `surface_normals.json`：采样点对应的皮层法向量。
6. `depth_samples.json`：每个 ROI 的 11 个深度采样点。
7. `roi_map.json`：ROI 编号、名称、网络、半球等信息。
8. `registration.json`：外部数据包提供的空间信息说明，仅用于展示和记录，不在边缘端重新配准。

### 5.4 `reference/`

`reference/` 是参考模板，不是病例最终答案：

1. `roi_reference_ranges.csv`：各 ROI 的参考范围，用于报告中的风险提示。
2. `hc_ri_template.json`：健康参考 RI 曲线模板，用于前端对比展示。

### 5.5 `output/`

`output/` 由边缘端后端生成或刷新：

1. `ri_depth_profiles.json`：每个 ROI 的 11 个深度点 RI 曲线。
2. `roi_ri_metrics.csv`：每个 ROI 的 RI Skewness、RI Maximum、风险等级。
3. `abnormal_regions.json`：异常脑区列表和解释。
4. `sampled_vectors.json`：RI 点积演示样本，包含 V1、normal、RI。
5. `report.json`：前端报告页读取的最终辅助分析报告。

报告页必须读取 `output/report.json`，不能在前端写死结论。

## 6. 后端 API 设计

后端基础地址：

```text
http://127.0.0.1:8000
```

### 6.1 健康检查

```text
GET /api/health
```

返回示例：

```json
{
  "status": "ok",
  "service": "ad-edge-backend",
  "case_root_exists": true
}
```

### 6.2 病例列表

```text
GET /api/cases
```

功能：扫描 `CASE_ROOT` 下所有病例目录，读取 `meta.json`，校验关键文件是否存在，返回病例列表。

返回示例：

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

### 6.3 病例详情

```text
GET /api/cases/{case_id}
```

功能：返回 `meta.json`、文件完整性、预览图 URL、输出文件状态。

### 6.4 预览图读取

```text
GET /api/cases/{case_id}/preview/{image_name}
```

功能：只允许读取该病例 `preview/` 目录下的 PNG/JPEG 文件。后端必须防止路径穿越，例如禁止 `../`。

### 6.5 局部超分流程演示

```text
POST /api/cases/{case_id}/simulate-super-resolution
```

功能：返回前端演示流程节点、进度文案、预存图片路径。

返回示例：

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

该接口不能声称真实运行完整 DisC-Diff。

### 6.6 RI 分析触发

```text
POST /api/cases/{case_id}/run-ri-analysis
```

功能：后端读取 `compute/`，真实执行简化版 DTI/V1/RI 计算，并写入 `output/`。

返回示例：

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

失败时必须返回明确原因，例如缺少 `sr_dwi_4d.nii.gz`、`grad.bvec`、`surface_normals.json`。

### 6.7 RI 曲线

```text
GET /api/cases/{case_id}/ri-profiles
```

功能：读取 `output/ri_depth_profiles.json`。如果文件不存在，返回“未完成 RI 分析”，不能返回假数据。

### 6.8 ROI 指标

```text
GET /api/cases/{case_id}/metrics
```

功能：读取 `output/roi_ri_metrics.csv` 并转换为 JSON。

### 6.9 报告

```text
GET /api/cases/{case_id}/report
```

功能：读取 `output/report.json`。如果文件不存在，返回“报告尚未生成”。前端不能自己拼接最终结论。

## 7. 后端核心计算流程

### 7.1 mock 病例生成

`scripts/generate_mock_cases.py` 负责生成开发用病例包。

建议生成参数：

```text
空间尺寸：32 x 32 x 16
方向数量：12 个 diffusion volume + 1 个 b0
ROI 数量：6 个示例 ROI
每个 ROI：11 个深度点
病例数量：HC / MCI / AD 各 1 个
```

mock 数据设计要求：

1. HC：RI 曲线接近倒 U 型，峰值较高。
2. MCI：RI 曲线形状部分保留，峰值略低。
3. AD：部分 ROI 出现峰值下降，部分 ROI 出现曲线偏斜。
4. 数据应加入少量噪声，保证重新计算结果来自输入数据，而不是固定字符串。

### 7.2 病例包校验

`scripts/validate_case_package.py` 和后端启动时的校验逻辑都要检查：

1. 必需文件是否存在。
2. `meta.json` 是否包含 `case_id`、`group`、`display_name`、`processing_status`。
3. `grad.bvec`、`grad.bval` 数量是否与 4D dMRI 最后一维匹配。
4. `depth_samples.json` 是否每个 ROI 有 11 个深度点。
5. `surface_normals.json` 是否能为采样点提供对应法向量。
6. `output/` 可写。

### 7.3 简化 DTI 拟合

后端在 `run-ri-analysis` 中执行简化 DTI 拟合：

1. 用 nibabel 读取 `sr_dwi_4d.nii.gz`。
2. 读取 `grad.bvec` 和 `grad.bval`。
3. 找到 b0 volume 和 diffusion volumes。
4. 对采样点附近体素读取信号。
5. 使用线性最小二乘估计 3x3 扩散张量。
6. 对张量做特征分解。
7. 取最大特征值对应特征向量作为 V1。

第一版只需要服务 mock 小数据和展示流程，不追求科研级 DTI 精度，但必须是真实矩阵计算。

### 7.4 RI 计算

每个采样点计算：

```text
RI = abs(dot(normalize(V1), normalize(normal)))
```

使用绝对值的原因：V1 方向存在正负号不确定性，取绝对值可以避免同一主方向因符号翻转导致 RI 变成负数。

每个 ROI 输出 11 个深度点的 RI 曲线。

### 7.5 指标计算

每个 ROI 计算：

1. `RI Maximum`：11 个深度点 RI 的最大值。
2. `RI Skewness`：11 个深度点 RI 曲线的偏度。
3. `risk_level`：根据 `reference/roi_reference_ranges.csv` 给出 `normal`、`mild`、`high`。
4. `pattern`：根据指标给出 `posterior_skewness_high`、`frontal_maximum_low`、`mixed_pattern` 或 `none`。

第一版只做 RI、RI Skewness、RI Maximum，不扩展 ADC、FA、皮层厚度。

### 7.6 输出文件格式

`ri_depth_profiles.json` 示例：

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

`roi_ri_metrics.csv` 列名固定：

```text
case_id,group,roi_id,roi_name,network,hemisphere,ri_skewness,ri_maximum,risk_level,pattern
```

`abnormal_regions.json` 示例：

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

`report.json` 示例：

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

## 8. 前端页面实现

前端初版固定 5 个页面，不做复杂路由也可以，但要有清晰步骤导航。

### 8.1 病例选择页

功能：

1. 调用 `GET /api/cases`。
2. 显示 HC、MCI、AD 三个病例卡片。
3. 显示病例包是否完整。
4. 显示是否已完成 RI 分析。
5. 点击病例进入输入概览页。

异常处理：

1. 后端未启动时，页面显示“边缘后端服务未连接”。
2. 病例包不完整时，按钮置灰或显示“请检查本地病例包”。
3. 不允许在无后端情况下直接进入报告页显示假结果。

### 8.2 输入概览页

功能：

1. 展示低分辨 dMRI 切片。
2. 展示 T1 切片。
3. 展示预存超分后 dMRI 切片。
4. 展示病例包状态。

推荐文案：

```text
边缘端正在读取本地标准化病例包。
重型影像处理结果已作为外部数据包输入，当前设备负责后续 DTI/V1/RI 分析与报告生成。
```

禁止文案：

```text
边缘端正在实时完成 FreeSurfer。
边缘端正在实时完成全脑配准。
边缘端正在真实运行完整 DisC-Diff。
```

### 8.3 局部超分演示页

功能：

1. 展示低分辨 dMRI patch。
2. 展示 T1 patch。
3. 点击“运行局部超分流程演示”。
4. 调用 `POST /api/cases/{case_id}/simulate-super-resolution`。
5. 按步骤显示流程动画。
6. 展示预存超分后 patch。

页面必须明确：

```text
该步骤为局部超分流程展示，输出图像来自本地预存结果；完整 DisC-Diff 全脑超分不在边缘端实时运行。
```

### 8.4 RI 分析页

功能：

1. 点击“开始边缘端 RI 分析”。
2. 调用 `POST /api/cases/{case_id}/run-ri-analysis`。
3. 显示后端返回的运行状态、耗时和生成文件。
4. 成功后调用 `GET /api/cases/{case_id}/ri-profiles`。
5. 使用 ECharts 绘制 11 个深度点 RI 曲线。
6. 可选择不同 ROI。
7. 展示 RI Maximum 和 RI Skewness 指标卡片。

这一页是防止“程序虚跑”的核心页面。前端必须等待后端计算成功后再显示结果。

### 8.5 报告页

功能：

1. 调用 `GET /api/cases/{case_id}/report`。
2. 展示病例摘要。
3. 展示 RI 曲线简图。
4. 展示异常 ROI 表格。
5. 展示辅助分析结论。
6. 展示免责声明。

报告措辞只能使用：

```text
辅助分析
风险提示
影像特征
可能提示
```

禁止使用：

```text
确诊 AD
诊断为 AD
临床诊断结论
```

前端页面组成的风格见《Page style.md》

## 9. 一键启动与部署

### 9.1 WSL Ubuntu 开发

第一阶段在 WSL Ubuntu 中完成。项目目录必须放在 WSL 的 Linux 文件系统内，推荐路径为 `/home/<user>/ad-edge-demo`，不要放在 Windows 盘挂载路径如 `/mnt/c/...` 下。

1. 在 WSL Ubuntu 中安装 Python 3.10+。
2. 在 WSL Ubuntu 中安装 Node.js 18+。
3. 在 WSL 项目目录中创建 Python 虚拟环境。
4. 在 WSL 中安装后端依赖。
5. 在 WSL 中安装前端依赖。
6. 运行 `scripts/generate_mock_cases.py` 生成病例包。
7. 运行 `scripts/validate_case_package.py` 校验病例包。
8. 运行 `./start_demo.sh` 启动 Demo。
9. 浏览器访问前端地址。

所有安装和运行命令都必须通过 WSL shell 执行。若从 Windows 侧通过 Codex App 下发命令，应使用：

```powershell
wsl -d Ubuntu --cd /home/<user>/ad-edge-demo -- bash -lc "<command>"
```

不要用 Windows 版 Node.js 或 Python 操作该项目的依赖目录。

### 9.2 `start_demo.sh` 要求

`start_demo.sh` 负责：

1. 检查 `.env` 是否存在，不存在则提示从 `.env.example` 复制。
2. 检查 `data/cases/` 是否存在。
3. 启动 FastAPI 后端。
4. 启动 Vite 前端或生产静态服务。
5. 输出访问地址。
6. 检查当前系统是否为 Linux；如果在 Windows PowerShell 中被直接执行，应提示改用 WSL 运行。

第一版可以在两个终端分别启动前后端，但最终演示前必须提供一键启动脚本。

### 9.3 树莓派 5 / 香橙派迁移要求

迁移时只允许改：

1. `.env` 中的路径和端口。
2. Python/Node 安装方式。
3. 触摸屏分辨率配置。
4. 开机自启动配置。

迁移时不应改：

1. API 契约。
2. 病例包结构。
3. 前端页面逻辑。
4. 后端 DTI/V1/RI 主流程。

## 10. 反虚跑验收标准

实现完成后必须通过以下测试。

### 10.1 无科研数据时

1. `generate_mock_cases.py` 能生成 HC、MCI、AD 三个小型病例包。
2. 每个病例包都能被 `validate_case_package.py` 校验通过。
3. 前端能完整走完病例选择、超分演示、RI 分析、报告生成。
4. `output/` 中确实生成 JSON 和 CSV 文件。

### 10.2 后端依赖测试

1. 停止后端后，前端不能生成报告。
2. 前端应提示“边缘后端服务未连接”。
3. 前端不能使用写死的默认报告继续展示。

### 10.3 计算文件缺失测试

1. 删除某病例的 `compute/sr_dwi_4d.nii.gz`。
2. 点击 RI 分析。
3. 后端必须返回失败。
4. 前端必须提示缺失计算文件。
5. 页面不能展示旧的假曲线。

### 10.4 报告文件缺失测试

1. 删除 `output/report.json`。
2. 进入报告页。
3. 前端必须提示“报告尚未生成”。
4. 前端不能硬编码辅助分析结论。

### 10.5 输入变化测试

1. 修改 mock dMRI 数据或重新生成病例包。
2. 重新运行 RI 分析。
3. RI 曲线、RI Maximum 或 RI Skewness 应发生变化。
4. 若输出完全不变，需要检查是否仍在读取旧结果或硬编码结果。

### 10.6 断网测试

1. 关闭网络。
2. 启动 Demo。
3. 前端和后端仍能在本地运行。
4. 已有病例包能完成本地 RI 分析和报告生成。

### 10.7 触摸屏测试

1. 页面在 1024x600 分辨率下不出现关键按钮遮挡。
2. 主要按钮适合触摸点击。
3. 报告页可完整滚动查看。
4. 图表文字不重叠。

### 10.8 WSL 环境一致性测试

1. `which node`、`which npm`、`which python3`、`which pip` 均应指向 WSL 内路径。
2. `node_modules/` 和 `.venv/` 均应在 WSL 项目目录内由 WSL 工具生成。
3. 从 Windows 侧只能通过 `wsl -d Ubuntu --cd ... -- bash -lc "<command>"` 运行项目命令。
4. 不允许出现 Windows 版 Python/Node 生成的依赖目录。
5. `./start_demo.sh` 在 WSL 中可启动；若被 Windows shell 直接调用，应提示使用 WSL。

## 11. 开发里程碑

### 阶段 1：边缘端工程骨架

目标：搭建可运行的前后端空工程。

任务：

1. 创建 `frontend/` React + Vite + TypeScript 项目。
2. 创建 `backend/` FastAPI 项目。
3. 创建 `.env.example`。
4. 创建 `data/cases/`。
5. 创建基础 `GET /api/health`。
6. 前端显示后端连接状态。

验收：

1. 后端 `/api/health` 返回 `ok`。
2. 前端能显示后端在线。

### 阶段 2：mock 病例包与病例列表

目标：无科研数据也能开发完整边缘端流程。

任务：

1. 实现 `generate_mock_cases.py`。
2. 实现 `validate_case_package.py`。
3. 生成 HC/MCI/AD 三个病例包。
4. 后端实现 `GET /api/cases` 和 `GET /api/cases/{case_id}`。
5. 前端实现病例选择页。

验收：

1. 三个病例都能显示。
2. 文件缺失时能提示数据包不完整。

### 阶段 3：输入概览与局部超分流程演示

目标：完成边缘端展示链路前半段。

任务：

1. 后端实现预览图接口。
2. 后端实现 `simulate-super-resolution`。
3. 前端实现输入概览页。
4. 前端实现局部超分演示页。
5. 页面明确标注该步骤为流程展示。

验收：

1. 能展示低分辨 dMRI、T1、预存超分结果。
2. 点击演示按钮后，能按步骤展示流程。
3. 页面不出现“真实运行完整 DisC-Diff”的错误文案。

### 阶段 4：边缘端 DTI/V1/RI 后处理

目标：实现真正的后端计算链路。

任务：

1. 后端读取 4D dMRI、bvec/bval、采样点、法向量。
2. 实现简化 DTI 拟合。
3. 实现 V1 提取。
4. 实现 RI 计算。
5. 生成 `ri_depth_profiles.json`、`roi_ri_metrics.csv`、`sampled_vectors.json`。
6. 前端实现 RI 分析页。

验收：

1. 点击“开始边缘端 RI 分析”后，后端真实计算。
2. `output/` 文件被创建或刷新。
3. 前端显示 11 个深度点 RI 曲线。
4. 删除计算输入文件会导致计算失败，而不是继续展示假结果。

### 阶段 5：报告生成与辅助分析展示

目标：完成闭环。

任务：

1. 后端生成 `abnormal_regions.json`。
2. 后端生成 `report.json`。
3. 前端实现报告页。
4. 报告页显示辅助分析结论和免责声明。

验收：

1. 报告来自后端生成文件。
2. 删除 `report.json` 后前端不能显示硬编码报告。
3. 报告不出现“确诊 AD”等临床诊断表述。

### 阶段 6：部署与迁移准备

目标：让 Demo 可以离开开发电脑运行。

任务：

1. 完成 `start_demo.sh`。
2. 编写 WSL Ubuntu 启动说明。
3. 测试断网运行。
4. 测试 1024x600 页面适配。
5. 准备树莓派 5 / 香橙派迁移说明。

验收：

1. 一键启动前后端。
2. 断网可用。
3. 触摸屏分辨率可用。
4. 修改 `.env` 后可切换病例目录。

## 12. 页面文案约束

允许使用：

1. “边缘端读取本地标准化病例包”。
2. “边缘端本地完成 DTI/V1/RI 后处理”。
3. “局部超分流程展示”。
4. “预存超分结果对比”。
5. “辅助分析报告”。
6. “影像特征风险提示”。

禁止使用：

1. “边缘端真实运行完整 DisC-Diff”。
2. “边缘端实时完成 FreeSurfer”。
3. “边缘端实时完成全脑配准”。
4. “边缘端实时完成完整科研级预处理”。
5. “确诊 AD”。
6. “临床诊断结论”。

## 13. 最终交付物

边缘端第一版完成后应交付：

1. 可运行的 `frontend/`。
2. 可运行的 `backend/`。
3. 可生成 mock 病例包的 `generate_mock_cases.py`。
4. 可校验病例包的 `validate_case_package.py`。
5. HC/MCI/AD 三个 mock 病例包。
6. 一键启动脚本 `start_demo.sh`。
7. WSL Ubuntu 运行说明。
8. 树莓派 5 / 香橙派迁移说明。
9. 反虚跑测试记录。

## 14. 一句话实现目标

第一版边缘端 Demo 的目标不是复现完整科研管线，而是在没有真实科研数据的情况下，先用可计算 mock 病例包把“本地病例包读取 - 局部超分流程展示 - DTI/V1/RI 真实后处理 - 报告生成 - 触摸屏展示”闭环做实；真实病例包到位后，替换数据即可进入联调。
