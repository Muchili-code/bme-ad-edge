from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services.ri_analysis import run_ri_analysis


def main() -> None:
    for case_id in ["case_HC_001", "case_MCI_001", "case_AD_001"]:
        print(run_ri_analysis(case_id))


if __name__ == "__main__":
    main()
