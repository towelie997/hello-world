"""Connors RSI(2) mit Stop-Loss – das Original hat keinen.

    python -m strategy_lab.connors_stops      (nach run_all und big_test)

Varianten (vorab festgelegt, nicht optimiert): ohne Stop (Original), Stop 5 % / 10 %
unter Einstieg, Stop 2 / 3 ATR(14) unter Einstieg, Zeit-Stop 10 Handelstage. Der
Ausstieg "Schluss > SMA5" bleibt immer aktiv. Getestet auf den 26 Werten (SWING) und den
200 Werten aus S&P 500 + DAX. Robustheit mit denselben Kriterien wie robustness.py,
Holm-Korrektur je Universum über alle Varianten.
Kennzahlen in % je Trade sind hier wichtiger als R, weil ein Stop vor allem die
großen Einzelverluste begrenzen soll: schlechtester Trade, 1-%-Quantil, Drawdown.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

from .robustness import analyze, bear_market_days, holm, profit_factor
from .run_all import RESULTS, SWING
from .strategies import connors_rsi2
from .universe import BIG

VARIANTS = [
    ("ohne Stop (Original)", None),
    ("Stop 5 %", ("pct", 0.05)),
    ("Stop 10 %", ("pct", 0.10)),
    ("Stop 2 ATR", ("atr", 2)),
    ("Stop 3 ATR", ("atr", 3)),
    ("Zeit-Stop 10 Tage", ("days", 10)),
]


def main():
    bear = bear_market_days()
    rows = []
    for uni_name, uni in [("26 Werte", SWING), ("200 Werte", BIG)]:
        rng = np.random.default_rng(42)
        part = []
        for label, stop in VARIANTS:
            trades = connors_rsi2.run(uni, stop=stop, name=f"Connors RSI(2) – {label}")
            g = pd.DataFrame([t.__dict__ for t in trades])
            last_year = pd.to_datetime(g.entry_time).dt.year.max()
            rob = analyze(g.strategy.iloc[0], g, bear, rng, last_year)
            # Drawdown in %: gleich große Positionen nacheinander aufsummiert (vereinfachend)
            eq = g.sort_values("entry_time").pct.cumsum()
            part.append({
                "universum": uni_name, "variante": label, "trades": len(g),
                "treffer_%": round(100 * (g.r > 0).mean(), 1),
                "pf": rob["pf"], "pf_pct": rob["pf_pct"],
                "avg_pct": round(g.pct.mean(), 3), "summe_pct": round(g.pct.sum()),
                "schlechtester_pct": round(g.pct.min(), 1),
                "quantil_1%_pct": round(float(np.quantile(g.pct, 0.01)), 1),
                "max_dd_pct": round(float((eq - eq.cummax()).min())),
                "anteil_stop_%": round(100 * g.reason.isin(["stop", "time"]).mean(), 1),
                "haltetage": int((pd.to_datetime(g.exit_time) - pd.to_datetime(g.entry_time)).dt.days.median()),
                "pf_letzte5": rob["pf_letzte5"], "jahre_pf>1_%": rob["jahre_pf>1_%"],
                "pf_baerenmarkt": rob["pf_baerenmarkt"], "pf_boot_5%": rob["pf_boot_5%"],
                "split_min": min(rob["split_min_vorher"], rob["split_min_nachher"]),
                "pf_zufall": rob["pf_zufall_median"], "p_zufall": rob["p_zufall"],
            })
            print(f"{uni_name:<10} {label:<22} {len(g):>6} Trades", flush=True)
        adj = holm({r["variante"]: r["p_zufall"] for r in part})
        for r in part:
            r["p_zufall_holm"] = round(adj[r["variante"]], 4)
            checks = [r["p_zufall_holm"] < 0.05, r["pf_boot_5%"] > 1, r["jahre_pf>1_%"] >= 70,
                      r["split_min"] > 1]
            r["urteil"] = "robust" if all(checks) else f"nein ({sum(checks)}/4)"
        rows += part
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(RESULTS, "connors_stops.csv"), index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(out.to_string(index=False))


if __name__ == "__main__":
    main()
