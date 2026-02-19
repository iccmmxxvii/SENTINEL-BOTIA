from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from pathlib import Path

from .config import deep_get
from .interfaces import CopySource, Decision, ExecutionEngine, SafetyGuard, TargetEvent, TradeResult


class PaperExecutionEngine(ExecutionEngine):
    def place_order(self, side: str, price: float, size: float, meta: dict) -> TradeResult:
        oid = f"paper-{int(time.time() * 1000)}-{random.randint(100,999)}"
        return TradeResult(True, oid, side, price, size, reason="paper_fill", meta=meta)


class BasicSafetyGuard(SafetyGuard):
    def __init__(self, cfg: dict):
        self.max_size = float(deep_get(cfg, "risk.max_size", 50))
        self.cooldown_seconds = int(deep_get(cfg, "risk.cooldown_seconds", 10))
        self.max_per_round = int(deep_get(cfg, "risk.max_trades_per_round", 1))
        self.last_trade_ts = 0.0

    def allow(self, action: str, context: dict) -> bool:
        if action == "NO_TRADE":
            return False
        if float(context.get("size", 0)) > self.max_size:
            return False
        if time.time() - self.last_trade_ts < self.cooldown_seconds:
            return False
        if int(context.get("round_trades", 0)) >= self.max_per_round:
            return False
        self.last_trade_ts = time.time()
        return True


class BasicSignalEngine:
    def __init__(self, cfg: dict):
        self.threshold = float(deep_get(cfg, "risk.min_edge_probability", 0.62))

    def compute_edge(self, market_state: dict, ref_price: float, time_to_close: int) -> Decision:
        last = float(market_state.get("last_price", ref_price))
        diff = (ref_price - last) / max(last, 1e-9)
        probability = min(max(0.5 + diff * 2, 0.0), 1.0)
        if probability >= self.threshold:
            return Decision("BUY_UP", probability, "edge_threshold_met", size=10)
        if (1 - probability) >= self.threshold:
            return Decision("BUY_DOWN", 1 - probability, "inverse_edge_threshold_met", size=10)
        return Decision("NO_TRADE", max(probability, 1 - probability), "edge_below_threshold", size=0)


class StubCopySource(CopySource):
    def poll_target(self) -> list[TargetEvent]:
        return [
            TargetEvent(
                source="stub_collectmarkets2",
                side="NONE",
                size=0,
                ts=datetime.now(timezone.utc).isoformat(),
                meta={"note": "copy source stub in paper mode"},
            )
        ]


def detect_adapters(base_dir: Path) -> dict[str, bool]:
    names = ["4coinsbot-main", "mlmodelpoly-main", "collectmarkets2-main"]
    return {n: (base_dir / n).exists() for n in names}
