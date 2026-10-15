"""TOP 200 nach Liquidität – monatlich neu, ohne Blick in die Zukunft.

    python -m strategy_lab.top200          (~1 Std.; schreibt results/top200/)

Pool: alle aktuellen S&P-500-Werte + alle 40 DAX-Werte (~540). Zu jedem Monatsanfang
werden die 200 Werte mit dem höchsten durchschnittlichen Tagesumsatz in USD (Kurs x
Stückzahl, DAX mit EUR/USD umgerechnet) der letzten 63 Handelstage VOR dem Monat
ausgewählt. Ein Trade zählt nur, wenn die Aktie im Monat des Einstiegs zur TOP 200 gehört.

Ablauf: alle Tages-/Wochenstrategien (jobs_for aus big_test.py) laufen auf dem ganzen
Pool, danach werden die Trades nach Mitgliedschaft gefiltert. Vereinfachung: Ein
weggefilterter Trade blockiert den Wert nicht für spätere Signale (je Wert ist immer nur
eine Position offen, andere Werte sind davon nicht betroffen).

Vergleich: zufällige 200 (big_test) – liquideste 200 – ganzer Pool, gleiche Regeln.
Grenze: Pool = heutige Indexmitglieder (Survivorship-Bias bleibt, wird nur gemildert).
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict

import numpy as np
import pandas as pd

from . import data, robustness
from .big_test import jobs_for
from .engine import summarize
from .run_all import RESULTS
from .universe import DAX40, SP500_ALL

OUT = os.path.join(RESULTS, "top200")
POOL = SP500_ALL + DAX40
TOP_N = 200
LOOKBACK = 63
POOL_CACHE = os.path.join(data.CACHE_DIR, "top200_pool_trades.pkl")


def membership(pool=POOL, top_n=TOP_N, lookback=LOOKBACK) -> pd.DataFrame:
    """Monat (Periode) x Symbol -> True, wenn der Wert in dem Monat zur TOP N gehört."""
    eurusd = data.load("EURUSD=X", "1d", "max").Close
    dv = {}
    for s in pool:
        px, vol = data.load(s, "1d", "max"), data.load_volume(s)
        if px.empty or vol.empty:
            continue
        x = px.Close * vol.reindex(px.index)
        if s.endswith(".DE"):
            x = x * eurusd.reindex(px.index, method="ffill")
        dv[s] = x.rolling(lookback, min_periods=lookback).mean()
    dv = pd.DataFrame(dv).sort_index()
    dv = dv[dv.index >= "2003-01-01"]
    last_day = dv.resample("ME").last()                          # letzter gültiger Wert je Monat
    last_day.index = last_day.index.to_period("M") + 1           # gilt für den Folgemonat
    rank = last_day.rank(axis=1, ascending=False, method="first")
    return (rank <= top_n) & last_day.notna()


def main():
    os.makedirs(OUT, exist_ok=True)
    mem = membership()
    mem.to_csv(os.path.join(OUT, "mitglieder.csv"))
    print(f"TOP {TOP_N}: {mem.shape[0]} Monate, {int(mem.any().sum())} Werte waren mind. einmal dabei",
          flush=True)

    if os.path.exists(POOL_CACHE) and time.time() - os.path.getmtime(POOL_CACHE) < 24 * 3600:
        pool = pd.read_pickle(POOL_CACHE)
    else:
        trades = []
        for label, fn in jobs_for(POOL):
            t0 = time.time()
            tr = fn()
            print(f"{label:<22} {len(tr):>8} Trades  ({time.time() - t0:.0f} s)", flush=True)
            trades += tr
        pool = pd.DataFrame([asdict(t) for t in trades])
        pool.to_pickle(POOL_CACHE)

    month = pd.to_datetime(pool.entry_time).dt.to_period("M")
    stacked = mem.stack()
    member = pd.Series(stacked.values, index=stacked.index)
    keep = np.array([member.get((m, s), False) for m, s in zip(month, pool.symbol)])
    top = pool[keep].copy()
    top["_t"] = pd.to_datetime(top.entry_time)
    top = top.sort_values(["strategy", "_t"], kind="stable").drop(columns="_t").reset_index(drop=True)
    top.to_csv(os.path.join(OUT, "trades.csv.gz"), index=False)

    rows = []
    for name, g in top.groupby("strategy", sort=False):
        rows.append({"strategie": name, "werte": g.symbol.nunique(), **summarize(g)})
    pd.DataFrame(rows).sort_values("profit_factor", ascending=False).to_csv(
        os.path.join(OUT, "ranking.csv"), index=False)

    print("\n=== Robustheit TOP 200 ===", flush=True)
    robustness.main("top200/trades.csv.gz", "top200/robustness.csv")

    # Vergleich zufällige 200 / liquideste 200 / ganzer Pool
    rnd = pd.read_csv(os.path.join(RESULTS, "big", "robustness.csv")).set_index("strategie")
    liq = pd.read_csv(os.path.join(OUT, "robustness.csv")).set_index("strategie")
    pool_pf = pool.groupby("strategy").r.apply(lambda r: summarize(pd.DataFrame({"r": r, "pct": 0})
                                                                   )["profit_factor"])
    comp = pd.DataFrame({
        "pf_zufall200": rnd.pf, "pf_top200": liq.pf, "pf_pool": pool_pf,
        "trades_zufall200": rnd.trades, "trades_top200": liq.trades,
        "pf_letzte5_zufall200": rnd.pf_letzte5, "pf_letzte5_top200": liq.pf_letzte5,
        "p_zufall_top200": liq.p_zufall_holm,
        "urteil_zufall200": rnd.urteil, "urteil_top200": liq.urteil,
    }).dropna(subset=["pf_top200"]).sort_values("pf_top200", ascending=False)
    comp.round(3).to_csv(os.path.join(OUT, "vergleich.csv"))
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(comp.to_string())


if __name__ == "__main__":
    main()
