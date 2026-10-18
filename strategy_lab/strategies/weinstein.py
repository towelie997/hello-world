"""Stan Weinstein Stufe-2-Methode (Wochenkerzen) – Trade With Trend, youtu.be/Ux_uuOj-gKs
(nach Stan Weinstein, "Secrets for Profiting in Bull and Bear Markets", 1988)

Regeln aus dem Video (nur Long):
  * Kurs über dem 50-Wochen-Durchschnitt (Weinstein selbst: 30 Wochen).
  * Relative Stärke (Kurs / S&P 500) steigt: über ihrem eigenen 50-Wochen-Durchschnitt.
  * Kurs bricht über einen Widerstand aus ("Stufe 2"); nur liquide Werte (Top 200–300).
Annahmen (im Video nicht genau festgelegt):
  * Widerstand = höchstes Hoch der 26 Vorwochen; Einstieg zum Wochenschluss des Ausbruchs.
  * Stufe 2 zusätzlich: 50-Wochen-Durchschnitt steigt (höher als vor 4 Wochen) – Weinsteins
    Definition aus dem Buch.
  * Ausstieg wie im Buch beschrieben: Wochenschluss unter dem 50-Wochen-Durchschnitt.
  * Anfangs-Stop für R: tiefstes Tief der 10 Vorwochen; wird er unter der Woche
    unterschritten, Verkauf am Stop (Kurslücke: Eröffnung).
Vergleich: dieselben Regeln ohne relative Stärke.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import make_trade
from .squeeze_swing import _weekly

NAME = "Weinstein Stufe 2 (1w)"


def run(symbols, start="2005-01-01", ma=50, breakout=26, baseline=False):
    trades = []
    name = "Vergleich: Stufe 2 ohne rel. Stärke (1w)" if baseline else NAME
    spy = _weekly(data.load("SPY", "1d", "max")).Close
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if df.empty:
            continue
        w = _weekly(df)
        if len(w) < ma + 30:
            continue
        o, h, l, c = (w[k].to_numpy() for k in ("Open", "High", "Low", "Close"))
        sma = w.Close.rolling(ma).mean()
        rs = w.Close / spy.reindex(w.index).ffill()
        rs_ok = (rs > rs.rolling(ma).mean()).to_numpy()
        rising = (sma > sma.shift(4)).to_numpy()
        res = w.High.shift().rolling(breakout).max().to_numpy()
        low10 = w.Low.shift().rolling(10).min().to_numpy()
        s = sma.to_numpy()
        i = max(int(np.searchsorted(w.index, pd.Timestamp(start))), ma + 5)
        while i < len(w) - 1:
            ok = c[i] > s[i] and rising[i] and c[i] > res[i] and (baseline or rs_ok[i])
            if not ok or not np.isfinite(low10[i]) or low10[i] >= c[i]:
                i += 1
                continue
            entry, stop = c[i], low10[i]
            exit_t, px, why = None, None, None
            for j in range(i + 1, len(w)):
                if l[j] <= stop:
                    exit_t, px, why = j, min(stop, o[j]), "stop"
                    break
                if c[j] < s[j]:
                    exit_t, px, why = j, c[j], "signal"
                    break
            if exit_t is None:
                exit_t, px, why = len(w) - 1, c[-1], "end"
            trades.append(make_trade(name, sym, "long", w.index[i], entry, stop, None,
                                     w.index[exit_t], px, why))
            i = exit_t + 1
    return trades
