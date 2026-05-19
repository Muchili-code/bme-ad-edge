from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services.ri_analysis import RIAnalysisError, run_ri_analysis


def main() -> None:
    dwi_path = Path("data/cases/case_HC_001/compute/sr_dwi_4d.nii.gz")
    backup_path = dwi_path.with_name("sr_dwi_4d.nii.gz.workerb_tmp")
    dwi_path.rename(backup_path)
    try:
        try:
            run_ri_analysis("case_HC_001")
        except RIAnalysisError as exc:
            print(str(exc))
        else:
            raise SystemExit("run_ri_analysis unexpectedly succeeded with missing dMRI input")
    finally:
        backup_path.rename(dwi_path)


if __name__ == "__main__":
    main()
