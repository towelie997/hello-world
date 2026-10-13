"""Connors RSI(2) als echtes Portfolio mit Kapitalgrenze – alle aktuellen S&P-500-Werte.

    python -m strategy_lab.portfolio      (schreibt results/portfolio/)

Bisher zählte jeder Trade einzeln, als gäbe es unbegrenzt Kapital. Hier gilt:
  * Startkapital 100 (Ergebnisse in %), höchstens N Positionen gleichzeitig,
    jede neue Position = 1/N des aktuellen Depotwerts (sonst Barbestand ohne Zins).
  * Täglich zum Schluss: erst Verkäufe (Schluss > SMA5), dann Käufe. Kandidaten:
    Schluss > SMA200 und RSI(2) < 5, nicht im Depot. Bei mehr Kandidaten als freien
    Plätzen: niedrigster RSI(2) zuerst (Kontrolle: zufällige Reihenfolge).
  * Optionaler Stop 10 % unter Einstieg, geprüft über das Tagestief ab dem Folgetag,
    Kurslücke -> Füllung zur Eröffnung.
  * Kosten 0,01 % je Seite wie im Strategy Lab; Kontrolle mit 0,05 % je Seite.
Varianten (vorab festgelegt): N = 5 / 10 / 20, ohne Stop / Stop 10 %.
Vergleich: gleichgewichtetes Kaufen-und-Halten DERSELBEN Werte (täglich ausgeglichen) –
fairer als der S&P 500, weil es denselben Survivorship-Bias hat – sowie SPY.
Grenze: heutige Indexmitglieder seit 2005 -> Survivorship-Bias, Ergebnisse zu günstig.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

from . import data
from .engine import rsi
from .universe import SP500_ALL

OUT = os.path.join(os.path.dirname(__file__), "results", "portfolio")
START = "2005-01-01"


def load_panel(symbols):
    frames = {s: data.load(s, "1d", "max") for s in symbols}
    frames = {s: f for s, f in frames.items() if len(f) >= 250}
    idx = data.load("SPY", "1d", "max").index
    idx = idx[idx >= "2003-01-01"]
    get = lambda col: pd.DataFrame({s: f[col] for s, f in frames.items()}).reindex(idx)
    o, l, c = get("Open"), get("Low"), get("Close")
    full = pd.DataFrame({s: f.Close for s, f in frames.items()})
    ind = {
        "sma200": full.rolling(200).mean().reindex(idx),
        "sma5": full.rolling(5).mean().reindex(idx),
        "rsi2": full.apply(lambda x: rsi(x.dropna(), 2)).reindex(idx),
    }
    return idx, o, l, c, ind


def simulate(idx, o, l, c, ind, n_max=10, stop_pct=None, cost=0.0001, rank="rsi", seed=0):
    rng = np.random.default_rng(seed)
    syms = np.array(c.columns)
    O, L, C = o.to_numpy(), l.to_numpy(), c.to_numpy()
    S200, S5, R2 = ind["sma200"].to_numpy(), ind["sma5"].to_numpy(), ind["rsi2"].to_numpy()
    cash, pos = 100.0, {}            # pos: spalte -> [stück, einstieg, stop, datum]
    equity, trades = [], []
    first = int(np.searchsorted(idx, pd.Timestamp(START)))
    for t in range(first, len(idx)):
        # 1) Stops im Tagesverlauf
        if stop_pct:
            for j in list(pos):
                sh, ep, st, d0 = pos[j]
                if not np.isnan(L[t, j]) and L[t, j] <= st:
                    px = min(st, O[t, j]) if not np.isnan(O[t, j]) else st
                    cash += sh * px * (1 - cost)
                    trades.append((syms[j], d0, idx[t], ep, px, "stop"))
                    del pos[j]
        # 2) Verkäufe zum Schluss
        for j in list(pos):
            if not np.isnan(C[t, j]) and C[t, j] > S5[t, j]:
                sh, ep, st, d0 = pos.pop(j)
                cash += sh * C[t, j] * (1 - cost)
                trades.append((syms[j], d0, idx[t], ep, C[t, j], "signal"))
        value = cash + sum(sh * (C[t, j] if not np.isnan(C[t, j]) else ep)
                           for j, (sh, ep, st, d0) in pos.items())
        # 3) Käufe zum Schluss
        free = n_max - len(pos)
        if free > 0:
            cand = np.flatnonzero((C[t] > S200[t]) & (R2[t] < 5))
            cand = [j for j in cand if j not in pos]
            if cand:
                order = np.argsort(R2[t, cand]) if rank == "rsi" else rng.permutation(len(cand))
                for k in order[:free]:
                    j = cand[k]
                    budget = min(value / n_max, cash)
                    if budget <= 0:
                        break
                    sh = budget / (C[t, j] * (1 + cost))
                    cash -= budget
                    pos[j] = [sh, C[t, j], C[t, j] * (1 - stop_pct) if stop_pct else -np.inf, idx[t]]
        equity.append(cash + sum(sh * (C[t, j] if not np.isnan(C[t, j]) else ep)
                                 for j, (sh, ep, st, d0) in pos.items()))
    eq = pd.Series(equity, index=idx[first:])
    tr = pd.DataFrame(trades, columns=["symbol", "entry", "exit", "entry_px", "exit_px", "reason"])
    tr["pct"] = 100 * ((tr.exit_px * (1 - cost)) / (tr.entry_px * (1 + cost)) - 1)
    return eq, tr


def stats(eq: pd.Series, exposure=None) -> dict:
    r = eq.pct_change().dropna()
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    dd = eq / eq.cummax() - 1
    yearly = eq.resample("YE").last().pct_change()
    yearly.iloc[0] = eq.resample("YE").last().iloc[0] / eq.iloc[0] - 1
    last5 = eq[eq.index >= eq.index[-1] - pd.DateOffset(years=5)]
    out = {
        "cagr_%": round(100 * ((eq.iloc[-1] / eq.iloc[0]) ** (1 / years) - 1), 1),
        "gesamt_%": round(100 * (eq.iloc[-1] / eq.iloc[0] - 1)),
        "max_dd_%": round(100 * dd.min(), 1),
        "sharpe": round(float(r.mean() / r.std() * np.sqrt(252)), 2),
        "schlechtestes_jahr_%": round(100 * yearly.min(), 1),
        "jahre_positiv_%": round(100 * (yearly > 0).mean()),
        "cagr_letzte5_%": round(100 * ((last5.iloc[-1] / last5.iloc[0]) ** (1 / 5) - 1), 1),
        "jahr_2008_%": round(100 * yearly.get(pd.Timestamp("2008-12-31"), np.nan), 1),
        "jahr_2022_%": round(100 * yearly.get(pd.Timestamp("2022-12-31"), np.nan), 1),
    }
    if exposure is not None:
        out["investiert_%"] = round(exposure, 0)
    return out, yearly


def main():
    os.makedirs(OUT, exist_ok=True)
    idx, o, l, c, ind = load_panel(SP500_ALL)
    print(f"{c.shape[1]} Werte, {idx[0].date()}–{idx[-1].date()}", flush=True)
    rows, curves, yearly_all = [], {}, {}
    variants = [(n, s, 0.0001, "rsi") for n in (5, 10, 20) for s in (None, 0.10)]
    variants += [(10, None, 0.0005, "rsi"), (10, None, 0.0001, "zufall")]
    for n, s, cost, rank in variants:
        label = f"N={n}, {'Stop 10 %' if s else 'ohne Stop'}"
        if cost != 0.0001:
            label += ", Kosten 0,05 %"
        if rank != "rsi":
            label += ", zufällige Auswahl"
        eq, tr = simulate(idx, o, l, c, ind, n, s, cost, rank)
        held = tr.assign(d=(tr.exit - tr.entry).dt.days)
        exposure = 100 * held.d.sum() / (n * (eq.index[-1] - eq.index[0]).days)
        st, yr = stats(eq, exposure)
        rows.append({"variante": label, **st, "trades": len(tr),
                     "treffer_%": round(100 * (tr.pct > 0).mean(), 1),
                     "avg_trade_%": round(tr.pct.mean(), 2)})
        curves[label], yearly_all[label] = eq, yr
        tr.to_csv(os.path.join(OUT, f"trades_N{n}_{'stop10' if s else 'nostop'}_{rank}_{int(cost*1e4)}bp.csv.gz"), index=False)
        print(f"{label:<40} CAGR {st['cagr_%']:>5} %  DD {st['max_dd_%']:>6} %", flush=True)
    # Vergleiche
    ret = c.pct_change(fill_method=None)
    ew = (1 + ret[ret.index >= START].mean(axis=1).fillna(0)).cumprod() * 100
    spy = data.load("SPY", "1d", "max").Close
    spy = spy[spy.index >= START] / spy[spy.index >= START].iloc[0] * 100
    for label, eq in [("Vergleich: gleichgewichtet halten (gleiche Werte)", ew),
                      ("Vergleich: SPY halten (Kurs, ohne Dividenden)", spy)]:
        st, yr = stats(eq, 100)
        rows.append({"variante": label, **st})
        curves[label], yearly_all[label] = eq, yr
    table = pd.DataFrame(rows)
    table.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    pd.DataFrame(curves).to_csv(os.path.join(OUT, "equity.csv.gz"))
    yt = pd.DataFrame(yearly_all)
    yt.index = yt.index.year
    (100 * yt).round(1).to_csv(os.path.join(OUT, "yearly.csv"))
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
