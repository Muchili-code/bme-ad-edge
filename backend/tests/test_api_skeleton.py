from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)
CASE_ID = "case_HC_001"
CASE_DIR = Path("data/cases") / CASE_ID


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "ad-edge-backend"


def test_cases_list_contains_mock_cases() -> None:
    response = client.get("/api/cases")

    assert response.status_code == 200
    case_ids = {case["case_id"] for case in response.json()["cases"]}
    assert {"case_HC_001", "case_MCI_001", "case_AD_001"}.issubset(case_ids)


def test_case_detail_reports_integrity_and_preview_urls() -> None:
    response = client.get(f"/api/cases/{CASE_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == CASE_ID
    assert body["package_valid"] is True
    assert body["file_integrity"]["missing_files"] == []
    assert body["preview_images"]["sr_dwi_patch.png"] == (
        f"/api/cases/{CASE_ID}/preview/sr_dwi_patch.png"
    )
    assert isinstance(body["output_status"]["ri_analysis_done"], bool)
    assert "report.json" in body["output_status"]["files"]


def test_case_detail_missing_case_is_clear_404() -> None:
    response = client.get("/api/cases/no_such_case")

    assert response.status_code == 404
    assert "Case not found" in response.json()["detail"]


def test_preview_serves_png_and_blocks_traversal() -> None:
    response = client.get(f"/api/cases/{CASE_ID}/preview/sr_dwi_patch.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    traversal = client.get(f"/api/cases/{CASE_ID}/preview/..%2Fmeta.json")
    assert traversal.status_code == 400
    assert "path segments" in traversal.json()["detail"]


def test_preview_rejects_non_image_name() -> None:
    response = client.get(f"/api/cases/{CASE_ID}/preview/meta.json")

    assert response.status_code == 400
    assert "PNG/JPEG" in response.json()["detail"]


def test_simulate_super_resolution_is_visual_demo_only() -> None:
    response = client.post(f"/api/cases/{CASE_ID}/simulate-super-resolution")

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == CASE_ID
    assert body["mode"] == "visual_demo_only"
    assert body["result_preview"] == f"/api/cases/{CASE_ID}/preview/sr_dwi_patch.png"


def test_run_ri_analysis_generates_output_and_result_apis_read_it() -> None:
    response = client.post(f"/api/cases/{CASE_ID}/run-ri-analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == CASE_ID
    assert body["status"] == "completed"
    assert body["generated_files"] == [
        "output/ri_depth_profiles.json",
        "output/roi_ri_metrics.csv",
        "output/abnormal_regions.json",
        "output/sampled_vectors.json",
        "output/report.json",
    ]

    profiles = client.get(f"/api/cases/{CASE_ID}/ri-profiles")
    assert profiles.status_code == 200
    profiles_body = profiles.json()
    assert profiles_body["status"] == "completed"
    assert profiles_body["case_id"] == CASE_ID
    assert len(profiles_body["profiles"]) == 6

    metrics = client.get(f"/api/cases/{CASE_ID}/metrics")
    assert metrics.status_code == 200
    metrics_body = metrics.json()
    assert metrics_body["status"] == "completed"
    assert metrics_body["case_id"] == CASE_ID
    assert len(metrics_body["metrics"]) == 6
    assert isinstance(metrics_body["metrics"][0]["ri_skewness"], float)

    report = client.get(f"/api/cases/{CASE_ID}/report")
    assert report.status_code == 200
    report_body = report.json()
    assert report_body["status"] == "completed"
    assert report_body["case_id"] == CASE_ID
    assert report_body["key_findings"]


def test_run_ri_analysis_fails_when_dwi_missing() -> None:
    dwi_path = CASE_DIR / "compute" / "sr_dwi_4d.nii.gz"
    backup_path = dwi_path.with_name("sr_dwi_4d.nii.gz.api_pytest_tmp")
    dwi_path.rename(backup_path)
    try:
        response = client.post(f"/api/cases/{CASE_ID}/run-ri-analysis")
    finally:
        backup_path.rename(dwi_path)

    assert response.status_code == 422
    assert "sr_dwi_4d.nii.gz" in response.json()["detail"]


def test_report_missing_file_returns_not_completed_without_hardcoded_findings() -> None:
    client.post(f"/api/cases/{CASE_ID}/run-ri-analysis")
    report_path = CASE_DIR / "output" / "report.json"
    backup_path = report_path.with_name("report.json.api_pytest_tmp")
    report_path.rename(backup_path)
    try:
        response = client.get(f"/api/cases/{CASE_ID}/report")
    finally:
        backup_path.rename(report_path)

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "case_id": CASE_ID,
        "status": "not_completed",
        "message": "报告尚未生成。",
    }


def test_profiles_and_metrics_missing_files_return_not_completed() -> None:
    client.post(f"/api/cases/{CASE_ID}/run-ri-analysis")
    moved_paths = []
    for name in ["ri_depth_profiles.json", "roi_ri_metrics.csv"]:
        path = CASE_DIR / "output" / name
        backup_path = path.with_name(f"{name}.api_pytest_tmp")
        path.rename(backup_path)
        moved_paths.append((path, backup_path))

    try:
        profiles = client.get(f"/api/cases/{CASE_ID}/ri-profiles")
        metrics = client.get(f"/api/cases/{CASE_ID}/metrics")
    finally:
        for path, backup_path in moved_paths:
            backup_path.rename(path)

    assert profiles.status_code == 200
    assert profiles.json()["status"] == "not_completed"
    assert "not completed" in profiles.json()["message"]
    assert "profiles" not in profiles.json()

    assert metrics.status_code == 200
    assert metrics.json() == {
        "case_id": CASE_ID,
        "status": "not_completed",
        "message": "RI metrics are not completed yet.",
        "metrics": [],
    }
