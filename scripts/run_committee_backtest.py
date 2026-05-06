from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
LOCAL_LUMIBOT = ROOT.parent / "lumibot"
if LOCAL_LUMIBOT.exists():
    sys.path.insert(0, str(LOCAL_LUMIBOT))

load_dotenv(ROOT / ".env")

if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError("Set OPENAI_API_KEY in .env before running the committee backtest.")

from scripts.run_ai_committee_real_backtest import main


if __name__ == "__main__":
    main()
