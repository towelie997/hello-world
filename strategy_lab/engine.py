"""Gemeinsame Bausteine: Trade-Datensatz, Ausstiegs-Simulation, Kennzahlen."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

# Kosten je Seite (Gebühr + Slippage) als Anteil vom Preis.
DEFAULT_COST = 0.0001


@dataclass
class Trade:
    strategy: str
    symbol: str
    side: str          # "long" / "short"
    entry_time: str
    entry: float
    stop: float
    target: float | None
    exit_time: str
    exit: float
    reason: str        # "target" / "stop" / "eod" / "signal" / "end"
    r: float           # Ergebnis in R nach Kosten
    pct: float         # Ergebnis in % vom Einstieg nach Kosten


def make_trade(strategy, symbol, side, entry_time, entry, stop, target,
               exit_time, exit_price, reason, cost=DEFAULT_COST) -> Trade:
    direction = 1 if side == "long" else -1
    gross = direction * (exit_price - entry)
    costs = cost * (entry + exit_price)
    risk = abs(entry - stop)
    return Trade(strategy, symbol, side, str(entry_time), round(entry, 5), round(stop, 5),
                 None if target is None else round(target, 5), str(exit_time),
                 round(exit_price, 5), reason,
                 round((gross - costs) / risk, 4), round(100 * (gross - costs) / entry, 4))


def simulate_exit(bars: pd.DataFrame, start: int, side: str, stop: float,
                  target: float | None, eod: bool = True):
    """Läuft ab Kerze `start` bis Stop/Ziel/Ende. Stop vor Ziel (konservativ),
    Kurslücken über den Stop werden zum Eröffnungskurs gefüllt."""
    for i in range(start, len(bars)):
        b = bars.iloc[i]
        if side == "long":
            if b.Low <= stop:
                return bars.index[i], min(stop, b.Open), "stop"
            if target is not None and b.High >= target:
                return bars.index[i], max(target, b.Open) if b.Open > target else target, "target"
        else:
            if b.High >= stop:
                return bars.index[i], max(stop, b.Open), "stop"
            if target is not None and b.Low <= target:
                return bars.index[i], min(target, b.Open) if b.Open < target else target, "target"
    last = bars.index[-1]
    return last, float(bars.iloc[-1].Close), "eod" if eod else "end"


def summarize(trades: list[Trade] | pd.DataFrame) -> dict:
    df = trades if isinstance(trades, pd.DataFrame) else pd.DataFrame([t.__dict__ for t in trades])
    if df.empty:
        return {"trades": 0}
    wins, losses = df[df.r > 0], df[df.r <= 0]
    equity = df.r.cumsum()
    gross_loss = -losses.r.sum()
    return {
        "trades": int(len(df)),
        "trefferquote_%": round(100 * len(wins) / len(df), 1),
        "avg_R": round(float(df.r.mean()), 3),
        "summe_R": round(float(df.r.sum()), 1),
        "profit_factor": round(float(wins.r.sum() / gross_loss), 2) if gross_loss > 0 else math.inf,
        "max_dd_R": round(float((equity - equity.cummax()).min()), 1),
        "avg_pct": round(float(df.pct.mean()), 3),
    }


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / down)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    prev = df.Close.shift()
    tr = pd.concat([df.High - df.Low, (df.High - prev).abs(), (df.Low - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()
