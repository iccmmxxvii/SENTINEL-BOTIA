from __future__ import annotations

import socket
import sqlite3
from pathlib import Path

from .adapters import detect_adapters


def run_doctor(base_dir: Path, db_path: str) -> list[tuple[str, str]]:
    checks: list[tuple[str, str]] = []
    checks.append(("python", "✅"))

    try:
        socket.gethostbyname("gamma-api.polymarket.com")
        checks.append(("network_dns", "✅"))
    except Exception:
        checks.append(("network_dns", "🟡"))

    try:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.execute("select 1")
        conn.close()
        checks.append(("sqlite", "✅"))
    except Exception:
        checks.append(("sqlite", "❌"))

    checks.append(("permissions", "✅" if Path(base_dir).exists() else "❌"))

    for name, present in detect_adapters(base_dir).items():
        checks.append((f"adapter:{name}", "✅" if present else "🟡"))
    return checks
