#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CASE_ID="${ACCEPTANCE_CASE_ID:-case_HC_001}"
BACKEND_PORT="${ACCEPTANCE_BACKEND_PORT:-18080}"
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}"
BACKEND_PID=""
TMP_DIR="$(mktemp -d /tmp/ad-edge-acceptance.XXXXXX)"
FAILURES=0

log() {
  printf '\n[acceptance] %s\n' "$1"
}

pass() {
  printf '[PASS] %s\n' "$1"
}

fail() {
  printf '[FAIL] %s\n' "$1"
  FAILURES=$((FAILURES + 1))
}

warn() {
  printf '[WARN] %s\n' "$1"
}

cleanup() {
  set +e
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null
    wait "$BACKEND_PID" 2>/dev/null
  fi

  if [ -f "$TMP_DIR/sr_dwi_4d.nii.gz" ]; then
    mkdir -p "data/cases/${CASE_ID}/compute"
    cp "$TMP_DIR/sr_dwi_4d.nii.gz" "data/cases/${CASE_ID}/compute/sr_dwi_4d.nii.gz"
  fi
  if [ -d "$TMP_DIR/output_backup" ]; then
    rm -rf "data/cases/${CASE_ID}/output"
    mkdir -p "data/cases/${CASE_ID}/output"
    cp -a "$TMP_DIR/output_backup/." "data/cases/${CASE_ID}/output/"
  fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

run_check() {
  local name="$1"
  shift
  if "$@"; then
    pass "$name"
  else
    fail "$name"
  fi
}

require_wsl_root() {
  [ "$(pwd)" = "/home/hp/ad-edge-demo" ] || return 1
  [ -f "README.md" ] && [ -d "backend" ] && [ -d "frontend" ]
}

check_start_demo_contract() {
  [ -x "./start_demo.sh" ] || return 1
  timeout 35s ./start_demo.sh >"$TMP_DIR/start_demo.log" 2>&1 &
  local pid=$!
  local ok=1
  for _ in $(seq 1 25); do
    if curl -fsS "http://127.0.0.1:8000/api/health" >"$TMP_DIR/start_demo_health.json" 2>/dev/null; then
      ok=0
      break
    fi
    sleep 1
  done
  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  [ "$ok" -eq 0 ] || return 1
  .venv/bin/python - "$TMP_DIR/start_demo_health.json" <<'PY'
import json
import sys
data = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert data.get("status") == "ok", data
PY
}

start_backend() {
  if [ ! -x ".venv/bin/python" ]; then
    fail "backend virtualenv exists at .venv/bin/python"
    return 1
  fi
  .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port "$BACKEND_PORT" \
    >"$TMP_DIR/backend.log" 2>&1 &
  BACKEND_PID=$!
  for _ in $(seq 1 25); do
    if curl -fsS "${BACKEND_URL}/api/health" >"$TMP_DIR/health.json" 2>/dev/null; then
      return 0
    fi
    sleep 1
  done
  return 1
}

health_returns_ok() {
  curl -fsS "${BACKEND_URL}/api/health" >"$TMP_DIR/health.json" || return 1
  .venv/bin/python - "$TMP_DIR/health.json" <<'PY'
import json
import sys
data = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert data.get("status") == "ok", data
assert data.get("case_root_exists") is True, data
PY
}

run_ri_analysis() {
  local out="$1"
  curl -fsS -X POST "${BACKEND_URL}/api/cases/${CASE_ID}/run-ri-analysis" >"$out"
}

check_report_completed() {
  curl -fsS "${BACKEND_URL}/api/cases/${CASE_ID}/report" >"$TMP_DIR/report.json" || return 1
  .venv/bin/python - "$TMP_DIR/report.json" <<'PY'
import json
import sys
data = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert data.get("status") == "completed", data
assert "确诊 AD" not in json.dumps(data, ensure_ascii=False), data
PY
}

check_frontend_source_has_backend_badge() {
  grep -q "BackendBadge" frontend/src/App.tsx &&
    grep -q "后端未连接" frontend/src/App.tsx &&
    grep -q "报告页不会展示缓存或假报告" frontend/src/App.tsx
}

check_offline_runtime_docs() {
  grep -q "断网" docs/acceptance_tests.md &&
    grep -q "不需要访问远端 API" docs/acceptance_tests.md &&
    grep -q "已安装好依赖" docs/acceptance_tests.md
}

check_no_remote_api_reference() {
  ! grep -RInE 'https?://(api|openai|huggingface|github|pypi|npmjs)' backend frontend/src scripts data/cases >/tmp/ad-edge-remote-grep.txt 2>/dev/null
}

check_backend_stopped_blocks_api() {
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null
    wait "$BACKEND_PID" 2>/dev/null
    BACKEND_PID=""
  fi
  ! curl -fsS "${BACKEND_URL}/api/cases/${CASE_ID}/report" >/dev/null 2>&1
}

check_missing_dwi_fails() {
  local dwi="data/cases/${CASE_ID}/compute/sr_dwi_4d.nii.gz"
  [ -f "$dwi" ] || return 1
  [ -f "$TMP_DIR/sr_dwi_4d.nii.gz" ] || cp "$dwi" "$TMP_DIR/sr_dwi_4d.nii.gz"
  mv "$dwi" "${dwi}.acceptance.bak"
  local code
  code="$(curl -sS -o "$TMP_DIR/missing_dwi.json" -w "%{http_code}" -X POST "${BACKEND_URL}/api/cases/${CASE_ID}/run-ri-analysis" || true)"
  mv "${dwi}.acceptance.bak" "$dwi"
  [ "$code" != "200" ]
}

check_missing_report_has_no_hardcoded_conclusion() {
  local report="data/cases/${CASE_ID}/output/report.json"
  [ -f "$report" ] || run_ri_analysis "$TMP_DIR/run_before_missing_report.json" || return 1
  mkdir -p "$TMP_DIR/output_backup"
  cp -a "data/cases/${CASE_ID}/output/." "$TMP_DIR/output_backup/"
  mv "$report" "${report}.acceptance.bak"
  curl -fsS "${BACKEND_URL}/api/cases/${CASE_ID}/report" >"$TMP_DIR/missing_report_response.json" || {
    mv "${report}.acceptance.bak" "$report"
    return 1
  }
  mv "${report}.acceptance.bak" "$report"
  .venv/bin/python - "$TMP_DIR/missing_report_response.json" <<'PY'
import json
import sys
data = json.loads(open(sys.argv[1], encoding="utf-8").read())
text = json.dumps(data, ensure_ascii=False)
assert data.get("status") == "not_completed", data
for forbidden in ["确诊 AD", "边缘端 RI 皮层柱辅助分析报告", "风险分布", "key_findings"]:
    assert forbidden not in text, text
PY
}

check_modified_dwi_changes_output() {
  local dwi="data/cases/${CASE_ID}/compute/sr_dwi_4d.nii.gz"
  [ -f "$dwi" ] || return 1
  [ -f "$TMP_DIR/sr_dwi_4d.nii.gz" ] || cp "$dwi" "$TMP_DIR/sr_dwi_4d.nii.gz"
  mkdir -p "$TMP_DIR/output_backup"
  cp -a "data/cases/${CASE_ID}/output/." "$TMP_DIR/output_backup/" 2>/dev/null || true

  run_ri_analysis "$TMP_DIR/run_baseline.json" || return 1
  sha256sum "data/cases/${CASE_ID}/output/ri_depth_profiles.json" >"$TMP_DIR/baseline.sha"

  .venv/bin/python - "$dwi" <<'PY'
import sys
import nibabel as nib
import numpy as np

path = sys.argv[1]
img = nib.load(path)
data = np.asarray(img.get_fdata(dtype=np.float32), dtype=np.float32)
if data.ndim != 4 or data.shape[3] < 7:
    raise SystemExit("dMRI file must be 4D with at least 7 volumes")

x = np.linspace(0.98, 1.04, data.shape[0], dtype=np.float32)[:, None, None]
for vol in range(1, data.shape[3]):
    factor = np.float32(1.0 + ((vol % 5) - 2) * 0.035)
    data[..., vol] = np.maximum(data[..., vol] * factor * x, 1e-6)
nib.save(nib.Nifti1Image(data, img.affine, img.header), path)
PY

  run_ri_analysis "$TMP_DIR/run_modified.json" || return 1
  sha256sum "data/cases/${CASE_ID}/output/ri_depth_profiles.json" >"$TMP_DIR/modified.sha"
  ! cmp -s "$TMP_DIR/baseline.sha" "$TMP_DIR/modified.sha"
}

check_git_status_and_ignored_dirs() {
  git status --short >"$TMP_DIR/git_status.txt" || return 1
  local tracked
  tracked="$(git ls-files .venv node_modules frontend/node_modules dist build frontend/dist 2>/dev/null)"
  [ -z "$tracked" ] || {
    printf '%s\n' "$tracked" >"$TMP_DIR/tracked_generated_dirs.txt"
    return 1
  }
}

check_copy_boundaries() {
  .venv/bin/python - <<'PY'
from pathlib import Path

roots = [Path("frontend/src"), Path("backend"), Path("README.md"), Path("docs"), Path("data/cases")]
forbidden = [
    "边缘端真实运行完整 DisC-Diff",
    "边缘端实时完成 FreeSurfer",
    "边缘端实时完成全脑配准",
    "确诊 AD",
]
allowed_markers = ("不写", "不能出现", "禁止", "不会", "不输出")
bad = []

def iter_files(root):
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".json", ".ts", ".tsx", ".py", ".html"}:
            yield path

for root in roots:
    if not root.exists():
        continue
    for path in iter_files(root):
        try:
            lines = path.read_text("utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, 1):
            for phrase in forbidden:
                if phrase in line and not any(marker in line for marker in allowed_markers):
                    bad.append(f"{path}:{number}:{phrase}")

if bad:
    Path("/tmp/ad-edge-copy-boundary.txt").write_text("\n".join(bad) + "\n", encoding="utf-8")
    raise SystemExit(1)
PY
}

log "environment"
run_check "script is running from WSL project root" require_wsl_root

log "basic startup"
run_check "./start_demo.sh can start and expose GET /api/health status ok" check_start_demo_contract
if start_backend; then
  pass "fallback backend started with .venv/bin/python -m uvicorn for API acceptance"
else
  fail "fallback backend started with .venv/bin/python -m uvicorn for API acceptance"
fi
run_check "GET /api/health returns ok" health_returns_ok
run_check "frontend source exposes backend connection and offline report states" check_frontend_source_has_backend_badge

log "offline acceptance"
run_check "docs explain installed-dependency offline startup without remote APIs" check_offline_runtime_docs
run_check "runtime code has no direct remote API endpoint references" check_no_remote_api_reference

log "anti-fake-run acceptance"
run_check "RI analysis completes before destructive checks" run_ri_analysis "$TMP_DIR/run_initial.json"
run_check "report API returns generated report and no diagnosis wording" check_report_completed
run_check "stopping backend blocks report API access" check_backend_stopped_blocks_api
if start_backend; then
  pass "backend restarted after stopped-backend check"
else
  fail "backend restarted after stopped-backend check"
fi
run_check "missing compute/sr_dwi_4d.nii.gz makes RI analysis fail" check_missing_dwi_fails
run_check "missing output/report.json returns not_completed without hardcoded conclusions" check_missing_report_has_no_hardcoded_conclusion
run_check "modified mock dMRI changes recomputed RI output" check_modified_dwi_changes_output

log "git and copy boundaries"
run_check "git status runs and generated dependency/build dirs are not tracked" check_git_status_and_ignored_dirs
run_check "page/docs/report wording stays inside demo boundaries" check_copy_boundaries

log "manual 1024x600 touch-screen acceptance required"
cat <<'EOF'
Open the frontend on the target screen at 1024x600 and manually verify:
1. Browser opens http://127.0.0.1:5173 or the board IP URL provided by start_demo.sh.
2. At 100% zoom, the top bar, sidebar, case table, RI charts, and report page are readable.
3. At 90% zoom, no text overlaps, and horizontal scrolling is limited to tables/charts when needed.
4. Touch taps work for refresh, case selection, local super-resolution demo, RI analysis, theme toggle, and report refresh.
5. Vertical scrolling reaches all controls and chart legends without hidden buttons.
6. RI curve and ROI metric charts remain legible on the 1024x600 panel.
EOF

if [ "$FAILURES" -eq 0 ]; then
  log "all scriptable checks passed"
  exit 0
fi

log "${FAILURES} scriptable check(s) failed"
printf 'Temporary logs are under %s until cleanup runs.\n' "$TMP_DIR"
exit 1
