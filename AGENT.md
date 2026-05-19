请仔细阅读当前工作目录 E:\Contest\BMEdesign\Zxx 的项目文件，重点详细阅读以下文件：
1. 《OHBM on AD.pdf》：论文原文，研究主题是基于 DisC-Diff 的临床 dMRI 超分辨率，以及 AD/MCI/HC 的皮层柱 RI 微结构分析。
    阅读要求掌握论文的完整工作方式、实验结果以及操作步骤。
2. 《完整工作流.png》与《OHBM_AD_dMRI_workflow_teaching.pdf》：我对论文工作流的可视化总结。
    你需要结合这两个文件对论文原文加深理解。
3. 《展示形式.md》：我计划参加 BME 竞赛的硬件 Demo 展示方案，目前方案是使用香橙派 AIPro 20T 12GB 版做低成本国产边缘 AI 盒子。
    对于这个文件，你需要理解我关于展示的核心政策、工作流程并掌握此套流程与论文之间的差异，这是面向比赛的工程化与科研结果之间的差异，是我针对比赛展示并结合硬件、经费等因素总结出的工作流，专门用于比赛展示。后续会对《展示形式.md》进行优化，并依据此文件的工作流完成整套工作，使得项目看起来闭环。
4. 《Question.md》：之前对展示方案合理性、数据需求、PC/板端分工和答辩风险的分析。
    对于项目答辩时评委可能提出的疑问、方案的需求与疑问等都会被写入此文件并且相应问题的解答也会写入此文件。
5. 《香橙派 aipro.md》：香橙派 AIPro 20T 的参数解释及其对本项目的意义。

另外请忽略 报名材料/ 文件夹、Preparation/文件夹、backups/文件夹、竞赛分析.md 和 背景了解.md。

其他说明：

- 请先理解项目背景：这个项目基于论文《AI-based Super-Resolution Diffusion MRI Unveils Heterogeneous Cortical Microstructural Alterations in Alzheimer’s Disease》，核心流程是 ADNI 临床 dMRI/T1 数据 -> 预处理 -> DisC-Diff 超分辨率 -> 皮层柱 11 个深度点采样 -> 计算 RI = V1 与皮层法向量点积 -> 提取 RI Skewness 与 RI Maximum -> 比较 HC/MCI/AD 并生成可视化报告。
- 当前工程 Demo 的核心策略是：PC/科研端离线完成 FreeSurfer、MRtrix3/FSL/ANTs 预处理、dMRI 与 T1 的预配准、全脑 DisC-Diff 超分以及皮层柱采样几何准备，并把超分后 4D dMRI、bvec/bval、表面法向量、11 个深度采样点和 ROI 映射打包；香橙派 AIPro 20T 负责现场前端展示、前端模拟局部 3D patch/代表性切片的超分处理流程、加载标准化数据包、在板端本地完成 DTI 拟合得到 V1、继续执行 RI 计算、生成报告和脑区可视化。香橙派 AIPro 20T 终端端不真实运行 DisC-Diff 超分模型，超分阶段只在前端显示流程、中间状态、进度和预存的超分前后对比结果；数据包交付后不再依赖 PC 端二次参与。请后续所有设计、代码和文档都围绕这个工作流展开。
- 按要求阅读完上述文件并了解项目后，列出你实际阅读过的文件清单，并标明每个文件是“全文阅读 / 提取正文阅读 / 实际查看图片”。





```
请严格按照 AGENT.md 了解项目。然后最后一行回复“已了解”。
```

