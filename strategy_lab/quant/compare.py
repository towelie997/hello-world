"""Fairer Vergleich: Connors RSI(2), Aktien-Momentum (mit/ohne Schutz) und Kombinationen –
alle mit derselben Engine, denselben Aktien (monatliche TOP 200), Kursen inkl. Dividenden,
denselben Kosten. Zusätzlich die Rechnung für ein 5.000-€-Konto (Mindestgebühren).

    python -m strategy_lab.quant.compare        (schreibt results/quant/vergleich_*.csv)

Varianten (vorab festgelegt):
  Connors RSI(2): täglich, Kauf zum Schluss bei Schluss > SMA200 und RSI(2) < 5 (niedrigster
      RSI zuerst), Verkauf bei Schluss > SMA5, höchstens N Positionen je 1/N.
  Momentum 12-1: monatlich die besten N der TOP 200.
  + Marktfilter: Liegt SPY am Monatsende unter seinem 200-Tage-Schnitt, ganz in den Geldmarkt.
  + Schwankungssteuerung (Barroso & Santa-Clara 2015): Anteil im Momentum-Portfolio =
      min(1, 18 % / Schwankung der Strategie der letzten 126 Tage), Rest Geldmarkt.
  Kombinationen: 50 % Momentum + 50 % Connors, monatlich auf 50/50 zurückgesetzt.
Bewertung wie run.py: a) Sharpe > TOP 200 gleichgewichtet, b) ≥ 3/4 Zeitabschnitte besser,
c) Nachbar-Parameter besser.
5.000-€-Konto: Kosten je Order = 0,02 % Spread + 0,50 $ Mindestgebühr / Ordergröße
(Ordergröße ≈ 5.500 $ / N) – mit wachsendem Konto würde das kleiner.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

from ..engine import rsi
from . import strategies as S
from .engine import backtest, sharpe, stats
from .run import OUT, PERIODS, START, eligible_panel, period_sharpes
from .panel import load_adjusted
from .run import ETF
from ..universe import DAX40, SP500_ALL


def connors_targets(close, eligible, n=20, rsi_max=5.0, start=START):
    sma200 = close.rolling(200).mean()
    sma5 = close.rolling(5).mean()
    r2 = rsi(close, 2)
    C, A, B, R, E = (x.to_numpy() for x in (close, sma200, sma5, r2, eligible))
    cols = close.columns
    rows, held = {}, set()
    first = int(np.searchsorted(close.index, pd.Timestamp(start)))
    for i in range(first, len(close.index)):
        change = {}
        for j in list(held):
            if np.isfinite(C[i, j]) and C[i, j] > B[i, j]:
                change[j] = 0.0
                held.discard(j)
        free = n - len(held)
        if free > 0:
            ok = E[i] & (C[i] > A[i]) & (R[i] < rsi_max)
            cand = [j for j in np.flatnonzero(ok) if j not in held]
            cand.sort(key=lambda j: R[i, j])
            for j in cand[:free]:
                change[j] = 1.0 / n
                held.add(j)
        if change:
            w = np.full(len(cols), np.nan)
            for j, v in change.items():
                w[j] = v
            rows[close.index[i]] = w
    return pd.DataFrame.from_dict(rows, orient="index", columns=cols)


def market_filter(targets, index_close):
    ok = index_close > index_close.rolling(200).mean()
    t = targets.copy()
    t.loc[~ok.reindex(t.index).fillna(False).to_numpy()] = 0.0
    return t


def vol_scale(ret, cash, target=0.18, window=126):
    """Barroso/Santa-Clara: monatlich Anteil = min(1, Ziel/realisierte Schwankung)."""
    c = cash.reindex(ret.index).pct_change(fill_method=None).fillna(0)
    vol = ret.rolling(window).std() * np.sqrt(252)
    ends = S.month_ends(ret.index)
    expo = pd.Series(np.nan, index=ret.index)
    expo.loc[ends] = np.minimum(1.0, target / vol.loc[ends])
    expo = expo.shift(1).ffill().fillna(1.0)          # gilt ab dem Folgetag
    return expo * ret + (1 - expo) * c


def combine(rets: list[pd.Series], weights: list[float]) -> pd.Series:
    """Teilportfolios, monatlich auf die Zielanteile zurückgesetzt."""
    df = pd.concat(rets, axis=1).dropna()
    ends = set(S.month_ends(df.index))
    v = np.array(weights, dtype=float)
    out = []
    for d, row in zip(df.index, df.to_numpy()):
        total_before = v.sum()
        v = v * (1 + row)
        out.append(v.sum() / total_before - 1)
        if d in ends:
            v = v.sum() * np.array(weights)
    return pd.Series(out, index=df.index)


def small_cost(n, account_usd=5500.0, min_fee=0.5, spread=0.0002):
    return spread + min_fee / (account_usd / n)


def main():
    os.makedirs(OUT, exist_ok=True)
    etf = load_adjusted(ETF, "etf")
    pool = load_adjusted(SP500_ALL + DAX40, "pool")
    cal = etf["Close"]["SPY"].dropna().index
    cal = cal[cal >= "2003-01-01"]
    ec = etf["Close"].reindex(cal)
    cash = ec["SHY"].ffill()
    pc = pool["Close"].reindex(cal).ffill(limit=5)
    elig = eligible_panel(cal, pc.columns, pit=True) & pc.notna()
    ew_t = pd.DataFrame({d: elig.loc[d] / elig.loc[d].sum() for d in S.month_ends(cal)}).T
    bench, _ = backtest(ew_t, pc, cash, 0.0005, start=START)
    spy_first = cal[cal >= pd.Timestamp(START)][0]
    spy, _ = backtest(pd.DataFrame({spy_first: {"SPY": 1.0}}).T, ec, cash, 0, start=spy_first)

    cache = {}

    def mom(n=20, filt=False, cost=0.0005, lookback=252):
        key = ("mom", n, filt, cost, lookback)
        if key not in cache:
            T = S.momentum(pc, elig, n=n, lookback=lookback)
            if filt:
                T = market_filter(T, ec["SPY"])
            cache[key] = backtest(T, pc, cash, cost, start=START)[0]
        return cache[key]

    def con(n=20, cost=0.0005, rsi_max=5.0):
        key = ("con", n, cost, rsi_max)
        if key not in cache:
            T = connors_targets(pc, elig, n=n, rsi_max=rsi_max)
            cache[key] = backtest(T, pc, cash, cost, start=START)[0]
        return cache[key]

    def momvol(n=20, cost=0.0005, target=0.18):
        return vol_scale(mom(n, cost=cost), cash, target)

    variants = {
        "Connors RSI(2), 20 Pos.": (lambda: con(20), [lambda: con(10), lambda: con(40), lambda: con(20, rsi_max=10)]),
        "Momentum 12-1, 20 Pos.": (lambda: mom(20), [lambda: mom(10), lambda: mom(40), lambda: mom(20, lookback=189)]),
        "Momentum + Marktfilter": (lambda: mom(20, True), [lambda: mom(10, True), lambda: mom(40, True)]),
        "Momentum + Schwankungssteuerung": (lambda: momvol(20), [lambda: momvol(20, target=0.12), lambda: momvol(20, target=0.24)]),
        "50 % Momentum + 50 % Connors": (lambda: combine([mom(20), con(20)], [0.5, 0.5]),
                                          [lambda: combine([mom(20), con(20)], [0.3, 0.7]),
                                           lambda: combine([mom(20), con(20)], [0.7, 0.3])]),
        "50 % Momentum+Filter + 50 % Connors": (lambda: combine([mom(20, True), con(20)], [0.5, 0.5]),
                                                 [lambda: combine([mom(20, True), con(20)], [0.3, 0.7]),
                                                  lambda: combine([mom(20, True), con(20)], [0.7, 0.3])]),
    }
    rows, curves = [], {}
    bs = sharpe(bench, cash)
    pb = period_sharpes(bench, cash)
    for name, (fn, neigh) in variants.items():
        ret = fn()
        ret = ret[ret.index >= START]
        st = stats(ret, cash)
        ps = period_sharpes(ret, cash)
        better = sum(a > b for a, b in zip(ps, pb))
        nb = [sharpe(f(), cash) for f in neigh]
        corr = None
        checks = [st["sharpe"] > bs, better >= 3, all(x > bs for x in nb)]
        rows.append({"variante": name, **st, "abschnitte_besser": f"{better}/4",
                     "nachbarn_sharpe": " / ".join(f"{x:.2f}" for x in nb),
                     "jahr_2008_%": round(100 * float((1 + ret[ret.index.year == 2008]).prod() - 1), 1),
                     "jahr_2022_%": round(100 * float((1 + ret[ret.index.year == 2022]).prod() - 1), 1),
                     "urteil": "robust" if all(checks) else f"nein ({sum(checks)}/3)"})
        curves[name] = ret
        print(f"{name:<40} CAGR {st['cagr_%']:>5} %  Sharpe {st['sharpe']:>5}  DD {st['max_dd_%']:>6} %", flush=True)
    for name, ret in [("Vergleich: TOP 200 gleichgewichtet", bench), ("Vergleich: SPY", spy)]:
        st = stats(ret, cash)
        rows.append({"variante": name, **st,
                     "jahr_2008_%": round(100 * float((1 + ret[ret.index.year == 2008]).prod() - 1), 1),
                     "jahr_2022_%": round(100 * float((1 + ret[ret.index.year == 2022]).prod() - 1), 1)})
        curves[name] = ret
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "vergleich_fair.csv"), index=False)  # Stichtags-Universum
    pd.DataFrame(curves).to_csv(os.path.join(OUT, "vergleich_returns.csv.gz"))
    corr = pd.DataFrame({"Momentum": mom(20), "Connors": con(20)}).corr().iloc[0, 1]
    print(f"Korrelation Momentum/Connors (tägl.): {corr:.2f}")

    # 5.000-€-Konto: Mindestgebühren je Order
    small = []
    for n in (3, 5, 10, 20):
        c = small_cost(n)
        for name, fn in [("Connors RSI(2)", lambda: con(n, cost=c)),
                         ("Momentum 12-1", lambda: mom(n, cost=c)),
                         ("Momentum + Marktfilter", lambda: mom(n, True, cost=c)),
                         ("50/50 Momentum+Filter / Connors",
                          lambda: combine([mom(n, True, cost=c), con(n, cost=c)], [0.5, 0.5]))]:
            r = fn()
            st = stats(r[r.index >= START], cash)
            small.append({"positionen": n, "kosten_je_order_%": round(100 * c, 3), "variante": name, **st})
    pd.DataFrame(small).to_csv(os.path.join(OUT, "vergleich_5000eur.csv"), index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(pd.DataFrame(rows).to_string(index=False))
        print(pd.DataFrame(small).to_string(index=False))


if __name__ == "__main__":
    main()
