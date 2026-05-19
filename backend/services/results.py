from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

from backend.services.cases import CasePackageError


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
METRIC_COLUMNS = [
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


def read_ri_profiles(case_id: str, case_root: str | Path = CASE_ROOT) -> dict[str, Any]:
    path = _output_file(case_id, "ri_depth_profiles.json", case_root)
    return _read_required_json(path, "RI depth profiles are not completed yet.")


def read_metrics(case_id: str, case_root: str | Path = CASE_ROOT) -> dict[str, Any]:
    path = _output_file(case_id, "roi_ri_metrics.csv", case_root)
    if not path.is_file():
        return {
            "case_id": case_id,
            "status": "not_completed",
            "message": "RI metrics are not completed yet.",
            "metrics": [],
        }

    with path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        missing = set(METRIC_COLUMNS).difference(reader.fieldnames or [])
        if missing:
            raise CasePackageError(
                f"Invalid roi_ri_metrics.csv: missing columns {sorted(missing)}",
                422,
            )
        rows = [_coerce_metric_row(row) for row in reader]

    return {
        "case_id": case_id,
        "status": "completed",
        "metrics": rows,
    }


def read_report(case_id: str, case_root: str | Path = CASE_ROOT) -> dict[str, Any]:
    path = _output_file(case_id, "report.json", case_root)
    return _read_required_json(path, "报告尚未生成。")


def _output_file(case_id: str, filename: str, case_root: str | Path) -> Path:
    if "/" in case_id or "\\" in case_id or case_id in {"", ".", ".."}:
        raise CasePackageError("Invalid case_id: path segments are not allowed.", 400)

    root = Path(case_root).resolve()
    case_dir = (root / case_id).resolve()
    if not _is_relative_to(case_dir, root):
        raise CasePackageError("Invalid case_id: path traversal is not allowed.", 400)
    if not case_dir.is_dir():
        raise CasePackageError(f"Case not found: {case_id}", 404)

    return case_dir / "output" / filename


def _read_required_json(path: Path, missing_message: str) -> dict[str, Any]:
    if not path.is_file():
        return {
            "case_id": path.parents[1].name,
            "status": "not_completed",
            "message": missing_message,
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CasePackageError(f"Invalid output JSON file: {path.name}", 422) from exc
    if not isinstance(data, dict):
        raise CasePackageError(f"Invalid output JSON root: {path.name}", 422)

    data.setdefault("case_id", path.parents[1].name)
    data["status"] = "completed"
    return data


def _coerce_metric_row(row: dict[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {column: row[column] for column in METRIC_COLUMNS}
    for column in ("ri_skewness", "ri_maximum"):
        try:
            result[column] = float(result[column])
        except (TypeError, ValueError) as exc:
            raise CasePackageError(
                f"Invalid numeric value in roi_ri_metrics.csv column {column}",
                422,
            ) from exc
    return result


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
