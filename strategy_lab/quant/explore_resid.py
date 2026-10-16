"""Nachgelagerte (explorative) Prüfung: Residual-Momentum als eigenständige Strategie.

Hintergrund: In momentum_research.py war die Auswahl nach Residual-Momentum unter allen
11 Merkmalen die beste (Sharpe 0,61 vs. 0,55, 4/4 Abschnitte), hielt der Korrektur für
11 Tests aber nicht stand. Hier die Strategie nach Blitz, Huij & Martens (2011): monatlich
die 20 Werte mit dem höchsten Residual-Momentum aus der ganzen TOP 200 (Stichtags-
Universum), gleiche Bewertung wie run.py. Da die Idee aus den Daten kam, gilt ein
Bestehen hier nur als Hinweis, nicht als Beweis.

    python -m strategy_lab.quant.explore_resid
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

from . import strategies as S
from .compare import connors_targets
from .engine import backtest, sharpe, stats
from .momentum_research import features
from .panel import load_adjusted
from .run import ETF, OUT, PERIODS, START, eligible_panel, period_sharpes, placebo
from ..universe import DAX40, SP500_ALL

HERE = os.path.dirname(__file__)


def main():
    etf = load_adjusted(ETF, "etf")
    pool = load_adjusted(SP500_ALL + DAX40, "pool")
    cal = etf["Close"]["SPY"].dropna().index
    cal = cal[cal >= "2003-01-01"]
    ec = etf["Close"].reindex(cal)
    cash = ec["SHY"].ffill()
    pc = pool["Close"].reindex(cal).ffill(limit=5)
    pv = pool["Volume"].reindex(cal).fillna(0)
    elig = eligible_panel(cal, pc.columns, pit=True) & pc.notna()
    sectors = pd.read_csv(os.path.join(HERE, "sektoren.csv")).set_index("symbol").sektor.to_dict()
    F = features(pc, pv, ec["SPY"], sectors)
    ew = pd.DataFrame({d: elig.loc[d] / elig.loc[d].sum() for d in S.month_ends(cal)}).T
    bench, _ = backtest(ew, pc, cash, 0.0005, start=START)
    bs, pb = sharpe(bench, cash), period_sharpes(bench, cash)
    rows = []

    def report(name, T, neigh=(), with_placebo=False):
        ret, meta = backtest(T, pc, cash, 0.0005, start=START)
        st = stats(ret, cash)
        ps = period_sharpes(ret, cash)
        nb = [sharpe(backtest(t, pc, cash, 0.0005, start=START)[0], cash) for t in neigh]
        row = {"variante": name, **st, "sharpe_vergleich": round(bs, 2),
               "abschnitte": " / ".join(f"{a:.2f}:{b:.2f}" for a, b in zip(ps, pb)),
               "abschnitte_besser": f"{sum(a > b for a, b in zip(ps, pb))}/4",
               "nachbarn_sharpe": " / ".join(f"{x:.2f}" for x in nb)}
        if with_placebo:
            pl = placebo(T, pc, cash, elig, 0.0005, np.random.default_rng(5))
            row["p_vs_zufall"] = round((1 + (pl >= st["sharpe"]).sum()) / (len(pl) + 1), 3)
        rows.append(row)
        print(row, flush=True)

    def top(score, n=20):
        return S._equal_top(score, S.month_ends(cal), elig, n)

    rm = F["resid_mom"]
    report("Residual-Momentum, 20 Pos.", top(rm), [top(rm, 10), top(rm, 40)], with_placebo=True)
    report("Connors RSI(2), 20 Pos. (Abschnitte)", connors_targets(pc, elig, 20))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "explorativ_residual.csv"), index=False)


if __name__ == "__main__":
    main()
