"""Backtest der "Sneaky Pivot"-Strategie (The Rumers, YouTube zspMXJVbfAY).

Regeln (aus dem Video, so eindeutig wie möglich formalisiert):

  Linien ("Magic Lines"), berechnet vor Handelsbeginn:
    range_high / range_low  = Hoch / Tief des Vortags (reguläre Handelszeit)
    swing_high              = nächstes ältere Tageshoch ÜBER range_high
    swing_low               = nächstes ältere Tagestief UNTER range_low

  Setup (15-Minuten-Kerzen ab 9:30 New York):
    Kerze 1 (Opening Range): bärisch und Tief im Kaufbereich
        (<= range_low + tol)                         -> Long-Setup
      bzw. bullisch und Hoch im Verkaufsbereich
        (>= range_high - tol)                        -> Short-Setup
      tol = zone_pct * (range_high - range_low)
    "Sneaky"-Kerze: die erste grüne (Long) bzw. rote (Short) Kerze
      innerhalb der nächsten `max_sneaky_wait` Kerzen
    Einstieg: sobald eine spätere Kerze das Hoch (Long) bzw. Tief (Short)
      der Sneaky-Kerze überschreitet, spätestens bis `entry_cutoff`
    Stop: unter dem Tagestief (Long) bzw. über dem Tageshoch (Short) bis
      zum Einstieg ("big buyer" / "big seller")
    Ziel: gegenüberliegende Range-Linie (range_high bzw. range_low),
      optional die Swing-Linie (--target swing)
    Ausstieg spätestens zum Handelsschluss. Treffen Stop und Ziel in
      derselben Kerze, wird konservativ der Stop angenommen.

Ergebnisse werden in R (Vielfache des Anfangsrisikos) gemessen, damit
Instrumente mit unterschiedlichen Preisen vergleichbar sind.

Aufruf:
    python sneaky_pivot/backtest.py
    python sneaky_pivot/backtest.py --symbols SPY QQQ NVDA --target swing
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, asdict
from datetime import time

import pandas as pd
import yfinance as yf

DEFAULT_SYMBOLS = [
    "YM=F", "ES=F", "NQ=F",            # Futures (Dow, S&P 500, Nasdaq)
    "SPY", "QQQ", "IWM",               # ETFs
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "AMD",
    "AAOI", "GGLL",                    # Werte aus dem Video
]

SESSION_OPEN = time(9, 30)
SESSION_CLOSE = time(16, 0)


@dataclass
class Trade:
    symbol: str
    date: str
    side: str
    entry_time: str
    entry: float
    stop: float
    target: float
    exit_time: str
    exit: float
    reason: str
    r: float
    pct: float


def load_intraday(symbol: str) -> pd.DataFrame:
    df = yf.download(symbol, period="60d", interval="15m",
                     progress=False, auto_adjust=False)
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close"]].dropna()
    df.index = df.index.tz_convert("America/New_York")
    t = df.index.time
    return df[(t >= SESSION_OPEN) & (t < SESSION_CLOSE)]


def load_daily(symbol: str) -> pd.DataFrame:
    df = yf.download(symbol, period="2y", interval="1d",
                     progress=False, auto_adjust=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["High", "Low"]].dropna()
    df.index = pd.to_datetime(df.index).date
    return df


def magic_lines(day, rth_daily: pd.DataFrame, daily: pd.DataFrame):
    """Range- und Swing-Linien für `day` (nur Daten vor `day`)."""
    prev = rth_daily[rth_daily.index < day]
    if prev.empty:
        return None
    prev_day = prev.index[-1]
    range_high = float(prev.iloc[-1]["High"])
    range_low = float(prev.iloc[-1]["Low"])

    older = daily[daily.index < prev_day].iloc[::-1]
    above = older[older["High"] > range_high]
    below = older[older["Low"] < range_low]
    swing_high = float(above.iloc[0]["High"]) if not above.empty else None
    swing_low = float(below.iloc[0]["Low"]) if not below.empty else None
    return range_high, range_low, swing_high, swing_low


def simulate_day(symbol, day, bars, lines, args) -> Trade | None:
    range_high, range_low, swing_high, swing_low = lines
    width = range_high - range_low
    if width <= 0 or len(bars) < 3:
        return None
    tol = args.zone_pct * width

    b1 = bars.iloc[0]
    if b1.Close < b1.Open and b1.Low <= range_low + tol:
        side = "long"
    elif b1.Close > b1.Open and b1.High >= range_high - tol:
        side = "short"
    else:
        return None

    # Sneaky-Kerze suchen
    sneaky_idx = None
    for i in range(1, min(1 + args.max_sneaky_wait, len(bars))):
        b = bars.iloc[i]
        if (side == "long" and b.Close > b.Open) or (side == "short" and b.Close < b.Open):
            sneaky_idx = i
            break
    if sneaky_idx is None:
        return None
    trigger = bars.iloc[sneaky_idx].High if side == "long" else bars.iloc[sneaky_idx].Low

    # Einstieg
    entry_idx = entry = None
    for i in range(sneaky_idx + 1, len(bars)):
        b = bars.iloc[i]
        if bars.index[i].time() > args.entry_cutoff:
            break
        if side == "long" and b.High > trigger:
            entry_idx, entry = i, max(trigger, b.Open)
            break
        if side == "short" and b.Low < trigger:
            entry_idx, entry = i, min(trigger, b.Open)
            break
    if entry_idx is None:
        return None

    upto = bars.iloc[: entry_idx + 1]
    buffer = args.stop_buffer_pct * width
    if side == "long":
        stop = float(upto.Low.min()) - buffer
        target = range_high
        if args.target == "swing" and swing_high is not None:
            target = swing_high
        if target <= entry:
            return None
    else:
        stop = float(upto.High.max()) + buffer
        target = range_low
        if args.target == "swing" and swing_low is not None:
            target = swing_low
        if target >= entry:
            return None
    risk = abs(entry - stop)
    if risk <= 0:
        return None

    # Verlauf ab der Einstiegskerze (Stop zuerst prüfen = konservativ)
    exit_price = exit_reason = exit_time = None
    for i in range(entry_idx, len(bars)):
        b = bars.iloc[i]
        hit_stop = b.Low <= stop if side == "long" else b.High >= stop
        hit_target = b.High >= target if side == "long" else b.Low <= target
        if hit_stop:
            exit_price, exit_reason = stop, "stop"
        elif hit_target and i > entry_idx:
            exit_price, exit_reason = target, "target"
        if exit_price is not None:
            exit_time = bars.index[i]
            break
    if exit_price is None:
        exit_price, exit_reason, exit_time = float(bars.iloc[-1].Close), "close", bars.index[-1]

    pnl = exit_price - entry if side == "long" else entry - exit_price
    return Trade(symbol, str(day), side, bars.index[entry_idx].strftime("%H:%M"),
                 round(entry, 4), round(stop, 4), round(target, 4),
                 exit_time.strftime("%H:%M"), round(exit_price, 4), exit_reason,
                 round(pnl / risk, 3), round(100 * pnl / entry, 3))


def backtest_symbol(symbol: str, args) -> list[Trade]:
    intraday = load_intraday(symbol)
    if intraday.empty:
        print(f"  {symbol}: keine Daten")
        return []
    daily = load_daily(symbol)
    by_day = {d: g for d, g in intraday.groupby(intraday.index.date)}
    days = sorted(by_day)
    # Nur vollständige Handelstage (heute läuft evtl. noch)
    complete = [d for d in days if by_day[d].index[-1].time() >= time(15, 45)]
    rth_daily = pd.DataFrame(
        {"High": [by_day[d].High.max() for d in complete],
         "Low": [by_day[d].Low.min() for d in complete]},
        index=complete,
    )
    trades = []
    for day in complete[1:]:
        lines = magic_lines(day, rth_daily, daily)
        if lines is None:
            continue
        t = simulate_day(symbol, day, by_day[day], lines, args)
        if t:
            trades.append(t)
    return trades


def summarize(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"trades": 0}
    wins = df[df.r > 0]
    losses = df[df.r <= 0]
    equity = df.r.cumsum()
    drawdown = (equity - equity.cummax()).min()
    gross_loss = -losses.r.sum()
    stats = {
        "trades": len(df),
        "trefferquote_%": round(100 * len(wins) / len(df), 1),
        "avg_R": round(df.r.mean(), 3),
        "summe_R": round(df.r.sum(), 2),
        "profit_factor": round(wins.r.sum() / gross_loss, 2) if gross_loss > 0 else math.inf,
        "max_drawdown_R": round(drawdown, 2),
        "ziel_erreicht_%": round(100 * (df.reason == "target").mean(), 1),
        "stop_%": round(100 * (df.reason == "stop").mean(), 1),
    }
    return {k: float(v) if k != "trades" else v for k, v in stats.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS)
    p.add_argument("--target", choices=["range", "swing"], default="range")
    p.add_argument("--zone-pct", type=float, default=0.10,
                   help="Toleranz um die Linien in Anteil der Vortagesspanne (Default 0.10)")
    p.add_argument("--max-sneaky-wait", type=int, default=3,
                   help="Max. Kerzen nach Kerze 1, um die Sneaky-Kerze zu finden")
    p.add_argument("--entry-cutoff", type=lambda s: time.fromisoformat(s), default=time(12, 0))
    p.add_argument("--stop-buffer-pct", type=float, default=0.02)
    p.add_argument("--out", default="sneaky_pivot/results")
    args = p.parse_args()

    all_trades: list[Trade] = []
    for sym in args.symbols:
        trades = backtest_symbol(sym, args)
        print(f"  {sym}: {len(trades)} Trades")
        all_trades += trades

    df = pd.DataFrame([asdict(t) for t in all_trades])
    if df.empty:
        print("Keine Trades gefunden.")
        return
    df = df.sort_values(["date", "entry_time"]).reset_index(drop=True)

    import os
    os.makedirs(args.out, exist_ok=True)
    df.to_csv(f"{args.out}/trades_{args.target}.csv", index=False)

    print("\n=== Gesamt ===")
    for k, v in summarize(df).items():
        print(f"  {k:>16}: {v}")
    print("\n=== Je Richtung ===")
    for side, g in df.groupby("side"):
        print(f"  {side}: {summarize(g)}")
    print("\n=== Je Symbol ===")
    per = pd.DataFrame({s: summarize(g) for s, g in df.groupby("symbol")}).T
    print(per.to_string())
    print(f"\nTrades gespeichert: {args.out}/trades_{args.target}.csv")


if __name__ == "__main__":
    main()
