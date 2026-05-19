from __future__ import annotations

import csv
import json
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_case_root() -> Path:
    configured = os.getenv("CASE_ROOT")
    if not configured:
        return (PROJECT_ROOT / "data" / "cases").resolve()
    path = Path(configured)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


CASE_ROOT = _resolve_case_root()
DEPTH_PERCENT = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
GENERATED_FILES = [
    "output/ri_depth_profiles.json",
    "output/roi_ri_metrics.csv",
    "output/abnormal_regions.json",
    "output/sampled_vectors.json",
    "output/report.json",
]


class RIAnalysisError(RuntimeError):
    """Raised when a case package cannot be analyzed."""


np: Any = None
nib: Any = None
pd: Any = None
scipy_skew: Any = None


@dataclass(frozen=True)
class CasePaths:
    case_dir: Path
    dwi: Path
    bvec: Path
    bval: Path
    mask: Path
    depth_samples: Path
    surface_normals: Path
    roi_map: Path
    reference_ranges: Path
    meta: Path
    output_dir: Path


def run_ri_analysis(case_id: str, case_root: str | Path = CASE_ROOT) -> dict[str, Any]:
    """Run simplified DTI/V1/RI analysis for one local case package.

    The implementation intentionally stays inside the edge-demo scope: it reads
    the standardized local package, fits a tensor from the mock dMRI volumes,
    samples V1 at prepared cortical-column points, and writes the contracted
    output files. It does not perform DisC-Diff, registration, or preprocessing.
    """

    started = time.perf_counter()
    paths = _build_case_paths(case_id, Path(case_root))
    _require_inputs(paths)

    meta = _read_json(paths.meta)
    group = str(meta.get("group", "unknown"))
    _require_analysis_dependencies()
    roi_map = _load_roi_map(paths.roi_map)
    depth_samples = _load_depth_samples(paths.depth_samples)
    normals = _load_normals(paths.surface_normals)
    reference = _load_reference_ranges(paths.reference_ranges)

    dwi_img = nib.load(str(paths.dwi))
    dwi = np.asarray(dwi_img.get_fdata(dtype=np.float32), dtype=np.float64)
    mask = np.asarray(nib.load(str(paths.mask)).get_fdata(), dtype=bool)
    bvecs, bvals = _load_gradients(paths.bvec, paths.bval, dwi.shape)
    v1_field = _fit_v1_field(dwi, mask, bvecs, bvals)

    profiles: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    abnormal_regions: list[dict[str, Any]] = []
    sampled_vectors: list[dict[str, Any]] = []

    for roi_id, roi in roi_map.items():
        samples = depth_samples.get(roi_id)
        normal_samples = normals.get(roi_id)
        if samples is None:
            raise RIAnalysisError(f"depth_samples.json missing samples for ROI {roi_id}")
        if normal_samples is None:
            raise RIAnalysisError(f"surface_normals.json missing samples for ROI {roi_id}")

        ri_values: list[float] = []
        sample_records: list[dict[str, Any]] = []
        for sample in samples:
            depth = int(sample["depth_percent"])
            normal = normal_samples.get(depth)
            if normal is None:
                raise RIAnalysisError(
                    f"surface_normals.json missing ROI {roi_id} depth {depth}"
                )
            voxel = _nearest_voxel(sample["voxel"], dwi.shape[:3])
            if not mask[voxel]:
                raise RIAnalysisError(
                    f"Sample voxel {voxel} for ROI {roi_id} depth {depth} is outside analysis_mask"
                )
            v1 = _orient_to_normal(v1_field[voxel], normal)
            ri = float(np.clip(np.dot(v1, normal), -1.0, 1.0))
            ri_values.append(round(ri, 6))
            sample_records.append(
                {
                    "sample_id": f"{roi_id}_depth_{depth}",
                    "roi_id": roi_id,
                    "depth_percent": depth,
                    "v1": _round_vector(v1),
                    "normal": _round_vector(normal),
                    "ri": round(ri, 6),
                }
            )

        skewness = _skewness(ri_values)
        maximum = float(max(ri_values))
        ref = reference.get(roi_id)
        risk_level, pattern = _classify_risk(skewness, maximum, ref)

        profiles.append(
            {
                "roi_id": roi_id,
                "roi_name": roi["roi_name"],
                "depth_percent": [int(s["depth_percent"]) for s in samples],
                "ri_values": ri_values,
            }
        )
        row = {
            "case_id": case_id,
            "group": group,
            "roi_id": roi_id,
            "roi_name": roi["roi_name"],
            "network": roi["network"],
            "hemisphere": roi["hemisphere"],
            "ri_skewness": round(skewness, 6),
            "ri_maximum": round(maximum, 6),
            "risk_level": risk_level,
            "pattern": pattern,
        }
        metric_rows.append(row)
        sampled_vectors.extend(sample_records)
        if risk_level != "normal":
            abnormal_regions.append(
                {
                    "roi_id": roi_id,
                    "roi_name": roi["roi_name"],
                    "risk_level": risk_level,
                    "pattern": pattern,
                    "explanation": _explain_region(pattern),
                }
            )

    paths.output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(paths.output_dir / "ri_depth_profiles.json", {"case_id": case_id, "profiles": profiles})
    _write_metrics_csv(paths.output_dir / "roi_ri_metrics.csv", metric_rows)
    _write_json(paths.output_dir / "abnormal_regions.json", {"case_id": case_id, "regions": abnormal_regions})
    _write_json(paths.output_dir / "sampled_vectors.json", {"case_id": case_id, "samples": sampled_vectors})
    _write_json(
        paths.output_dir / "report.json",
        _build_report(case_id, group, metric_rows, abnormal_regions),
    )

    return {
        "case_id": case_id,
        "status": "completed",
        "elapsed_ms": int(round((time.perf_counter() - started) * 1000)),
        "generated_files": GENERATED_FILES,
    }


