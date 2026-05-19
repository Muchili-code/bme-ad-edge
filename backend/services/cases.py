import json
import os
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

REQUIRED_PREVIEW_FILES = (
    "lowres_dwi_slice.png",
    "lowres_dwi_patch.png",
    "t1_slice.png",
    "t1_patch.png",
    "sr_dwi_slice.png",
    "sr_dwi_patch.png",
)

REQUIRED_COMPUTE_FILES = (
    "sr_dwi_4d.nii.gz",
    "grad.bvec",
    "grad.bval",
    "analysis_mask.nii.gz",
    "surface_normals.json",
    "depth_samples.json",
    "roi_map.json",
    "registration.json",
)

REQUIRED_REFERENCE_FILES = (
    "roi_reference_ranges.csv",
    "hc_ri_template.json",
)

OUTPUT_FILES = (
    "ri_depth_profiles.json",
    "roi_ri_metrics.csv",
    "abnormal_regions.json",
    "sampled_vectors.json",
    "report.json",
)

ALLOWED_PREVIEW_SUFFIXES = {".png", ".jpg", ".jpeg"}


class CasePackageError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def case_root_exists() -> bool:
    return CASE_ROOT.is_dir()


def list_cases() -> list[dict[str, Any]]:
    if not CASE_ROOT.is_dir():
        return []

    cases = []
    for case_dir in sorted(CASE_ROOT.iterdir()):
        if not case_dir.is_dir():
            continue

        meta = _read_meta_if_available(case_dir)
        case_id = str(meta.get("case_id") or case_dir.name)
        cases.append(
            {
                "case_id": case_id,
                "group": meta.get("group", "unknown"),
                "display_name": meta.get("display_name", case_id),
                "data_mode": meta.get("data_mode", "unknown"),
                "package_valid": _package_integrity(case_dir)["package_valid"],
                "ri_analysis_done": _ri_analysis_done(case_dir),
            }
        )
    return cases


def case_detail(case_id: str) -> dict[str, Any]:
    case_dir = _case_dir(case_id)
    meta = _read_meta(case_dir)
    integrity = _package_integrity(case_dir)

    return {
        "case_id": meta.get("case_id", case_id),
        "group": meta.get("group"),
        "display_name": meta.get("display_name"),
        "data_mode": meta.get("data_mode"),
        "description": meta.get("description"),
        "scan_protocol": meta.get("scan_protocol"),
        "processing_status": meta.get("processing_status", {}),
        "package_valid": integrity["package_valid"],
        "file_integrity": integrity,
        "preview_images": {
            name: f"/api/cases/{case_id}/preview/{name}"
            for name in REQUIRED_PREVIEW_FILES
            if (case_dir / "preview" / name).is_file()
        },
        "output_status": _output_status(case_dir),
    }


def preview_image_path(case_id: str, image_name: str) -> Path:
    if Path(image_name).name != image_name:
        raise CasePackageError("Invalid preview image name: path segments are not allowed.", 400)

    suffix = Path(image_name).suffix.lower()
    if suffix not in ALLOWED_PREVIEW_SUFFIXES:
        raise CasePackageError("Invalid preview image type: only PNG/JPEG files are allowed.", 400)

    case_dir = _case_dir(case_id)
    preview_dir = (case_dir / "preview").resolve()
    image_path = (preview_dir / image_name).resolve()

    if not _is_relative_to(image_path, preview_dir):
        raise CasePackageError("Invalid preview image path: path traversal is not allowed.", 400)
    if not image_path.is_file():
        raise CasePackageError(f"Preview image not found: {image_name}", 404)

    return image_path


def simulate_super_resolution(case_id: str) -> dict[str, Any]:
    case_dir = _case_dir(case_id)
    preview_image_path(case_id, "sr_dwi_patch.png")
    if not (case_dir / "preview" / "lowres_dwi_patch.png").is_file():
        raise CasePackageError("Required low-resolution DWI patch is missing.", 422)
    if not (case_dir / "preview" / "t1_patch.png").is_file():
        raise CasePackageError("Required T1 patch is missing.", 422)

    return {
        "case_id": case_id,
        "mode": "visual_demo_only",
        "message": "边缘端正在展示局部超分流程，输出图像来自本地预存结果。",
        "steps": [
            "读取低分辨 dMRI patch",
            "读取 T1 解剖先验 patch",
            "展示多模态特征编码过程",
            "展示反向扩散去噪过程",
            "加载预存超分后 patch",
        ],
        "result_preview": f"/api/cases/{case_id}/preview/sr_dwi_patch.png",
    }


def _case_dir(case_id: str) -> Path:
    if Path(case_id).name != case_id:
        raise CasePackageError("Invalid case_id: path segments are not allowed.", 400)

    case_dir = (CASE_ROOT / case_id).resolve()
    if not _is_relative_to(case_dir, CASE_ROOT):
        raise CasePackageError("Invalid case_id: path traversal is not allowed.", 400)
    if not case_dir.is_dir():
        raise CasePackageError(f"Case not found: {case_id}", 404)

    return case_dir


def _read_meta(case_dir: Path) -> dict[str, Any]:
    meta_path = case_dir / "meta.json"
    if not meta_path.is_file():
        raise CasePackageError(f"Missing meta.json for case: {case_dir.name}", 422)

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CasePackageError(f"Invalid meta.json for case: {case_dir.name}", 422) from exc

    if not isinstance(meta, dict):
        raise CasePackageError(f"Invalid meta.json root for case: {case_dir.name}", 422)

    expected_case_id = meta.get("case_id")
    if expected_case_id and expected_case_id != case_dir.name:
        raise CasePackageError(
            f"meta.json case_id does not match directory name: {case_dir.name}",
            422,
        )

    return meta


def _read_meta_if_available(case_dir: Path) -> dict[str, Any]:
    try:
        return _read_meta(case_dir)
    except CasePackageError:
        return {}


def _package_integrity(case_dir: Path) -> dict[str, Any]:
    sections = {
        "root": ("meta.json",),
        "preview": tuple(f"preview/{name}" for name in REQUIRED_PREVIEW_FILES),
        "compute": tuple(f"compute/{name}" for name in REQUIRED_COMPUTE_FILES),
        "reference": tuple(f"reference/{name}" for name in REQUIRED_REFERENCE_FILES),
    }
    missing_by_section: dict[str, list[str]] = {}
    present_by_section: dict[str, list[str]] = {}

    for section, relative_paths in sections.items():
        missing = []
        present = []
        for relative_path in relative_paths:
            if (case_dir / relative_path).is_file():
                present.append(relative_path)
            else:
                missing.append(relative_path)
        missing_by_section[section] = missing
        present_by_section[section] = present

    missing_files = [
        relative_path
        for missing in missing_by_section.values()
        for relative_path in missing
    ]

    return {
        "package_valid": not missing_files,
        "missing_files": missing_files,
        "missing_by_section": missing_by_section,
        "present_by_section": present_by_section,
    }


def _output_status(case_dir: Path) -> dict[str, Any]:
    files = {}
    for name in OUTPUT_FILES:
        output_path = case_dir / "output" / name
        files[name] = {
            "exists": output_path.is_file(),
            "path": f"output/{name}",
        }

    return {
        "ri_analysis_done": _ri_analysis_done(case_dir),
        "files": files,
    }


def _ri_analysis_done(case_dir: Path) -> bool:
    return all((case_dir / "output" / name).is_file() for name in OUTPUT_FILES)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
