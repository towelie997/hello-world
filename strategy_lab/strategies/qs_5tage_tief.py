"""5-Tage-Tief mit Zeitstopp (S&P 500) – Quantified Strategies, youtu.be/UkoTdKV65yk
("3 Mean Reversion Strategies (Backtested)", ca. 28.000 Aufrufe), Strategie 3.

Regeln aus dem Video (nur Long): Kauf auf einem 5-Tage-Tief; Verkauf, wenn der Schluss
über dem Vortageshoch liegt oder nach 5 Handelstagen.
Annahmen: "5-Tage-Tief" = Schluss ist der tiefste Schluss der letzten 5 Tage (inkl. heute).
Ein- und Ausstieg zum Schluss. Kein Trendfilter (im Video keiner genannt). KEIN Stop-Loss.
"1 R" = 1 ATR(14). Tageskerzen seit 2005.
Strategien 1 (XLP) und 2 (FXI short, IBS) aus demselben Video: Regeln nur im Bild, nicht
gesprochen -> nicht getestet.
Vergleich: dieselbe Regel ohne Zeitstopp.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "QS 5-Tage-Tief + Zeitstopp (1d)"


def run(symbols, start="2005-01-01", baseline=False, max_days=5):
    trades = []
    name = "Vergleich: 5-Tage-Tief ohne Zeitstopp (1d)" if baseline else NAME
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        c, h = df.Close, df.High
        sig = (c <= c.rolling(5).min()).to_numpy()
        ex = (c > h.shift()).to_numpy()
        C, a = c.to_numpy(), atr(df).to_numpy()
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 20)
        while i < len(df) - 1:
            if not sig[i]:
                i += 1
                continue
            j, why = None, "end"
            for k in range(i + 1, len(df)):
                if ex[k]:
                    j, why = k, "signal"
                    break
                if not baseline and k - i >= max_days:
                    j, why = k, "time"
                    break
            j = len(df) - 1 if j is None else j
            trades.append(make_trade(name, sym, "long", df.index[i], C[i], C[i] - a[i], None,
                                     df.index[j], C[j], why))
            i = j + 1
    return trades
