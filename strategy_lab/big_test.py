"""Großer Test: alle Tages-/Wochenstrategien auf 200 Werten aus S&P 500 und DAX.

    python -m strategy_lab.big_test                  alle Strategien (~25 Min.)
    python -m strategy_lab.big_test --only "Connors"  nur Jobs, deren Name den Text enthält;
                                                      ersetzt deren Trades, Rest bleibt

Pflicht im wöchentlichen Lauf für jede neue Tages-/Wochenstrategie (siehe README):
neue Strategie in `jobs` unten eintragen (mit Vergleichs-Variante) und mit --only testen.

Universum: strategy_lab/universe.py (40 DAX + 160 zufällig gezogene S&P-500-Werte).
Schreibt nach results/big/: trades.csv.gz, ranking.csv, per_symbol.csv,
robustness.csv (gleiche Kriterien wie robustness.py) und momentum_filter.csv
(relatives Momentum jetzt = obere Hälfte von 200 Werten).
Intraday- und Forex-Strategien sind nicht enthalten (Yahoo liefert dafür zu wenig Historie).
"""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import asdict

import pandas as pd

from . import momentum_filter, robustness
from .engine import summarize
from .run_all import RESULTS, VIDEOS
from .strategies import (golden_cross, qs_connors6, tl_bb_rsi, turtles_tmr0,
                         chartart_bb_rsi, chartart_macd_sma, connors_rsi2, donchian_macd,
                         ema50_pullback, ema_rsi_engulf, glow_ribbon, moving_momentum, qs5,
                         qs_ibs, squeeze_swing, weekly_breakout, weinstein)
from .universe import BIG

OUT = os.path.join(RESULTS, "big")
N_SIM_MOMENTUM = 5000


def jobs_for(U):
    """Alle Tages-/Wochenstrategien als (Name, Funktion) für das Universum U."""
    return [
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
        ("QS 5 Regeln", lambda: qs5.run(U, label=" (1d)")),
        ("Weinstein", lambda: weinstein.run(U)),
        ("Vergleich Weinstein", lambda: weinstein.run(U, baseline=True)),
        ("ChartArt BB+RSI", lambda: chartart_bb_rsi.run(U)),
        ("ChartArt BB+RSI Long", lambda: chartart_bb_rsi.run(U, shorts=False)),
        ("Vergleich BB", lambda: chartart_bb_rsi.run(U, baseline=True)),
        ("ChartArt MACD+SMA", lambda: chartart_macd_sma.run(U)),
        ("ChartArt MACD+SMA Long", lambda: chartart_macd_sma.run(U, shorts=False)),
        ("Vergleich MACD", lambda: chartart_macd_sma.run(U, baseline=True)),
        ("Moving Momentum", lambda: moving_momentum.run(U)),
        ("Moving Momentum Long", lambda: moving_momentum.run(U, shorts=False)),
        ("Vergleich Moving Mom.", lambda: moving_momentum.run(U, baseline=True)),
        ("TL BB+RSI", lambda: tl_bb_rsi.run(U)),
        ("TL BB+RSI Long", lambda: tl_bb_rsi.run(U, shorts=False)),
        ("Vergleich TL BB", lambda: tl_bb_rsi.run(U, baseline=True)),
        ("Golden Cross", lambda: golden_cross.run(U)),
        ("Vergleich Golden", lambda: golden_cross.run(U, baseline=True)),
        ("Turtles", lambda: turtles_tmr0.run(U)),
        ("Turtles Long", lambda: turtles_tmr0.run(U, shorts=False)),
        ("QSC double5", lambda: qs_connors6.run(U, "double5")),
        ("QSC tage_runter", lambda: qs_connors6.run(U, "tage_runter")),
        ("QSC prozent_b", lambda: qs_connors6.run(U, "prozent_b")),
        ("QSC r3", lambda: qs_connors6.run(U, "r3")),
        ("QSC rsi5", lambda: qs_connors6.run(U, "rsi5")),
        ("QSC drei_tage", lambda: qs_connors6.run(U, "drei_tage")),
    ]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", action="append", default=[],
                    help="nur Jobs, deren Name diesen Text enthält (mehrfach möglich)")
    args = ap.parse_args(argv)
    jobs = jobs_for(BIG)
    if args.only:
        jobs = [j for j in jobs if any(o.lower() in j[0].lower() for o in args.only)]
        if not jobs:
            raise SystemExit(f"Kein Job passt zu {args.only}")
    all_trades = []
    for label, fn in jobs:
        t0 = time.time()
        trades = fn()
        print(f"{label:<22} {len(trades):>7} Trades  ({time.time() - t0:.0f} s)", flush=True)
        all_trades += trades

    df = pd.DataFrame([asdict(t) for t in all_trades])
    old_path = os.path.join(OUT, "trades.csv.gz")
    if args.only and os.path.exists(old_path):
        # nur die neu gerechneten Strategien ersetzen, alle anderen behalten
        old = pd.read_csv(old_path)
        df = pd.concat([old[~old.strategy.isin(set(df.strategy))], df], ignore_index=True)
    df["_t"] = pd.to_datetime(df.entry_time)  # gleiche Reihenfolge wie beim Volllauf
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
