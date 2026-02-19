from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .config import deep_get, load_config
from .doctor import run_doctor
from .engine import run_engine
from .storage import Storage


def _guard_live(cfg: dict, paper: bool) -> None:
    live_enabled = bool(deep_get(cfg, "mode.live_enabled", False))
    live_confirmation = str(deep_get(cfg, "mode.live_confirmation", ""))
    if paper:
        return
    if not (live_enabled and live_confirmation == "CONFIRMO"):
        raise SystemExit("LIVE bloqueado: usar --paper o configurar mode.live_enabled=true y mode.live_confirmation=CONFIRMO")


def main() -> None:
    parser = argparse.ArgumentParser(prog="botia5m")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor")

    run_p = sub.add_parser("run")
    run_p.add_argument("--paper", action="store_true")
    run_p.add_argument("--max-seconds", type=int, default=None)

    sub.add_parser("status")

    exp = sub.add_parser("export")
    exp.add_argument("--csv", required=True)

    args = parser.parse_args()
    base_dir = Path.cwd()
    cfg = load_config(base_dir)

    if args.cmd == "doctor":
        checks = run_doctor(base_dir, str(base_dir / deep_get(cfg, "data.db_path", "data/botia5m.sqlite")))
        for name, status in checks:
            print(f"{status} {name}")
        return

    if args.cmd == "run":
        _guard_live(cfg, args.paper)
        run_engine(cfg, base_dir, max_seconds=args.max_seconds)
        return

    if args.cmd == "status":
        status_path = base_dir / deep_get(cfg, "data.status_path", "STATUS.md")
        print(status_path.read_text(encoding="utf-8") if status_path.exists() else "STATUS.md not found")
        return

    if args.cmd == "export":
        db = Storage(str(base_dir / deep_get(cfg, "data.db_path", "data/botia5m.sqlite")))
        rows = db.fetchall("SELECT ts, market_slug, action, probability, reason, size FROM decisions ORDER BY ts DESC")
        out = Path(args.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ts", "market_slug", "action", "probability", "reason", "size"])
            w.writerows(rows)
        print(f"exported {len(rows)} rows to {out}")
