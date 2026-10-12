"""Connors RSI(2) – Larry Connors & Cesar Alvarez, "Short Term Trading Strategies
That Work" (2008), Kapitel RSI(2)

Regeln aus dem Buch (nur Long):
  * Schluss über dem 200-Tage-Durchschnitt (SMA200).
  * RSI(2) schließt unter 5 -> Kauf zum Schlusskurs.
  * Ausstieg zum Schlusskurs, sobald der Schluss über dem 5-Tage-Durchschnitt liegt.
  * KEIN Stop-Loss im Original (Connors lehnt Stops für diese Strategie ab).
Annahmen: Da es keinen Stop gibt, ist "1 R" hier nur eine Rechengröße: 1 ATR(14)
beim Einstieg. Eine Position pro Wert. Tageskerzen seit 2005.
Vergleich: Kauf nach jedem roten Tag über dem SMA200, gleicher Ausstieg.
"""

import pandas as pd

from .. import data
from ..engine import atr, make_trade, rsi

NAME = "Connors RSI(2)"


def run(symbols, start="2005-01-01", threshold=5, baseline=False):
    trades = []
    name = "Vergleich: roter Tag > SMA200 (1d)" if baseline else f"{NAME} (1d)"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 250:
            continue
        c = df.Close
        sma200, sma5, r2, a = c.rolling(200).mean(), c.rolling(5).mean(), rsi(c, 2), atr(df)
        i = 200
        while i < len(df) - 1:
            if df.index[i] < pd.Timestamp(start):
                i += 1
                continue
            signal = (c.iloc[i] < c.iloc[i - 1]) if baseline else (r2.iloc[i] < threshold)
            if signal and c.iloc[i] > sma200.iloc[i]:
                entry = c.iloc[i]
                j = next((k for k in range(i + 1, len(df)) if c.iloc[k] > sma5.iloc[k]), None)
                why = "signal" if j is not None else "end"
                j = len(df) - 1 if j is None else j
                trades.append(make_trade(name, sym, "long", df.index[i], entry,
                                         entry - a.iloc[i], None, df.index[j], c.iloc[j], why))
                i = j + 1
                continue
            i += 1
    return trades
