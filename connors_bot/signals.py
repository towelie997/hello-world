"""Signale – identisch zu strategy_lab/strategies/connors_rsi2.py (per Test geprüft).

Kauf:    Schluss > SMA(200) und RSI(2) < 5
Verkauf: Schluss > SMA(5)
"Schluss" ist im Live-Betrieb der Kurs kurz vor Börsenschluss (Näherung).
"""

from __future__ import annotations

import pandas as pd


def rsi(close: pd.Series, n: int = 2) -> pd.Series:
    """Wilder-RSI, gleiche Formel wie strategy_lab.engine.rsi."""
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / down)


def with_live_price(history: pd.Series, price: float, today: pd.Timestamp) -> pd.Series:
    """Tagesschlüsse bis gestern + heutiger Kurs als letzter Wert."""
    h = history[history.index < today]
    return pd.concat([h, pd.Series([price], index=[today])])


def snapshot(closes: pd.Series) -> dict | None:
    """Kennzahlen am letzten Tag; None, wenn zu wenig Historie (< 200 Tage)."""
    closes = closes.dropna()
    if len(closes) < 200:
        return None
    return {
        "close": float(closes.iloc[-1]),
        "sma200": float(closes.iloc[-200:].mean()),
        "sma5": float(closes.iloc[-5:].mean()),
        "rsi2": float(rsi(closes, 2).iloc[-1]),
    }


def is_entry(k: dict, rsi_entry: float = 5.0) -> bool:
    return k["close"] > k["sma200"] and k["rsi2"] < rsi_entry


def is_exit(k: dict) -> bool:
    return k["close"] > k["sma5"]
