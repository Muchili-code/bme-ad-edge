#!/usr/bin/env python3
"""Generate small, computable mock case packages for the edge demo."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import random
import shutil
import struct
from array import array
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "data" / "cases"
SHAPE = (32, 32, 16)
BVAL = 1000.0
DEPTH_PERCENT = [i * 10 for i in range(11)]

GRADIENTS = [
    (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
    (0.70710678, 0.70710678, 0.0),
    (0.70710678, 0.0, 0.70710678),
    (0.0, 0.70710678, 0.70710678),
    (0.57735027, 0.57735027, 0.57735027),
    (-0.70710678, 0.70710678, 0.0),
    (0.70710678, 0.0, -0.70710678),
    (0.0, -0.70710678, 0.70710678),
    (-0.57735027, 0.57735027, 0.57735027),
    (0.57735027, -0.57735027, 0.57735027),
]

ROIS = [
    ("ROI_001", "Superior Parietal", "dorsal_attention", "L", (8, 9, 6), (0.18, 0.16, 0.9708)),
    ("ROI_002", "Precuneus", "default_mode", "R", (23, 10, 7), (-0.12, 0.20, 0.9724)),
    ("ROI_003", "Posterior Cingulate", "default_mode", "L", (12, 21, 8), (0.08, -0.22, 0.9722)),
    ("ROI_004", "Inferior Parietal", "frontoparietal", "R", (21, 22, 7), (-0.23, -0.12, 0.9658)),
    ("ROI_005", "Middle Temporal", "temporal_memory", "L", (9, 24, 5), (0.28, -0.10, 0.9548)),
    ("ROI_006", "Medial Frontal", "executive_control", "R", (24, 7, 9), (-0.18, 0.26, 0.9487)),
]

CASE_CONFIG = {
    "HC": {
        "case_id": "case_HC_001",
        "display_name": "健康对照示例",
        "peak_scale": [1.00, 0.98, 1.02, 0.99, 1.01, 1.00],
        "skew": [0.00, 0.02, -0.02, 0.00, 0.01, -0.01],
        "seed": 101,
    },
    "MCI": {
        "case_id": "case_MCI_001",
        "display_name": "轻度认知障碍示例",
        "peak_scale": [0.92, 0.86, 0.88, 0.90, 0.89, 0.91],
        "skew": [0.04, 0.10, 0.08, 0.03, 0.07, 0.05],
        "seed": 202,
    },
    "AD": {
        "case_id": "case_AD_001",
        "display_name": "阿尔茨海默病示例",
        "peak_scale": [0.80, 0.64, 0.60, 0.66, 0.58, 0.74],
        "skew": [0.10, 0.26, 0.30, -0.18, 0.24, -0.12],
        "seed": 303,
    },
}


def normalize(vector: Iterable[float]) -> tuple[float, float, float]:
    x, y, z = vector
    length = math.sqrt(x * x + y * y + z * z)
    return (x / length, y / length, z / length)


def ri_profile(scale: float, skew: float) -> list[float]:
    values = []
    for depth in DEPTH_PERCENT:
        t = depth / 100.0
        dome = 0.48 + 0.36 * math.sin(math.pi * t)
        shoulder = 0.035 * math.cos(2.0 * math.pi * t)
        skew_term = skew * (t - 0.50) * (0.35 + math.sin(math.pi * t))
        values.append(max(0.25, min(0.92, scale * dome + shoulder + skew_term)))
    return values


def tangent_for(normal: tuple[float, float, float]) -> tuple[float, float, float]:
    nx, ny, nz = normal
    seed = (0.0, 0.0, 1.0) if abs(nz) < 0.9 else (0.0, 1.0, 0.0)
    sx, sy, sz = seed
    dot = sx * nx + sy * ny + sz * nz
    return normalize((sx - dot * nx, sy - dot * ny, sz - dot * nz))


def direction_from_ri(
    normal: tuple[float, float, float],
    tangent: tuple[float, float, float],
    ri: float,
) -> tuple[float, float, float]:
    ri = max(-0.98, min(0.98, ri))
    side = math.sqrt(max(0.0, 1.0 - ri * ri))
    return normalize(tuple(ri * n + side * t for n, t in zip(normal, tangent)))


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_nifti(path: Path, dims: tuple[int, ...], datatype: int, bitpix: int, data: array) -> None:
    header = bytearray(348)
    struct.pack_into("<i", header, 0, 348)
    dim = [len(dims), *dims, *([1] * (7 - len(dims)))]
    struct.pack_into("<8h", header, 40, *dim)
    struct.pack_into("<h", header, 70, datatype)
    struct.pack_into("<h", header, 72, bitpix)
    struct.pack_into("<8f", header, 76, 0.0, 1.5, 1.5, 1.5, 1.0, 0.0, 0.0, 0.0)
    struct.pack_into("<f", header, 108, 352.0)
    struct.pack_into("<h", header, 254, 1)
    struct.pack_into("<4f", header, 280, 0.0, 1.5, 0.0, 0.0)
    struct.pack_into("<4f", header, 296, 0.0, 0.0, 1.5, 0.0)
    struct.pack_into("<4f", header, 312, 0.0, 0.0, 0.0, 1.5)
    header[344:348] = b"n+1\0"
    with gzip.open(path, "wb") as f:
        f.write(header)
        f.write(b"\0\0\0\0")
        f.write(data.tobytes())


def make_preview(path: Path, title: str, group: str, mode: str, seed: int) -> None:
    rng = random.Random(seed)
    img = Image.new("L", (160, 120), 18)
    draw = ImageDraw.Draw(img)
    cx, cy = 80 + rng.randint(-4, 4), 60 + rng.randint(-3, 3)
    rx, ry = (48, 38) if "patch" not in mode else (34, 28)
    base = {"HC": 108, "MCI": 92, "AD": 78}[group]
    if mode.startswith("sr"):
        base += 25
    elif mode.startswith("t1"):
        base += 45
    for y in range(img.height):
        for x in range(img.width):
            dx = (x - cx) / rx
            dy = (y - cy) / ry
            radius = dx * dx + dy * dy
            if radius < 1.0:
                val = int(base + 72 * (1.0 - radius) + 12 * math.sin((x + y) / 11.0))
                if mode.startswith("lowres"):
                    val = (val // 18) * 18
                img.putpixel((x, y), max(0, min(255, val)))
    draw.text((8, 8), title, fill=230)
    img.convert("RGB").save(path)


def build_geometry(group: str) -> tuple[dict, dict, dict, list[list[float]]]:
    cfg = CASE_CONFIG[group]
    depth_samples = {"depth_percent": DEPTH_PERCENT, "rois": []}
    surface_normals = {"space": "sr_dwi_voxel", "normals": []}
    roi_map = {"roi_count": len(ROIS), "rois": []}
    profiles = []
    for idx, (roi_id, roi_name, network, hemisphere, center, normal_raw) in enumerate(ROIS):
        normal = normalize(normal_raw)
        profile = ri_profile(cfg["peak_scale"][idx], cfg["skew"][idx])
        profiles.append(profile)
        samples = []
        normals = []
        for depth, ri in zip(DEPTH_PERCENT, profile):
            offset = (depth - 50) / 25.0
            voxel = [round(center[i] + offset * normal[i], 3) for i in range(3)]
            samples.append({"depth_percent": depth, "voxel": voxel, "expected_mock_ri": round(ri, 4)})
            normals.append({"depth_percent": depth, "normal": [round(v, 6) for v in normal]})
        depth_samples["rois"].append({"roi_id": roi_id, "roi_name": roi_name, "samples": samples})
        surface_normals["normals"].append({"roi_id": roi_id, "roi_name": roi_name, "samples": normals})
        roi_map["rois"].append(
            {
                "roi_id": roi_id,
                "roi_name": roi_name,
                "network": network,
                "hemisphere": hemisphere,
                "label": idx + 1,
                "center_voxel": list(center),
            }
        )
    return surface_normals, depth_samples, roi_map, profiles


def build_images(case_dir: Path, group: str, depth_samples: dict, profiles: list[list[float]]) -> None:
    rng = random.Random(CASE_CONFIG[group]["seed"])
    sx, sy, sz = SHAPE
    voxels = sx * sy * sz
    mask = array("B", [0]) * voxels
    field = {}

    for roi_idx, roi in enumerate(ROIS):
        normal = normalize(roi[5])
        tangent = tangent_for(normal)
        for sample, ri in zip(depth_samples["rois"][roi_idx]["samples"], profiles[roi_idx]):
            vx, vy, vz = [int(round(v)) for v in sample["voxel"]]
            v1 = direction_from_ri(normal, tangent, ri)
            for dz in range(-1, 2):
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        x, y, z = vx + dx, vy + dy, vz + dz
                        if 0 <= x < sx and 0 <= y < sy and 0 <= z < sz:
                            index = x + sx * (y + sy * z)
                            mask[index] = 1
                            field[(x, y, z)] = (roi_idx, v1, ri)

    dwi = array("f")
    for t, grad in enumerate(GRADIENTS):
        bval = 0.0 if t == 0 else BVAL
        gx, gy, gz = grad
        for z in range(sz):
            for y in range(sy):
                for x in range(sx):
                    index = x + sx * (y + sy * z)
                    s0 = 920.0 + 35.0 * math.sin(x / 4.0) + 18.0 * math.cos(y / 5.0)
                    if mask[index] == 0:
                        signal = 18.0 + 2.5 * math.sin((x + y + z + t) / 4.0)
                    elif t == 0:
                        signal = s0
                    else:
                        roi_idx, v1, ri = field[(x, y, z)]
                        axial = (gx * v1[0] + gy * v1[1] + gz * v1[2]) ** 2
                        md = 0.00078 + 0.00003 * roi_idx
                        anis = 0.00074 * max(0.25, ri)
                        signal = s0 * math.exp(-bval * (md + anis * axial)) + rng.uniform(-2.0, 2.0)
                    dwi.append(float(max(1.0, signal)))

    compute = case_dir / "compute"
    write_nifti(compute / "sr_dwi_4d.nii.gz", (*SHAPE, len(GRADIENTS)), 16, 32, dwi)
    write_nifti(compute / "analysis_mask.nii.gz", SHAPE, 2, 8, mask)


def write_gradients(case_dir: Path) -> None:
    compute = case_dir / "compute"
    bvals = ["0" if i == 0 else str(int(BVAL)) for i in range(len(GRADIENTS))]
    (compute / "grad.bval").write_text(" ".join(bvals) + "\n", encoding="utf-8")
    rows = [" ".join(f"{g[axis]:.8f}" for g in GRADIENTS) for axis in range(3)]
    (compute / "grad.bvec").write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_reference(case_dir: Path) -> None:
    reference = case_dir / "reference"
    with (reference / "roi_reference_ranges.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "roi_id",
                "roi_name",
                "network",
                "hemisphere",
                "ri_maximum_low",
                "ri_maximum_high",
                "ri_skewness_low",
                "ri_skewness_high",
            ],
        )
        writer.writeheader()
        for roi_id, roi_name, network, hemisphere, *_ in ROIS:
            writer.writerow(
                {
                    "roi_id": roi_id,
                    "roi_name": roi_name,
                    "network": network,
                    "hemisphere": hemisphere,
                    "ri_maximum_low": "0.76",
                    "ri_maximum_high": "0.91",
                    "ri_skewness_low": "-0.35",
                    "ri_skewness_high": "0.35",
                }
            )

    profiles = []
    for roi_id, roi_name, *_ in ROIS:
        profiles.append(
            {
                "roi_id": roi_id,
                "roi_name": roi_name,
                "depth_percent": DEPTH_PERCENT,
                "ri_values": [round(v, 4) for v in ri_profile(1.0, 0.0)],
            }
        )
    write_json(reference / "hc_ri_template.json", {"template_group": "HC", "profiles": profiles})


def write_case(group: str, case_root: Path) -> Path:
    cfg = CASE_CONFIG[group]
    case_dir = case_root / cfg["case_id"]
    if case_dir.exists():
        shutil.rmtree(case_dir)
    for subdir in ["preview", "compute", "reference", "output"]:
        (case_dir / subdir).mkdir(parents=True, exist_ok=True)

    write_json(
        case_dir / "meta.json",
        {
            "case_id": cfg["case_id"],
            "group": group,
            "display_name": cfg["display_name"],
            "data_mode": "mock",
            "description": "科研数据未到前使用的小型可计算模拟病例",
            "scan_protocol": "mock_dMRI_b1000_12dir",
            "processing_status": {
                "external_package_ready": True,
                "board_dti_done": False,
                "board_ri_done": False,
                "board_report_done": False,
            },
        },
    )

    preview_specs = [
        ("lowres_dwi_slice.png", "lowres slice", "lowres"),
        ("lowres_dwi_patch.png", "lowres patch", "lowres_patch"),
        ("t1_slice.png", "T1 slice", "t1"),
        ("t1_patch.png", "T1 patch", "t1_patch"),
        ("sr_dwi_slice.png", "SR dMRI slice", "sr"),
        ("sr_dwi_patch.png", "SR dMRI patch", "sr_patch"),
    ]
    for i, (filename, title, mode) in enumerate(preview_specs):
        make_preview(case_dir / "preview" / filename, title, group, mode, cfg["seed"] + i)

    surface_normals, depth_samples, roi_map, profiles = build_geometry(group)
    compute = case_dir / "compute"
    write_json(compute / "surface_normals.json", surface_normals)
    write_json(compute / "depth_samples.json", depth_samples)
    write_json(compute / "roi_map.json", roi_map)
    write_json(
        compute / "registration.json",
        {
            "space": "mock_sr_dwi",
            "voxel_size_mm": [1.5, 1.5, 1.5],
            "affine": [[1.5, 0, 0, 0], [0, 1.5, 0, 0], [0, 0, 1.5, 0], [0, 0, 0, 1]],
            "note": "Mock package uses pre-aligned sampling coordinates; edge demo does not run registration.",
        },
    )
    write_gradients(case_dir)
    write_reference(case_dir)
    build_images(case_dir, group, depth_samples, profiles)
    return case_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate HC/MCI/AD mock case packages.")
    parser.add_argument("--case-root", type=Path, default=CASE_ROOT, help="Output case root directory.")
    args = parser.parse_args()

    args.case_root.mkdir(parents=True, exist_ok=True)
    created = [write_case(group, args.case_root) for group in ["HC", "MCI", "AD"]]
    for path in created:
        print(f"generated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
