"""Alle Quant-/Hedgefonds-Strategien testen und bewerten.

    python -m strategy_lab.quant.run        (~30–60 Min.; schreibt results/quant/)

Bewertung (vorab festgelegt, nicht nachträglich angepasst):
  a) Sharpe-Quote höher als die Vergleichsanlage
     (Aktien-Strategien: alle TOP-200-Werte gleichgewichtet; sonst: 60 % SPY / 40 % IEF)
  b) in mindestens 3 von 4 Zeitabschnitten (bis 2010, 2011–15, 2016–20, ab 2021) besser
  c) alle Nachbar-Parameter (andere Anzahl/Zeitfenster) ebenfalls besser
  d) nur Aktienauswahl: besser als 100 Zufallsportfolios mit gleichen Gewichten, gleichen
     Terminen, zufälligen Aktien aus der TOP 200 (p nach Holm < 0,05)
Kosten: Aktien 0,05 %, ETFs 0,02 % je umgeschichtetem Euro. Kurse inkl. Dividenden.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

from ..robustness import holm
from ..universe import DAX40, SP500_ALL
from . import strategies as S
from .engine import backtest, sharpe, stats
from .pairs import pairs_returns
from .panel import load_adjusted

HERE = os.path.dirname(os.path.dirname(__file__))
OUT = os.path.join(HERE, "results", "quant")
START = "2005-01-01"
N_PLACEBO = 100
PERIODS = [("bis 2010", None, "2010-12-31"), ("2011–15", "2011-01-01", "2015-12-31"),
           ("2016–20", "2016-01-01", "2020-12-31"), ("ab 2021", "2021-01-01", None)]
ETF = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "SHY", "AGG", "LQD", "HYG", "GLD",
       "DBC", "VNQ", "BIL"]


def eligible_panel(index, columns) -> pd.DataFrame:
    mem = pd.read_csv(os.path.join(HERE, "results", "top200", "mitglieder.csv"), index_col=0)
    mem.index = pd.PeriodIndex(mem.index, freq="M")
    mem = mem.reindex(columns=columns).fillna(False).astype(bool)
    return mem.reindex(index.to_period("M")).set_axis(index).fillna(False).astype(bool)


def period_sharpes(ret, cash):
    out = []
    for _, a, b in PERIODS:
        r = ret
        if a:
            r = r[r.index >= a]
        if b:
            r = r[r.index <= b]
        out.append(sharpe(r, cash) if len(r) > 200 else np.nan)
    return out


def placebo(targets, close, cash, eligible, cost, rng, n=N_PLACEBO):
    vals = []
    for _ in range(n):
        rows = {}
        for d, w in targets.iterrows():
            nz = w[w != 0]
            pool = eligible.columns[eligible.loc[d].to_numpy()]
            if len(pool) < len(nz):
                continue
            pick = rng.choice(pool, size=len(nz), replace=False)
            new = pd.Series(0.0, index=targets.columns)
            new[pick] = nz.to_numpy()
            rows[d] = new
        r, _ = backtest(pd.DataFrame(rows).T, close, cash, cost, start=targets.index[0])
        vals.append(sharpe(r, cash))
    return np.array(vals)


def main():
    os.makedirs(OUT, exist_ok=True)
    etf = load_adjusted(ETF, "etf")
    pool = load_adjusted(SP500_ALL + DAX40, "pool")
    cal = etf["Close"]["SPY"].dropna().index
    cal = cal[cal >= "2003-01-01"]
    ec = etf["Close"].reindex(cal)
    cash = ec["SHY"].ffill()
    pc = pool["Close"].reindex(cal).ffill(limit=5)
    ph = pool["High"].reindex(cal).ffill(limit=5)
    pl = pool["Low"].reindex(cal).ffill(limit=5)
    elig = eligible_panel(cal, pc.columns) & pc.notna()

    # Vergleichsanlagen
    ew_t = pd.DataFrame({d: elig.loc[d] / elig.loc[d].sum() for d in S.month_ends(cal)}).T
    bench_stock, _ = backtest(ew_t, pc, cash, 0.0005, start=START)
    b6040_t = pd.DataFrame({d: {"SPY": 0.6, "IEF": 0.4} for d in S.month_ends(cal)}).T
    bench_etf, _ = backtest(b6040_t, ec, cash, 0.0002, start=START)
    first = cal[cal >= pd.Timestamp(START)][0]
    spy, _ = backtest(pd.DataFrame({first: {"SPY": 1.0}}).T, ec, cash, 0, start=first)

    stock = {
        "Aktien-Momentum 12-1": (lambda **k: S.momentum(pc, elig, **k), {},
                                 [{"n": 10}, {"n": 40}, {"lookback": 126}, {"lookback": 189}]),
        "Clenow Stocks on the Move": (lambda **k: S.clenow(pc, ph, pl, elig, ec["SPY"], **k), {},
                                      [{"n_days": 60}, {"n_days": 120}, {"top_frac": 0.1}, {"top_frac": 0.3}]),
        "Niedrige Schwankung": (lambda **k: S.low_vol(pc, elig, **k), {},
                                [{"n": 10}, {"n": 40}, {"window": 126}]),
        "Kurzfrist-Umkehr (Wochenverlierer)": (lambda **k: S.reversal(pc, elig, **k), {},
                                               [{"n": 10}, {"n": 40}, {"days": 10}]),
    }
    multi = {
        "Trendfolge Anlageklassen (TSMOM)": (lambda **k: S.tsmom(ec, **k), {},
                                             [{"lookback": 126}, {"lookback": 189}, {"vol_window": 21}]),
        "Dual Momentum GEM": (lambda **k: S.gem(ec, **k), {}, [{"lookback": 126}, {"lookback": 189}]),
        "Risk Parity (All-Weather-Idee)": (lambda **k: S.risk_parity(ec, **k), {},
                                           [{"vol_window": 21}, {"vol_window": 126}]),
        "Monatswechsel-Effekt SPY": (lambda **k: S.turn_of_month(ec, **k), {},
                                     [{"before": 2}, {"after": 2}, {"after": 4}]),
    }
    rows, curves, p_raw = [], {}, {}
    rng = np.random.default_rng(42)

    def evaluate(name, kind, ret, meta, bench, neighbor_rets, plac=None):
        bench = bench[bench.index >= ret.index[0]]      # gleicher Zeitraum
        neighbor_rets = [r[r.index >= ret.index[0]] for r in neighbor_rets]
        bs = sharpe(bench, cash)
        st = stats(ret, cash)
        ps, pb = period_sharpes(ret, cash), period_sharpes(bench, cash)
        better = sum(a > b for a, b in zip(ps, pb) if np.isfinite(a) and np.isfinite(b))
        nb = [sharpe(r, cash) for r in neighbor_rets]
        row = {"strategie": name, "art": kind, **st, **meta,
               "sharpe_vergleich": round(bs, 2),
               "cagr_vergleich_%": stats(bench, cash)["cagr_%"],
               "maxdd_vergleich_%": stats(bench, cash)["max_dd_%"],
               "abschnitte_besser": f"{better}/4",
               "nachbarn_sharpe": " / ".join(f"{x:.2f}" for x in nb),
               "a": st["sharpe"] > bs, "b": better >= 3, "c": all(x > bs for x in nb)}
        if plac is not None:
            row["sharpe_zufall_median"] = round(float(np.median(plac)), 2)
            p_raw[name] = (1 + (plac >= st["sharpe"]).sum()) / (len(plac) + 1)
        rows.append(row)
        curves[name] = ret
        print(f"{name:<38} CAGR {st['cagr_%']:>5} %  Sharpe {st['sharpe']:>5}  DD {st['max_dd_%']:>6} %"
              f"  (Vergleich Sharpe {bs:.2f})", flush=True)

    for name, (fn, base, neigh) in stock.items():
        T = fn(**base)
        st0 = max(pd.Timestamp(START), T.index[0])
        ret, meta = backtest(T, pc, cash, 0.0005, start=st0)
        nrets = [backtest(fn(**k), pc, cash, 0.0005, start=st0)[0] for k in neigh]
        plac = placebo(T, pc, cash, elig, 0.0005, rng)
        evaluate(name, "Aktien", ret, meta, bench_stock, nrets, plac)
    for name, (fn, base, neigh) in multi.items():
        T = fn(**base)
        st0 = max(pd.Timestamp(START), T.index[0])        # ab dem ersten Signal
        ret, meta = backtest(T, ec, cash, 0.0002, start=st0)
        nrets = [backtest(fn(**k), ec, cash, 0.0002, start=st0)[0] for k in neigh]
        evaluate(name, "ETF", ret, meta, bench_etf, nrets)
    pr, pmeta = pairs_returns(pc, elig, cash, start=START)
    nrets = [pairs_returns(pc, elig, cash, start=START, k=1.5)[0],
             pairs_returns(pc, elig, cash, start=START, k=2.5)[0],
             pairs_returns(pc, elig, cash, start=START, n_pairs=40)[0]]
    evaluate("Paarhandel (Gatev et al.)", "Long/Short", pr, pmeta, bench_etf, nrets)

    adj = holm(p_raw)
    for r in rows:
        checks = [r["a"], r["b"], r["c"]]
        if r["strategie"] in adj:
            r["p_zufall_holm"] = round(adj[r["strategie"]], 4)
            checks.append(adj[r["strategie"]] < 0.05)
        r["urteil"] = "robust" if all(checks) else f"nein ({sum(checks)}/{len(checks)})"
    table = pd.DataFrame(rows).drop(columns=["a", "b", "c"])
    for name, ret, bench in [("Vergleich: TOP 200 gleichgewichtet", bench_stock, None),
                             ("Vergleich: 60 % SPY / 40 % IEF", bench_etf, None),
                             ("Vergleich: SPY", spy, None)]:
        table.loc[len(table)] = {"strategie": name, "art": "Vergleich", **stats(ret, cash)}
        curves[name] = ret
    table.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    pd.DataFrame(curves).to_csv(os.path.join(OUT, "returns.csv.gz"))
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
