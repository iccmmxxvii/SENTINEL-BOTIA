from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = [
    """CREATE TABLE IF NOT EXISTS ticks(ts TEXT, symbol TEXT, ref_price REAL, raw_json TEXT)""",
    """CREATE TABLE IF NOT EXISTS rounds(ts TEXT, market_slug TEXT, status TEXT, reason TEXT)""",
    """CREATE TABLE IF NOT EXISTS decisions(ts TEXT, market_slug TEXT, action TEXT, probability REAL, reason TEXT, size REAL)""",
    """CREATE TABLE IF NOT EXISTS trades_paper(ts TEXT, order_id TEXT, market_slug TEXT, side TEXT, price REAL, size REAL, reason TEXT)""",
    """CREATE TABLE IF NOT EXISTS markets(ts TEXT, market_slug TEXT, question TEXT, close_time TEXT, raw_json TEXT)""",
]


class Storage:
    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        for stmt in SCHEMA:
            cur.execute(stmt)
        self.conn.commit()

    def exec(self, query: str, params: tuple = ()) -> None:
        self.conn.execute(query, params)
        self.conn.commit()

    def fetchall(self, query: str, params: tuple = ()):
        return self.conn.execute(query, params).fetchall()
