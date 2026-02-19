from __future__ import annotations

import json
import time
from pathlib import Path

from .adapters import BasicSafetyGuard, BasicSignalEngine, PaperExecutionEngine, StubCopySource
from .config import deep_get
from .data_clients import discover_btc_5m_market, fetch_reference_price, sleep_backoff, utcnow
from .heartbeat import write_status
from .logging_utils import setup_logger
from .storage import Storage


def run_engine(cfg: dict, base_dir: Path, max_seconds: int | None = None) -> None:
    db_path = str(base_dir / deep_get(cfg, "data.db_path", "data/botia5m.sqlite"))
    status_path = str(base_dir / deep_get(cfg, "data.status_path", "STATUS.md"))
    log_path = str(base_dir / deep_get(cfg, "data.log_path", "logs/botia5m.log"))

    storage = Storage(db_path)
    logger = setup_logger(log_path)
    exec_engine = PaperExecutionEngine()
    safety = BasicSafetyGuard(cfg)
    signal = BasicSignalEngine(cfg)
    copy_source = StubCopySource()

    loop_seconds = int(deep_get(cfg, "runtime.loop_seconds", 5))
    heartbeat_seconds = int(deep_get(cfg, "runtime.heartbeat_seconds", 30))
    max_backoff = int(deep_get(cfg, "runtime.max_backoff_seconds", 60))
    discovery_urls = deep_get(cfg, "market.discovery_urls", []) or []
    reference_urls = deep_get(cfg, "market.reference_urls", []) or []

    started = time.time()
    last_heartbeat = 0.0
    backoff = 1

    while True:
        if max_seconds and (time.time() - started) >= max_seconds:
            break

        market = discover_btc_5m_market(discovery_urls)
        ref_price, price_source = fetch_reference_price(reference_urls)

        now = utcnow()
        storage.exec(
            "INSERT INTO markets(ts, market_slug, question, close_time, raw_json) VALUES (?, ?, ?, ?, ?)",
            (now, market["slug"], market["question"], market["close_time"], json.dumps(market["raw"])),
        )

        if ref_price is None:
            reason = "NO_TRADE: reference_price_unavailable"
            storage.exec("INSERT INTO ticks(ts, symbol, ref_price, raw_json) VALUES (?, ?, ?, ?)", (now, "BTC", None, json.dumps({"source": price_source, "degraded": True})))
            decision = signal.compute_edge(market, float(market.get("last_price", 0) or 0), 60)
            decision.action = "NO_TRADE"
            decision.reason = "reference_price_unavailable"
            decision.size = 0
            storage.exec(
                "INSERT INTO decisions(ts, market_slug, action, probability, reason, size) VALUES (?, ?, ?, ?, ?, ?)",
                (now, market["slug"], decision.action, decision.probability, decision.reason, decision.size),
            )
            storage.exec("INSERT INTO rounds(ts, market_slug, status, reason) VALUES (?, ?, ?, ?)", (now, market["slug"], "NO_TRADE", reason))
            logger.info("degraded_no_trade", extra={"extra": {"reason": reason}})
            backoff = sleep_backoff(backoff, max_backoff)
        else:
            backoff = 1
            storage.exec("INSERT INTO ticks(ts, symbol, ref_price, raw_json) VALUES (?, ?, ?, ?)", (now, "BTC", ref_price, json.dumps({"source": price_source})))
            decision = signal.compute_edge(market, ref_price, 60)
            storage.exec(
                "INSERT INTO decisions(ts, market_slug, action, probability, reason, size) VALUES (?, ?, ?, ?, ?, ?)",
                (now, market["slug"], decision.action, decision.probability, decision.reason, decision.size),
            )
            round_trades = storage.fetchall("SELECT COUNT(*) FROM trades_paper WHERE market_slug = ?", (market["slug"],))[0][0]
            ctx = {"size": decision.size, "round_trades": round_trades}
            if safety.allow(decision.action, ctx):
                trade = exec_engine.place_order(decision.action, ref_price, decision.size, {"market": market["slug"], "paper": True})
                storage.exec(
                    "INSERT INTO trades_paper(ts, order_id, market_slug, side, price, size, reason) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (now, trade.order_id, market["slug"], trade.side, trade.price, trade.size, trade.reason),
                )
            storage.exec("INSERT INTO rounds(ts, market_slug, status, reason) VALUES (?, ?, ?, ?)", (now, market["slug"], decision.action, decision.reason))

        if (time.time() - last_heartbeat) >= heartbeat_seconds:
            write_status(
                status_path,
                {
                    "mode": "paper",
                    "market": market["slug"],
                    "ref_price": ref_price if ref_price is not None else "N/A",
                    "decision": decision.action if ref_price is not None else "NO_TRADE",
                    "reason": decision.reason if ref_price is not None else "reference_price_unavailable",
                },
            )
            last_heartbeat = time.time()

        copy_source.poll_target()
        time.sleep(loop_seconds)
