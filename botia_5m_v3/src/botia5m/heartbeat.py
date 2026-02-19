from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def write_status(path: str, state: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "# BOTIA_5M_V3 STATUS",
        f"updated_at: {now}",
        f"mode: {state.get('mode', 'paper')}",
        f"last_market: {state.get('market', 'N/A')}",
        f"last_ref_price: {state.get('ref_price', 'N/A')}",
        f"last_decision: {state.get('decision', 'N/A')}",
        f"last_reason: {state.get('reason', 'N/A')}",
    ]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
