import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LUMIBOT = ROOT.parent / "lumibot"
SMOKE = LUMIBOT / "scripts" / "run_ai_committee_smoke_backtest.py"


def main() -> None:
    if not SMOKE.exists():
        raise RuntimeError(
            "Deterministic smoke requires a sibling Lumibot checkout with "
            "scripts/run_ai_committee_smoke_backtest.py."
        )
    subprocess.run([sys.executable, str(SMOKE)], cwd=str(LUMIBOT), check=True)


if __name__ == "__main__":
    main()
