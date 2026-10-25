"""Bollinger Band + RSI – TradingLab, youtu.be/pCmJ8wsAS_w

Regeln aus dem Video:
  * Bollinger-Bänder: Länge 30, 2 Standardabweichungen. RSI Länge 13.
  * Long: Kurs unter dem unteren Band UND RSI unter 25.
  * Short: Kurs über dem oberen Band UND RSI über 75.
  * Ziel: Rückkehr zum Mittelwert (mittlere Linie = 30er-Durchschnitt).
Annahmen (im Video nicht festgelegt):
  * Signal und Einstieg zum Schlusskurs; Ausstieg, sobald der Schluss die Mittellinie
    erreicht (Long: Schluss >= Mittellinie).
  * KEIN Stop-Loss im Video. "1 R" = 1 ATR(14) (nur Rechengröße).
  * Weggelassen, weil Ermessen: "keine engen Bänder / Seitwärtsphase" und Divergenzen.
  * Zeitebene nicht genannt – Tageskerzen seit 2005 (Swing).
Vergleich: nur die Bollinger-Bedingung, ohne RSI.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade, rsi

NAME = "TradingLab Bollinger + RSI"


def run(symbols, start="2005-01-01", longs=True, shorts=True, baseline=False):
    trades = []
    if baseline:
        name = "Vergleich: nur Bollinger 30 (1d)"
    else:
        name = f"{NAME} (1d{'' if shorts else ', nur Long'})"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        c = df.Close
        mid = c.rolling(30).mean()
        sd = c.rolling(30).std(ddof=0)
        lo, up = (mid - 2 * sd).to_numpy(), (mid + 2 * sd).to_numpy()
        r = rsi(c, 13).to_numpy()
        C, M = c.to_numpy(), mid.to_numpy()
        a = atr(df).to_numpy()
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 31)
        while i < len(df) - 1:
            side = 0
            if longs and C[i] < lo[i] and (baseline or r[i] < 25):
                side = 1
            elif shorts and C[i] > up[i] and (baseline or r[i] > 75):
                side = -1
            if side == 0:
                i += 1
                continue
            j = next((k for k in range(i + 1, len(df))
                      if (side == 1 and C[k] >= M[k]) or (side == -1 and C[k] <= M[k])), None)
            why = "target" if j is not None else "end"
            j = len(df) - 1 if j is None else j
            trades.append(make_trade(name, sym, "long" if side == 1 else "short", df.index[i],
                                     C[i], C[i] - side * a[i], None, df.index[j], C[j], why))
            i = j + 1
    return trades
