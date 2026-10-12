"""3 Swing-Strategien für den S&P 500 – Quantified Strategies, youtu.be/lKzoUptU2io

Regeln aus dem Video (nur Long, Einstieg und Ausstieg jeweils zum Schlusskurs):
  1. Heute ist Montag und es ist der zweite Tag in Folge mit tieferem Schluss.
  2. Schluss markiert ein neues 5-Tage-Tief und IBS < 0,25.
  3. Heutiges Hoch liegt unter dem 10-Tage-Hoch der Vortage und IBS < 0,15.
  Ausstieg (alle): Schluss über dem Vortageshoch.
  IBS = (Schluss - Tief) / (Hoch - Tief).
  KEIN Stop-Loss im Video.
Annahmen: Regel 3 wörtlich umgesetzt (Hoch < höchstes Hoch der 10 Vortage). Die drei
Regeln laufen zusammen als ein Portfolio (eine Position pro Wert, erstes Signal zählt).
"1 R" ist nur eine Rechengröße: 1 ATR(14) beim Einstieg. Getestet auf SPY (wie im
Video) und der ganzen SWING-Liste. Tageskerzen seit 2005.
Vergleich: Kauf nach jedem roten Tag, gleicher Ausstieg.
"""

import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "QS 3 Swing-Regeln"


def run(symbols, start="2005-01-01", baseline=False, label=""):
    trades = []
    name = f"Vergleich: Kauf nach rotem Tag{label}" if baseline else f"{NAME}{label}"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 50:
            continue
        o, h, l, c = df.Open, df.High, df.Low, df.Close
        ibs = ((c - l) / (h - l)).fillna(0.5)
        down = c < c.shift()
        r1 = (df.index.dayofweek == 0) & down & down.shift(fill_value=False)
        r2 = (c <= c.rolling(5).min()) & (ibs < 0.25)
        r3 = (h < h.shift().rolling(10).max()) & (ibs < 0.15)
        sig = down if baseline else (r1 | r2 | r3)
        a = atr(df)
        i = 15
        while i < len(df) - 1:
            if df.index[i] < pd.Timestamp(start) or not sig.iloc[i]:
                i += 1
                continue
            entry = c.iloc[i]
            j = next((k for k in range(i + 1, len(df)) if c.iloc[k] > h.iloc[k - 1]), None)
            why = "signal" if j is not None else "end"
            j = len(df) - 1 if j is None else j
            trades.append(make_trade(name, sym, "long", df.index[i], entry,
                                     entry - a.iloc[i], None, df.index[j], c.iloc[j], why))
            i = j + 1
    return trades
