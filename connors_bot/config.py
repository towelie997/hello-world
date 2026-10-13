"""Einstellungen – alle per Umgebungsvariable änderbar (siehe README.md)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name, default, cast=str):
    v = os.environ.get(name)
    return default if v in (None, "") else cast(v)


def _opt_float(v):
    return None if str(v).lower() in ("", "none", "0") else float(v)


@dataclass
class Config:
    # Strategie (wie im Backtest strategy_lab/portfolio.py)
    max_positions: int = field(default_factory=lambda: _env("CB_MAX_POSITIONS", 5, int))
    rsi_entry: float = field(default_factory=lambda: _env("CB_RSI_ENTRY", 5.0, float))
    stop_pct: float | None = field(default_factory=lambda: _env("CB_STOP_PCT", None, _opt_float))
    # Risiko
    max_drawdown: float = field(default_factory=lambda: _env("CB_MAX_DRAWDOWN", 0.25, float))
    capital_limit_usd: float | None = field(
        default_factory=lambda: _env("CB_CAPITAL_LIMIT_USD", None, _opt_float))
    minutes_before_close: int = field(default_factory=lambda: _env("CB_MINUTES_BEFORE_CLOSE", 20, int))
    # Interactive Brokers (IB Gateway: 4002 = Papier, 4001 = echt; TWS: 7497 / 7496)
    ib_host: str = field(default_factory=lambda: _env("CB_IB_HOST", "127.0.0.1"))
    ib_port: int = field(default_factory=lambda: _env("CB_IB_PORT", 4002, int))
    ib_client_id: int = field(default_factory=lambda: _env("CB_IB_CLIENT_ID", 17, int))
    market_data_type: int = field(default_factory=lambda: _env("CB_MARKET_DATA_TYPE", 1, int))
    snapshot_batch: int = field(default_factory=lambda: _env("CB_SNAPSHOT_BATCH", 80, int))
    # Dateien und Benachrichtigung
    state_dir: str = field(default_factory=lambda: _env(
        "CB_STATE_DIR", os.path.join(os.path.dirname(__file__), "data")))
    telegram_token: str = field(default_factory=lambda: _env("CB_TELEGRAM_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: _env("CB_TELEGRAM_CHAT_ID", ""))
