from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from backend.services.cases import (
    CasePackageError,
    case_detail,
    case_root_exists,
    list_cases,
    preview_image_path,
    simulate_super_resolution,
)
from backend.services.ri_analysis import RIAnalysisError, run_ri_analysis
from backend.services.results import read_metrics, read_report, read_ri_profiles


app = FastAPI(title="AD Edge Backend")


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "ad-edge-backend",
        "case_root_exists": case_root_exists(),
    }


@app.get("/api/cases")
def get_cases() -> dict:
    return {"cases": list_cases()}


@app.get("/api/cases/{case_id}")
def get_case(case_id: str) -> dict:
    try:
        return case_detail(case_id)
    except CasePackageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@app.get("/api/cases/{case_id}/preview/{image_name:path}")
def get_preview(case_id: str, image_name: str) -> FileResponse:
    try:
        image_path = preview_image_path(case_id, image_name)
    except CasePackageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return FileResponse(image_path)


@app.post("/api/cases/{case_id}/simulate-super-resolution")
def post_simulate_super_resolution(case_id: str) -> dict:
    try:
        return simulate_super_resolution(case_id)
    except CasePackageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@app.post("/api/cases/{case_id}/run-ri-analysis")
def post_run_ri_analysis(case_id: str) -> dict:
    try:
        case_detail(case_id)
        return run_ri_analysis(case_id)
    except CasePackageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except RIAnalysisError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/cases/{case_id}/ri-profiles")
def get_ri_profiles(case_id: str) -> dict:
    try:
        return read_ri_profiles(case_id)
    except CasePackageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@app.get("/api/cases/{case_id}/metrics")
def get_metrics(case_id: str) -> dict:
    try:
        return read_metrics(case_id)
    except CasePackageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@app.get("/api/cases/{case_id}/report")
def get_report(case_id: str) -> dict:
    try:
        return read_report(case_id)
    except CasePackageError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
