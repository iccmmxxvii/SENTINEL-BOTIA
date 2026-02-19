from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class TradeResult:
    accepted: bool
    order_id: str
    side: str
    price: float
    size: float
    reason: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    action: str
    probability: float
    reason: str
    size: float = 0.0


@dataclass
class TargetEvent:
    source: str
    side: str
    size: float
    ts: str
    meta: dict[str, Any] = field(default_factory=dict)


class ExecutionEngine(Protocol):
    def place_order(self, side: str, price: float, size: float, meta: dict[str, Any]) -> TradeResult:
        ...


class SafetyGuard(Protocol):
    def allow(self, action: str, context: dict[str, Any]) -> bool:
        ...


class SignalEngine(Protocol):
    def compute_edge(self, market_state: dict[str, Any], ref_price: float, time_to_close: int) -> Decision:
        ...


class CopySource(Protocol):
    def poll_target(self) -> list[TargetEvent]:
        ...
