"""Connors Double 7s – StatOasis (Ali Casey), youtu.be/2CwM3u_8daY ("Best Mean Reversion
Strategy // Connor's Double 7s", ca. 42.000 Aufrufe); Original: Connors & Alvarez,
"Short Term Trading Strategies That Work" (2008).

Regeln aus dem Video (nur Long, alles zum Schlusskurs):
  Kauf:    Schluss < tiefster Schluss der 6 Vortage (= 7-Tage-Tief auf Schlusskursbasis)
           und Schluss > SMA(200).
  Verkauf: Schluss > höchster Schluss der 6 Vortage (= 7-Tage-Hoch).
  KEIN Stop-Loss, kein Kursziel (ausdrücklich im Video). "1 R" = 1 ATR(14) (Rechengröße).
Tageskerzen seit 2005. Vergleich: "roter Tag > SMA200" (connors_rsi2.py) und Double 5 aus
qs_connors6.py (gleiche Idee mit 5 Tagen).
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "Connors Double 7s (1d)"


def run(symbols, start="2005-01-01", n=7):
    trades = []
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 250:
            continue
        c = df.Close
        prev = c.shift()
        sig = ((c < prev.rolling(n - 1).min()) & (c > c.rolling(200).mean())).to_numpy()
        ex = (c > prev.rolling(n - 1).max()).to_numpy()
        C, a = c.to_numpy(), atr(df).to_numpy()
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 200)
        while i < len(df) - 1:
            if not sig[i]:
                i += 1
                continue
            j = next((k for k in range(i + 1, len(df)) if ex[k]), None)
            why = "signal" if j is not None else "end"
            j = len(df) - 1 if j is None else j
            trades.append(make_trade(NAME, sym, "long", df.index[i], C[i], C[i] - a[i], None,
                                     df.index[j], C[j], why))
            i = j + 1
    return trades
