"""Portfolio-Backtest: Zielgewichte an Umschichtungstagen, dazwischen treiben die Gewichte
mit den Kursen. Entscheidung mit dem Schlusskurs des Umschichtungstags, Handel zu diesem
Schluss (Market-on-Close); erste Rendite ab dem Folgetag. Nicht investiertes Geld
verzinst sich wie SHY (kurze US-Staatsanleihen, Gesamtrendite).

Kosten: je umgeschichtetem Euro `cost` (Standard Aktien 0,05 %, ETFs 0,02 % je Seite).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def backtest(targets: pd.DataFrame, close: pd.DataFrame, cash: pd.Series,
             cost: float = 0.0005, start=None, end=None, cap: bool = True) -> tuple[pd.Series, dict]:
    """targets: Index = Umschichtungstage, Spalten = Symbole, Werte = Zielgewicht
    (NaN = Gewicht unverändert lassen). Gibt tägliche Renditen und Kennzahlen zurück."""
    cols = list(targets.columns)
    px = close.reindex(columns=cols)
    idx = px.index
    if start is not None:
        idx = idx[idx >= pd.Timestamp(start)]
    if end is not None:
        idx = idx[idx <= pd.Timestamp(end)]
    R = px.pct_change(fill_method=None).reindex(idx).to_numpy()
    R = np.nan_to_num(R, nan=0.0)
    c = cash.reindex(idx).pct_change(fill_method=None).fillna(0).to_numpy()
    T = targets.reindex(columns=cols)
    reb = {d: T.loc[d].to_numpy() for d in T.index}
    w = np.zeros(len(cols))
    out = np.zeros(len(idx))
    turnover, n_hold = 0.0, []
    for i, d in enumerate(idx):
        r = R[i]
        port = float(w @ r) + (1 - w.sum()) * c[i]
        if i > 0:
            w = w * (1 + r) / (1 + port) if port > -1 else w * 0
        if d in reb:
            new = np.where(np.isnan(reb[d]), w, reb[d])
            if cap and new.sum() > 1 + 1e-9:
                # ohne Kredit: neu gesetzte Käufe so weit kürzen, dass höchstens 100 % investiert sind
                fresh = ~np.isnan(reb[d]) & (reb[d] > 0) & (reb[d] > w)
                excess = new.sum() - 1
                room = new[fresh].sum()
                if room > 0:
                    new[fresh] *= max(0.0, 1 - excess / room)
            to = float(np.abs(new - w).sum())
            port -= to * cost
            turnover += to
            w = new
        out[i] = port
        n_hold.append(int((np.abs(w) > 1e-9).sum()))
    ret = pd.Series(out, index=idx)
    years = (idx[-1] - idx[0]).days / 365.25
    return ret, {"umschlag_pa": turnover / years, "positionen": float(np.mean(n_hold))}


def stats(ret: pd.Series, cash: pd.Series | None = None) -> dict:
    eq = (1 + ret).cumprod()
    years = (ret.index[-1] - ret.index[0]).days / 365.25
    ex = ret - (cash.reindex(ret.index).pct_change(fill_method=None).fillna(0) if cash is not None else 0)
    yearly = (1 + ret).groupby(ret.index.year).prod() - 1
    last5 = ret[ret.index > ret.index[-1] - pd.DateOffset(years=5)]
    return {
        "cagr_%": round(100 * (eq.iloc[-1] ** (1 / years) - 1), 1),
        "vola_%": round(100 * ret.std() * np.sqrt(252), 1),
        "sharpe": round(float(ex.mean() / ex.std() * np.sqrt(252)), 2) if ex.std() > 0 else np.nan,
        "max_dd_%": round(100 * float((eq / eq.cummax() - 1).min()), 1),
        "schlechtestes_jahr_%": round(100 * float(yearly.min()), 1),
        "jahre_positiv_%": round(100 * float((yearly > 0).mean())),
        "cagr_letzte5_%": round(100 * ((1 + last5).prod() ** (1 / 5) - 1), 1),
    }


def sharpe(ret: pd.Series, cash: pd.Series) -> float:
    ex = ret - cash.reindex(ret.index).pct_change(fill_method=None).fillna(0)
    return float(ex.mean() / ex.std() * np.sqrt(252)) if ex.std() > 0 else np.nan
