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

Stop-Varianten (nicht im Original, siehe connors_stops.py): stop=("pct", 0.05) Stop 5 %
unter Einstieg, ("atr", 2) Stop 2 ATR(14) unter Einstieg, ("days", 10) Zeit-Stop: Verkauf
zum Schluss nach 10 Handelstagen. Preis-Stops ab dem Folgetag über das Tagestief geprüft,
Kurslücke unter den Stop -> Füllung zur Eröffnung. Der reguläre Ausstieg (Schluss > SMA5)
bleibt immer aktiv. "1 R" bleibt 1 ATR(14), damit alle Varianten vergleichbar sind.
"""

import pandas as pd

from .. import data
from ..engine import atr, make_trade, rsi

NAME = "Connors RSI(2)"


def _exit(df, i, sma5, a, stop):
    """(Index, Preis, Grund) des Ausstiegs für einen Einstieg zum Schluss von Kerze i."""
    o, l, c = df.Open.to_numpy(), df.Low.to_numpy(), df.Close.to_numpy()
    kind, val = stop if stop else (None, None)
    level = None
    if kind == "pct":
        level = c[i] * (1 - val)
    elif kind == "atr":
        level = c[i] - val * a.iloc[i]
    for k in range(i + 1, len(df)):
        if level is not None and l[k] <= level:
            return k, min(level, o[k]), "stop"
        if c[k] > sma5.iloc[k]:
            return k, c[k], "signal"
        if kind == "days" and k - i >= val:
            return k, c[k], "time"
    return len(df) - 1, c[-1], "end"


def run(symbols, start="2005-01-01", threshold=5, baseline=False, stop=None, name=None):
    trades = []
    name = name or ("Vergleich: roter Tag > SMA200 (1d)" if baseline else f"{NAME} (1d)")
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
                j, px, why = _exit(df, i, sma5, a, stop)
                trades.append(make_trade(name, sym, "long", df.index[i], entry,
                                         entry - a.iloc[i], None, df.index[j], px, why))
                i = j + 1
                continue
            i += 1
    return trades
