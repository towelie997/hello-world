"""Paarhandel nach Gatev, Goetzmann & Rouwenhorst (2006), "Pairs Trading:
Performance of a Relative-Value Arbitrage Rule" – Klassiker der statistischen Arbitrage.

Regeln aus dem Aufsatz:
  * Bildungsphase 12 Monate: Kurse (Gesamtrendite) auf 1 normiert, für alle Paare die
    Summe der quadrierten Abstände (SSD); die 20 Paare mit der kleinsten SSD.
  * Handelsphase 6 Monate: Abstand der neu normierten Kurse; weicht er um mehr als
    2 Standardabweichungen (aus der Bildungsphase) ab: Verlierer kaufen, Gewinner leer
    verkaufen. Schließen, wenn sich die Kurse kreuzen, spätestens am Ende der Phase.
  * Ertrag auf das gebundene Kapital: jedes Paar bekommt 1/20; Long- und Short-Seite je
    1/20 (Brutto 2/20). Kapital ohne offene Paare verzinst sich wie SHY.
Annahmen: neue Bildungsphase alle 6 Monate (nicht überlappend, im Aufsatz monatlich
gestaffelt). Universum: US-Werte der TOP 200 zu Beginn der Handelsphase. Kosten je Seite
und Bein; zusätzlich 0,25 % p. a. Leihgebühr auf die Short-Seite.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def pairs_returns(close: pd.DataFrame, eligible: pd.DataFrame, cash: pd.Series,
                  start="2005-01-01", n_pairs=20, form=252, trade=126, k=2.0,
                  cost=0.0005, borrow_pa=0.0025) -> tuple[pd.Series, dict]:
    idx = close.index[close.index >= pd.Timestamp(start) - pd.Timedelta(days=400)]
    px = close.reindex(idx)
    cash_r = cash.reindex(idx).pct_change(fill_method=None).fillna(0).to_numpy()
    rets = px.pct_change(fill_method=None).to_numpy()
    first = int(np.searchsorted(idx, pd.Timestamp(start)))
    out = np.zeros(len(idx))
    n_trades = 0
    t0 = first
    while t0 + 1 < len(idx):
        f0 = t0 - form
        elig = eligible.loc[idx[t0]]
        cols = [c for c in px.columns if elig.get(c, False) and not c.endswith(".DE")]
        F = px.iloc[f0:t0 + 1][cols]
        F = F.loc[:, F.notna().all()]
        if F.shape[1] < 40:
            t0 += trade
            continue
        norm = (F / F.iloc[0]).to_numpy()
        # SSD aller Paare über ||a-b||² = |a|² + |b|² - 2ab
        sq = (norm ** 2).sum(axis=0)
        ssd = sq[:, None] + sq[None, :] - 2 * norm.T @ norm
        iu = np.triu_indices(len(sq), 1)
        order = np.argsort(ssd[iu])[:n_pairs]
        names = list(F.columns)
        pairs = [(iu[0][o], iu[1][o]) for o in order]
        sigma = [np.std(norm[:, a] - norm[:, b]) for a, b in pairs]
        col_idx = [px.columns.get_loc(n) for n in names]
        t_end = min(t0 + trade, len(idx) - 1)
        P = px.iloc[t0:t_end + 1, [col_idx[a] for a, b in pairs] + [col_idx[b] for a, b in pairs]].to_numpy()
        P = P / P[0]
        state = np.zeros(n_pairs)              # +1: long a / short b, -1: umgekehrt
        for j in range(1, P.shape[0]):
            t = t0 + j
            day = 0.0
            invested = 0
            for p_i, (a, b) in enumerate(pairs):
                ra = rets[t, col_idx[a]]
                rb = rets[t, col_idx[b]]
                ra = 0.0 if np.isnan(ra) else ra
                rb = 0.0 if np.isnan(rb) else rb
                if state[p_i] != 0:
                    day += state[p_i] * (ra - rb) / n_pairs
                    day -= borrow_pa / 252 / n_pairs
                    invested += 1
                spread = P[j, p_i] - P[j, n_pairs + p_i]
                last = j == P.shape[0] - 1
                if state[p_i] == 0 and not last and abs(spread) > k * sigma[p_i]:
                    state[p_i] = -np.sign(spread)      # teureres Papier leer verkaufen
                    day -= 2 * cost / n_pairs
                    n_trades += 1
                elif state[p_i] != 0 and (np.sign(spread) == state[p_i] or spread == 0 or last):
                    state[p_i] = 0
                    day -= 2 * cost / n_pairs
            out[t] = day + cash_r[t]           # Kapital bleibt im Geldmarkt (Short-Erlös deckt Long)
        t0 = t_end
    ret = pd.Series(out, index=idx).iloc[first:]
    years = (ret.index[-1] - ret.index[0]).days / 365.25
    return ret, {"umschlag_pa": n_trades * 4 / n_pairs / years, "positionen": float(n_pairs * 2)}
