"""Großer Test: alle Tages-/Wochenstrategien auf 200 Werten aus S&P 500 und DAX.

    python -m strategy_lab.big_test        (aus dem Repo-Hauptordner, dauert lange)

Universum: strategy_lab/universe.py (40 DAX + 160 zufällig gezogene S&P-500-Werte).
Schreibt nach results/big/: trades.csv.gz, ranking.csv, per_symbol.csv,
robustness.csv (gleiche Kriterien wie robustness.py) und momentum_filter.csv
(relatives Momentum jetzt = obere Hälfte von 200 Werten).
Intraday- und Forex-Strategien sind nicht enthalten (Yahoo liefert dafür zu wenig Historie).
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict

import pandas as pd

from . import momentum_filter, robustness
from .engine import summarize
from .run_all import RESULTS, VIDEOS
from .strategies import (connors_rsi2, donchian_macd, ema50_pullback, ema_rsi_engulf,
                         glow_ribbon, qs_ibs, squeeze_swing, weekly_breakout)
from .universe import BIG

OUT = os.path.join(RESULTS, "big")
N_SIM_MOMENTUM = 2000


def main():
    U = BIG
    jobs = [
        ("EMA/RSI/Engulf 1d", lambda: ema_rsi_engulf.run(U, "1d", "max")),
        ("Vergleich 1d", lambda: ema_rsi_engulf.run(U, "1d", "max", baseline=True)),
        ("EMA50 Pullback 1d", lambda: ema50_pullback.run(U, "1d", "max")),
        ("Squeeze 1d", lambda: squeeze_swing.run(U, "1d")),
        ("Squeeze 1w", lambda: squeeze_swing.run(U, "1w")),
        ("Vergleich Squeeze 1d", lambda: squeeze_swing.run(U, "1d", baseline=True)),
        ("Vergleich Squeeze 1w", lambda: squeeze_swing.run(U, "1w", baseline=True)),
        ("Connors RSI2", lambda: connors_rsi2.run(U)),
        ("Vergleich RSI2", lambda: connors_rsi2.run(U, baseline=True)),
        ("QS Swing", lambda: qs_ibs.run(U, label=" (1d)")),
        ("Vergleich QS", lambda: qs_ibs.run(U, baseline=True, label=" (1d)")),
        ("Wochen-Ausbruch", lambda: weekly_breakout.run(U)),
        ("Vergleich Ausbruch", lambda: weekly_breakout.run(U, baseline=True)),
        ("Glow Ribbon", lambda: glow_ribbon.run(U)),
        ("Glow Ribbon Long", lambda: glow_ribbon.run(U, shorts=False)),
        ("Vergleich Glow", lambda: glow_ribbon.run(U, baseline=True)),
        ("Donchian+MACD", lambda: donchian_macd.run(U)),
        ("Vergleich Donchian", lambda: donchian_macd.run(U, baseline=True)),
    ]
    all_trades = []
    for label, fn in jobs:
        t0 = time.time()
        trades = fn()
        print(f"{label:<22} {len(trades):>7} Trades  ({time.time() - t0:.0f} s)", flush=True)
        all_trades += trades

    df = pd.DataFrame([asdict(t) for t in all_trades])
    df["_t"] = pd.to_datetime(df.entry_time)
    df = df.sort_values(["strategy", "_t"], kind="stable").drop(columns="_t").reset_index(drop=True)
    os.makedirs(OUT, exist_ok=True)
    df.to_csv(os.path.join(OUT, "trades.csv.gz"), index=False)

    rows = []
    for name, g in df.groupby("strategy", sort=False):
        channel = VIDEOS.get(name, ("", "", ""))[0]
        rows.append({"strategie": name, "quelle": channel, "werte": g.symbol.nunique(), **summarize(g)})
    table = pd.DataFrame(rows).sort_values("profit_factor", ascending=False)
    table.to_csv(os.path.join(OUT, "ranking.csv"), index=False)
    print(table.to_string(index=False))
    (df.groupby(["strategy", "symbol"]).apply(lambda g: pd.Series(summarize(g)))
     .reset_index().to_csv(os.path.join(OUT, "per_symbol.csv"), index=False))

    print("\n=== Robustheit ===", flush=True)
    robustness.main("big/trades.csv.gz", "big/robustness.csv")
    print("\n=== Momentum-Filter ===", flush=True)
    momentum_filter.main(BIG, "big/trades.csv.gz", "big/momentum_filter.csv", N_SIM_MOMENTUM)


if __name__ == "__main__":
    main()