def _build_case_paths(case_id: str, case_root: Path) -> CasePaths:
    if "/" in case_id or "\\" in case_id or case_id in {"", ".", ".."}:
        raise RIAnalysisError(f"Invalid case_id: {case_id!r}")
    case_dir = case_root / case_id
    compute = case_dir / "compute"
    reference = case_dir / "reference"
    return CasePaths(
        case_dir=case_dir,
        dwi=compute / "sr_dwi_4d.nii.gz",
        bvec=compute / "grad.bvec",
        bval=compute / "grad.bval",
        mask=compute / "analysis_mask.nii.gz",
        depth_samples=compute / "depth_samples.json",
        surface_normals=compute / "surface_normals.json",
        roi_map=compute / "roi_map.json",
        reference_ranges=reference / "roi_reference_ranges.csv",
        meta=case_dir / "meta.json",
        output_dir=case_dir / "output",
    )


def _require_inputs(paths: CasePaths) -> None:
    required = [
        paths.case_dir,
        paths.dwi,
        paths.bvec,
        paths.bval,
        paths.mask,
        paths.depth_samples,
        paths.surface_normals,
        paths.roi_map,
        paths.reference_ranges,
        paths.meta,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RIAnalysisError("Missing required RI analysis input(s): " + ", ".join(missing))


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RIAnalysisError(f"Invalid JSON file {path}: {exc}") from exc


def _require_analysis_dependencies() -> None:
    global np, nib, pd, scipy_skew
    try:
        import nibabel as nib_module
        import numpy as np_module
        import pandas as pd_module
        from scipy.stats import skew as scipy_skew_func
    except ImportError as exc:
        raise RIAnalysisError(
            "Missing Python dependency for RI analysis. "
            "Install backend/requirements.txt in WSL before running analysis: "
            f"{exc.name}"
        ) from exc
    np = np_module
    nib = nib_module
    pd = pd_module
    scipy_skew = scipy_skew_func


def _load_roi_map(path: Path) -> dict[str, dict[str, Any]]:
    data = _read_json(path)
    rois = data.get("rois")
    if not isinstance(rois, list) or not rois:
        raise RIAnalysisError("roi_map.json must contain a non-empty rois list")
    result: dict[str, dict[str, Any]] = {}
    for roi in rois:
        roi_id = str(roi.get("roi_id", ""))
        if not roi_id:
            raise RIAnalysisError("roi_map.json contains ROI without roi_id")
        result[roi_id] = {
            "roi_name": str(roi.get("roi_name", roi_id)),
            "network": str(roi.get("network", "")),
            "hemisphere": str(roi.get("hemisphere", "")),
        }
    return result


def _load_depth_samples(path: Path) -> dict[str, list[dict[str, Any]]]:
    data = _read_json(path)
    result: dict[str, list[dict[str, Any]]] = {}
    for roi in data.get("rois", []):
        roi_id = str(roi.get("roi_id", ""))
        samples = roi.get("samples", [])
        if len(samples) != 11:
            raise RIAnalysisError(f"depth_samples.json ROI {roi_id} must contain 11 samples")
        result[roi_id] = [
            {
                "depth_percent": int(sample["depth_percent"]),
                "voxel": np.asarray(sample["voxel"], dtype=float),
            }
            for sample in samples
        ]
    if not result:
        raise RIAnalysisError("depth_samples.json contains no ROI samples")
    return result


def _load_normals(path: Path) -> dict[str, dict[int, np.ndarray]]:
    data = _read_json(path)
    result: dict[str, dict[int, np.ndarray]] = {}
    for roi in data.get("normals", []):
        roi_id = str(roi.get("roi_id", ""))
        samples: dict[int, np.ndarray] = {}
        for sample in roi.get("samples", []):
            normal = _unit_vector(np.asarray(sample["normal"], dtype=float))
            samples[int(sample["depth_percent"])] = normal
        if len(samples) != 11:
            raise RIAnalysisError(f"surface_normals.json ROI {roi_id} must contain 11 normals")
        result[roi_id] = samples
    if not result:
        raise RIAnalysisError("surface_normals.json contains no ROI normals")
    return result


def _load_reference_ranges(path: Path) -> dict[str, dict[str, float]]:
    rows = pd.read_csv(path)
    required = {
        "roi_id",
        "ri_maximum_low",
        "ri_maximum_high",
        "ri_skewness_low",
        "ri_skewness_high",
    }
    missing = required.difference(rows.columns)
    if missing:
        raise RIAnalysisError(f"roi_reference_ranges.csv missing columns: {sorted(missing)}")
    result: dict[str, dict[str, float]] = {}
    for row in rows.to_dict(orient="records"):
        result[str(row["roi_id"])] = {
            "ri_maximum_low": float(row["ri_maximum_low"]),
            "ri_maximum_high": float(row["ri_maximum_high"]),
            "ri_skewness_low": float(row["ri_skewness_low"]),
            "ri_skewness_high": float(row["ri_skewness_high"]),
        }
    return result


def _load_gradients(bvec_path: Path, bval_path: Path, dwi_shape: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    if len(dwi_shape) != 4:
        raise RIAnalysisError(f"sr_dwi_4d.nii.gz must be 4D, got shape {dwi_shape}")
    bvecs = np.loadtxt(bvec_path, dtype=float)
    bvals = np.loadtxt(bval_path, dtype=float).reshape(-1)
    if bvecs.ndim != 2:
        raise RIAnalysisError("grad.bvec must be a 2D matrix")
    if bvecs.shape[0] == 3 and bvecs.shape[1] != 3:
        bvecs = bvecs.T
    if bvecs.shape[1] != 3:
        raise RIAnalysisError(f"grad.bvec must have 3 vector components, got shape {bvecs.shape}")
    if bvecs.shape[0] != dwi_shape[3] or bvals.shape[0] != dwi_shape[3]:
        raise RIAnalysisError(
            "Gradient count must match dMRI volumes: "
            f"dwi volumes={dwi_shape[3]}, bvecs={bvecs.shape[0]}, bvals={bvals.shape[0]}"
        )
    return bvecs, bvals


def _fit_v1_field(dwi: np.ndarray, mask: np.ndarray, bvecs: np.ndarray, bvals: np.ndarray) -> np.ndarray:
    if mask.shape != dwi.shape[:3]:
        raise RIAnalysisError(f"analysis_mask shape {mask.shape} does not match dMRI shape {dwi.shape[:3]}")

    b0_idx = np.where(bvals < 50)[0]
    diff_idx = np.where(bvals >= 50)[0]
    if len(b0_idx) < 1:
        raise RIAnalysisError("grad.bval must contain at least one b0 volume with b < 50")
    if len(diff_idx) < 6:
        raise RIAnalysisError("DTI fitting requires at least 6 diffusion-weighted volumes")

    gradients = bvecs[diff_idx]
    grad_norm = np.linalg.norm(gradients, axis=1)
    valid = grad_norm > 1e-8
    if int(valid.sum()) < 6:
        raise RIAnalysisError("DTI fitting requires at least 6 non-zero diffusion directions")
    gradients = gradients[valid] / grad_norm[valid, None]
    b = bvals[diff_idx][valid]
    diffusion = dwi[..., diff_idx][..., valid]

    design = -b[:, None] * np.column_stack(
        [
            gradients[:, 0] * gradients[:, 0],
            2.0 * gradients[:, 0] * gradients[:, 1],
            2.0 * gradients[:, 0] * gradients[:, 2],
            gradients[:, 1] * gradients[:, 1],
            2.0 * gradients[:, 1] * gradients[:, 2],
            gradients[:, 2] * gradients[:, 2],
        ]
    )
    pinv = np.linalg.pinv(design)
    s0 = np.mean(dwi[..., b0_idx], axis=3)
    v1_field = np.zeros((*dwi.shape[:3], 3), dtype=float)

    coords = np.argwhere(mask)
    for x, y, z in coords:
        baseline = max(float(s0[x, y, z]), 1e-6)
        signals = np.maximum(diffusion[x, y, z, :], 1e-6)
        log_ratio = np.log(signals / baseline)
        coeff = pinv @ log_ratio
        tensor = np.array(
            [
                [coeff[0], coeff[1], coeff[2]],
                [coeff[1], coeff[3], coeff[4]],
                [coeff[2], coeff[4], coeff[5]],
            ],
            dtype=float,
        )
        tensor = 0.5 * (tensor + tensor.T)
        if not np.all(np.isfinite(tensor)):
            raise RIAnalysisError(f"Non-finite tensor fit at voxel {(int(x), int(y), int(z))}")
        eigvals, eigvecs = np.linalg.eigh(tensor)
        v1 = eigvecs[:, int(np.argmax(eigvals))]
        v1_field[x, y, z, :] = _unit_vector(v1)
    return v1_field


def _nearest_voxel(voxel: np.ndarray, shape: tuple[int, int, int]) -> tuple[int, int, int]:
    rounded = np.rint(voxel).astype(int)
    clipped = np.clip(rounded, [0, 0, 0], np.asarray(shape) - 1)
    return int(clipped[0]), int(clipped[1]), int(clipped[2])


def _unit_vector(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 1e-12:
        raise RIAnalysisError("Encountered zero-length or non-finite vector")
    return vector / norm


def _orient_to_normal(v1: np.ndarray, normal: np.ndarray) -> np.ndarray:
    v1 = _unit_vector(v1)
    normal = _unit_vector(normal)
    return -v1 if float(np.dot(v1, normal)) < 0 else v1


def _round_vector(vector: np.ndarray) -> list[float]:
    return [round(float(value), 6) for value in vector.tolist()]


def _skewness(values: list[float]) -> float:
    arr = np.asarray(values, dtype=float)
    std = float(arr.std(ddof=0))
    if std <= 1e-12:
        return 0.0
    return float(scipy_skew(arr, bias=True))


def _classify_risk(
    skewness: float, maximum: float, ref: dict[str, float] | None
) -> tuple[str, str]:
    if ref is None:
        return "unknown", "reference_missing"

    skew_high = skewness > ref["ri_skewness_high"]
    skew_low = skewness < ref["ri_skewness_low"]
    max_high = maximum > ref["ri_maximum_high"]
    max_low = maximum < ref["ri_maximum_low"]

    issue_count = int(skew_high or skew_low) + int(max_high or max_low)
    if issue_count == 0:
        return "normal", "within_reference"
    if issue_count == 2:
        return "high", "mixed_pattern"
    if max_low:
        return "medium", "ri_maximum_decreased"
    if max_high:
        return "medium", "ri_maximum_increased"
    if skew_high:
        return "medium", "ri_skewness_increased"
    return "medium", "ri_skewness_decreased"


def _explain_region(pattern: str) -> str:
    explanations = {
        "mixed_pattern": "该 ROI 同时表现出 RI Skewness 与 RI Maximum 偏离参考范围的影像特征。",
        "ri_maximum_decreased": "该 ROI 表现出 RI Maximum 低于参考范围的影像特征。",
        "ri_maximum_increased": "该 ROI 表现出 RI Maximum 高于参考范围的影像特征。",
        "ri_skewness_increased": "该 ROI 表现出 RI Skewness 高于参考范围的影像特征。",
        "ri_skewness_decreased": "该 ROI 表现出 RI Skewness 低于参考范围的影像特征。",
        "reference_missing": "该 ROI 缺少参考范围，需由模块母进程检查病例包。",
    }
    return explanations.get(pattern, "该 ROI 的 RI 指标偏离参考范围。")


def _build_report(
    case_id: str,
    group: str,
    metric_rows: list[dict[str, Any]],
    abnormal_regions: list[dict[str, Any]],
) -> dict[str, Any]:
    high_count = sum(1 for row in metric_rows if row["risk_level"] == "high")
    medium_count = sum(1 for row in metric_rows if row["risk_level"] == "medium")
    normal_count = sum(1 for row in metric_rows if row["risk_level"] == "normal")

    key_findings: list[str] = []
    if abnormal_regions:
        top = abnormal_regions[:3]
        names = "、".join(region["roi_name"] for region in top)
        key_findings.append(f"{len(abnormal_regions)} 个 ROI 的 RI 指标偏离参考范围，代表区域包括 {names}。")
    else:
        key_findings.append("所有 ROI 的 RI Skewness 与 RI Maximum 均位于参考范围内。")
    key_findings.append(
        f"风险分布：高风险 {high_count} 个，中风险 {medium_count} 个，参考范围内 {normal_count} 个。"
    )

    pattern_counts: dict[str, int] = {}
    for row in metric_rows:
        pattern_counts[row["pattern"]] = pattern_counts.get(row["pattern"], 0) + 1
    dominant_pattern = max(pattern_counts.items(), key=lambda item: item[1])[0] if pattern_counts else "none"
    key_findings.append(f"主要 RI 模式为 {dominant_pattern}，由本次 DTI/V1/RI 计算结果生成。")

    return {
        "case_id": case_id,
        "group": group,
        "title": "边缘端 RI 皮层柱辅助分析报告",
        "summary": "本报告基于本地病例包完成 DTI/V1/RI 后处理，结果仅作为影像特征辅助分析。",
        "key_findings": key_findings,
        "disclaimer": "本系统不输出临床确诊结论，仅用于竞赛 Demo 与影像特征展示。",
    }


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "case_id",
        "group",
        "roi_id",
        "roi_name",
        "network",
        "hemisphere",
        "ri_skewness",
        "ri_maximum",
        "risk_level",
        "pattern",
    ]
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
