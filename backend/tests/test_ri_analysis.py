from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from backend.services.ri_analysis import RIAnalysisError, run_ri_analysis


CASE_ID = "case_HC_001"
CASE_DIR = Path("data/cases") / CASE_ID


def test_run_ri_analysis_generates_contract_files() -> None:
    result = run_ri_analysis(CASE_ID)

    assert result["case_id"] == CASE_ID
    assert result["status"] == "completed"
    assert result["generated_files"] == [
        "output/ri_depth_profiles.json",
        "output/roi_ri_metrics.csv",
        "output/abnormal_regions.json",
        "output/sampled_vectors.json",
        "output/report.json",
    ]

    output_dir = CASE_DIR / "output"
    for name in [
        "ri_depth_profiles.json",
        "roi_ri_metrics.csv",
        "abnormal_regions.json",
        "sampled_vectors.json",
        "report.json",
    ]:
        assert (output_dir / name).exists()

    profiles = json.loads((output_dir / "ri_depth_profiles.json").read_text(encoding="utf-8"))
    assert profiles["case_id"] == CASE_ID
    assert len(profiles["profiles"]) == 6
    assert all(len(profile["ri_values"]) == 11 for profile in profiles["profiles"])

    sampled = json.loads((output_dir / "sampled_vectors.json").read_text(encoding="utf-8"))
    assert len(sampled["samples"]) == 66
    assert {"sample_id", "roi_id", "depth_percent", "v1", "normal", "ri"} <= set(
        sampled["samples"][0]
    )

    report = json.loads((output_dir / "report.json").read_text(encoding="utf-8"))
    assert report["case_id"] == CASE_ID
    assert report["key_findings"]


def test_run_ri_analysis_changes_when_dwi_changes() -> None:
    dwi_path = CASE_DIR / "compute" / "sr_dwi_4d.nii.gz"
    original = dwi_path.read_bytes()
    try:
        run_ri_analysis(CASE_ID)
        before = json.loads(
            (CASE_DIR / "output" / "ri_depth_profiles.json").read_text(encoding="utf-8")
        )

        img = nib.load(str(dwi_path))
        data = np.asarray(img.get_fdata(dtype=np.float32), dtype=np.float32)
        data[8, 9, 6, 1:] *= np.linspace(0.75, 1.25, data.shape[3] - 1, dtype=np.float32)
        nib.save(nib.Nifti1Image(data, img.affine, img.header), str(dwi_path))

        run_ri_analysis(CASE_ID)
        after = json.loads(
            (CASE_DIR / "output" / "ri_depth_profiles.json").read_text(encoding="utf-8")
        )
        assert before != after
    finally:
        dwi_path.write_bytes(original)
        run_ri_analysis(CASE_ID)


def test_run_ri_analysis_fails_when_dwi_missing() -> None:
    dwi_path = CASE_DIR / "compute" / "sr_dwi_4d.nii.gz"
    backup_path = dwi_path.with_suffix(dwi_path.suffix + ".pytest_tmp")
    dwi_path.rename(backup_path)
    try:
        with pytest.raises(RIAnalysisError, match="sr_dwi_4d.nii.gz"):
            run_ri_analysis(CASE_ID)
    finally:
        backup_path.rename(dwi_path)
