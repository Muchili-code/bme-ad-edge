#!/usr/bin/env python3
"""Validate mock case packages against the shared case-package contract."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import struct
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "data" / "cases"

REQUIRED_FILES = [
    "meta.json",
    "preview/lowres_dwi_slice.png",
    "preview/lowres_dwi_patch.png",
    "preview/t1_slice.png",
    "preview/t1_patch.png",
    "preview/sr_dwi_slice.png",
    "preview/sr_dwi_patch.png",
    "compute/sr_dwi_4d.nii.gz",
    "compute/grad.bvec",
    "compute/grad.bval",
    "compute/analysis_mask.nii.gz",
    "compute/surface_normals.json",
    "compute/depth_samples.json",
    "compute/roi_map.json",
    "compute/registration.json",
    "reference/roi_reference_ranges.csv",
    "reference/hc_ri_template.json",
]

META_FIELDS = [
    "case_id",
    "group",
    "display_name",
    "data_mode",
    "description",
    "scan_protocol",
    "processing_status",
]

PROCESSING_FIELDS = [
    "external_package_ready",
    "board_dti_done",
    "board_ri_done",
    "board_report_done",
]


class CaseValidationError(Exception):
    pass


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CaseValidationError(f"{path}: invalid JSON: {exc}") from exc


def read_nifti_dims(path: Path) -> tuple[int, ...]:
    try:
        with gzip.open(path, "rb") as f:
            header = f.read(348)
    except Exception as exc:
        raise CaseValidationError(f"{path}: cannot read NIfTI header: {exc}") from exc
    if len(header) != 348:
        raise CaseValidationError(f"{path}: NIfTI header is shorter than 348 bytes")
    sizeof_hdr = struct.unpack_from("<i", header, 0)[0]
    magic = header[344:348]
    if sizeof_hdr != 348 or magic not in (b"n+1\0", b"ni1\0"):
        raise CaseValidationError(f"{path}: not a valid little-endian NIfTI-1 image")
    dim = struct.unpack_from("<8h", header, 40)
    ndim = dim[0]
    if ndim < 1 or ndim > 7:
        raise CaseValidationError(f"{path}: invalid NIfTI dimension count {ndim}")
    dims = tuple(int(v) for v in dim[1 : ndim + 1])
    if any(v <= 0 for v in dims):
        raise CaseValidationError(f"{path}: invalid NIfTI dimensions {dims}")
    return dims


def parse_bvals(path: Path) -> list[float]:
    tokens = path.read_text(encoding="utf-8").split()
    if not tokens:
        raise CaseValidationError(f"{path}: no b-values found")
    try:
        return [float(token) for token in tokens]
    except ValueError as exc:
        raise CaseValidationError(f"{path}: b-values must be numeric") from exc


def parse_bvecs(path: Path) -> list[list[float]]:
    rows = [line.split() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 3:
        raise CaseValidationError(f"{path}: expected 3 rows in FSL bvec format, got {len(rows)}")
    try:
        parsed = [[float(token) for token in row] for row in rows]
    except ValueError as exc:
        raise CaseValidationError(f"{path}: b-vectors must be numeric") from exc
    counts = {len(row) for row in parsed}
    if len(counts) != 1:
        raise CaseValidationError(f"{path}: b-vector rows have inconsistent counts {sorted(counts)}")
    if not parsed[0]:
        raise CaseValidationError(f"{path}: no b-vectors found")
    return parsed


def assert_output_writable(path: Path) -> None:
    if not path.is_dir():
        raise CaseValidationError(f"{path}: output directory is missing")
    try:
        fd, probe = tempfile.mkstemp(prefix=".write_check_", dir=path)
        os.close(fd)
        Path(probe).unlink()
    except Exception as exc:
        raise CaseValidationError(f"{path}: output directory is not writable: {exc}") from exc


def validate_meta(case_dir: Path) -> None:
    meta = load_json(case_dir / "meta.json")
    if not isinstance(meta, dict):
        raise CaseValidationError("meta.json: root must be an object")
    for field in META_FIELDS:
        if field not in meta:
            raise CaseValidationError(f"meta.json: missing required field '{field}'")
    if meta["case_id"] != case_dir.name:
        raise CaseValidationError(f"meta.json: case_id '{meta['case_id']}' does not match directory '{case_dir.name}'")
    if meta["group"] not in {"HC", "MCI", "AD"}:
        raise CaseValidationError(f"meta.json: unsupported group '{meta['group']}'")
    status = meta["processing_status"]
    if not isinstance(status, dict):
        raise CaseValidationError("meta.json: processing_status must be an object")
    for field in PROCESSING_FIELDS:
        if field not in status:
            raise CaseValidationError(f"meta.json: processing_status missing '{field}'")
        if not isinstance(status[field], bool):
            raise CaseValidationError(f"meta.json: processing_status.{field} must be boolean")


def validate_geometry(case_dir: Path) -> None:
    depth = load_json(case_dir / "compute" / "depth_samples.json")
    normals = load_json(case_dir / "compute" / "surface_normals.json")
    roi_map = load_json(case_dir / "compute" / "roi_map.json")
    registration = load_json(case_dir / "compute" / "registration.json")

    if not isinstance(depth, dict) or "rois" not in depth or "depth_percent" not in depth:
        raise CaseValidationError("depth_samples.json: expected depth_percent and rois fields")
    expected_depths = [i * 10 for i in range(11)]
    if depth["depth_percent"] != expected_depths:
        raise CaseValidationError("depth_samples.json: depth_percent must be 0..100 in 10% steps")
    if not isinstance(depth["rois"], list) or not depth["rois"]:
        raise CaseValidationError("depth_samples.json: rois must be a non-empty list")
    for roi in depth["rois"]:
        if not isinstance(roi, dict) or "roi_id" not in roi or "samples" not in roi:
            raise CaseValidationError("depth_samples.json: each ROI needs roi_id and samples")
        samples = roi["samples"]
        if not isinstance(samples, list) or len(samples) != 11:
            raise CaseValidationError(f"depth_samples.json: {roi.get('roi_id', '<unknown>')} must have 11 depth samples")
        depths = [sample.get("depth_percent") for sample in samples if isinstance(sample, dict)]
        if depths != expected_depths:
            raise CaseValidationError(f"depth_samples.json: {roi['roi_id']} depths must be 0..100 in order")
        for sample in samples:
            voxel = sample.get("voxel")
            if not isinstance(voxel, list) or len(voxel) != 3:
                raise CaseValidationError(f"depth_samples.json: {roi['roi_id']} sample voxel must have 3 coordinates")

    if not isinstance(normals, dict) or "normals" not in normals:
        raise CaseValidationError("surface_normals.json: missing normals field")
    if len(normals["normals"]) != len(depth["rois"]):
        raise CaseValidationError("surface_normals.json: ROI count does not match depth_samples.json")
    for roi in normals["normals"]:
        samples = roi.get("samples")
        if not isinstance(samples, list) or len(samples) != 11:
            raise CaseValidationError(f"surface_normals.json: {roi.get('roi_id', '<unknown>')} must have 11 normals")
        for sample in samples:
            normal = sample.get("normal")
            if not isinstance(normal, list) or len(normal) != 3:
                raise CaseValidationError(f"surface_normals.json: {roi.get('roi_id', '<unknown>')} normal must have 3 values")

    if not isinstance(roi_map, dict) or "rois" not in roi_map:
        raise CaseValidationError("roi_map.json: missing rois field")
    if roi_map.get("roi_count") != len(roi_map["rois"]):
        raise CaseValidationError("roi_map.json: roi_count does not match rois length")
    if len(roi_map["rois"]) != len(depth["rois"]):
        raise CaseValidationError("roi_map.json: ROI count does not match depth_samples.json")
    for roi in roi_map["rois"]:
        for field in ["roi_id", "roi_name", "network", "hemisphere", "label"]:
            if field not in roi:
                raise CaseValidationError(f"roi_map.json: ROI entry missing '{field}'")

    if not isinstance(registration, dict) or "space" not in registration or "affine" not in registration:
        raise CaseValidationError("registration.json: expected space and affine fields")


def validate_case(case_dir: Path) -> list[str]:
    errors = []
    try:
        if not case_dir.is_dir():
            raise CaseValidationError(f"{case_dir}: case directory does not exist")
        for rel in REQUIRED_FILES:
            if not (case_dir / rel).is_file():
                raise CaseValidationError(f"{case_dir}: missing required file {rel}")
        validate_meta(case_dir)

        dwi_dims = read_nifti_dims(case_dir / "compute" / "sr_dwi_4d.nii.gz")
        mask_dims = read_nifti_dims(case_dir / "compute" / "analysis_mask.nii.gz")
        if len(dwi_dims) != 4:
            raise CaseValidationError(f"sr_dwi_4d.nii.gz: expected 4D image, got dims {dwi_dims}")
        if len(mask_dims) != 3:
            raise CaseValidationError(f"analysis_mask.nii.gz: expected 3D image, got dims {mask_dims}")
        if dwi_dims[:3] != mask_dims:
            raise CaseValidationError(f"analysis_mask.nii.gz: dims {mask_dims} do not match DWI spatial dims {dwi_dims[:3]}")

        bvals = parse_bvals(case_dir / "compute" / "grad.bval")
        bvecs = parse_bvecs(case_dir / "compute" / "grad.bvec")
        volume_count = dwi_dims[3]
        if len(bvals) != volume_count:
            raise CaseValidationError(f"grad.bval: {len(bvals)} b-values do not match DWI volumes {volume_count}")
        if len(bvecs[0]) != volume_count:
            raise CaseValidationError(f"grad.bvec: {len(bvecs[0])} b-vectors do not match DWI volumes {volume_count}")
        if bvals[0] != 0:
            raise CaseValidationError("grad.bval: first volume should be b0 with b-value 0")

        validate_geometry(case_dir)
        assert_output_writable(case_dir / "output")
    except CaseValidationError as exc:
        errors.append(str(exc))
    return errors


def discover_cases(case_root: Path) -> list[Path]:
    return sorted(path for path in case_root.iterdir() if path.is_dir() and path.name.startswith("case_"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate one or more case packages.")
    parser.add_argument("cases", nargs="*", type=Path, help="Case directories. Defaults to all data/cases/case_*.")
    parser.add_argument("--case-root", type=Path, default=CASE_ROOT, help="Case root used when no case is given.")
    args = parser.parse_args()

    cases = args.cases or discover_cases(args.case_root)
    if not cases:
        print(f"ERROR: no cases found under {args.case_root}")
        return 1

    failed = False
    for case_dir in cases:
        errors = validate_case(case_dir)
        if errors:
            failed = True
            print(f"FAIL {case_dir}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK {case_dir}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
