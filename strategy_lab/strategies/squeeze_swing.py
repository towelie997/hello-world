"""TTM Squeeze + EMA 21/34 Swing – BrandonTrades, youtu.be/OKl208tuiIs

Regeln aus dem Video (nur Long):
  * Kurs hält sich über dem 21er und 34er EMA.
  * Kurs ist im "Squeeze": Bollinger-Bänder (20, 2) liegen innerhalb der
    Keltner-Kanäle (20, 1,5x ATR).
  * Einstieg zum Kerzenschluss bei "bullischer Kursbewegung" – hier: Squeeze
    in der Vorkerze aktiv und Momentum steigt (Schluss minus 20er-Durchschnitt
    höher als in der Vorkerze).
  * Stop: Schluss unter dem 34er EMA. Kein festes Kursziel im Video.
Annahmen: Ausstieg zum Schlusskurs der Kerze, die unter dem 34er EMA schließt.
Das Risiko für die R-Berechnung ist der Abstand zum 34er EMA (mind. 0,5 ATR).
Getestet auf Tages- und Wochenkerzen seit 2005.
"""

import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "Squeeze + EMA21/34"


def _weekly(df):
    w = df.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last"})
    return w.dropna()


def run(symbols, timeframe="1d", start="2005-01-01", baseline=False):
    """baseline=True: gleiche Regeln ohne Squeeze-Bedingung (zeigt, ob der Squeeze etwas bringt)."""
    trades = []
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if df.empty:
            continue
        if timeframe == "1w":
            df = _weekly(df)
        if len(df) < 100:
            continue
        e21 = df.Close.ewm(span=21, adjust=False).mean()
        e34 = df.Close.ewm(span=34, adjust=False).mean()
        sma = df.Close.rolling(20).mean()
        sd = df.Close.rolling(20).std()
        a = atr(df, 20)
        squeeze = (sma + 2 * sd < sma + 1.5 * a) & (sma - 2 * sd > sma - 1.5 * a)
        mom = df.Close - sma
        i = 40
        while i < len(df):
            if df.index[i] < pd.Timestamp(start):
                i += 1
                continue
            c = df.Close.iloc[i]
            if (baseline or squeeze.iloc[i - 1]) and c > e21.iloc[i] and c > e34.iloc[i] \
                    and mom.iloc[i] > mom.iloc[i - 1]:
                entry = c
                stop_ref = min(e34.iloc[i], entry - 0.5 * a.iloc[i])
                exit_idx = None
                for j in range(i + 1, len(df)):
                    if df.Close.iloc[j] < e34.iloc[j]:
                        exit_idx = j
                        break
                if exit_idx is None:
                    exit_idx, why = len(df) - 1, "end"
                else:
                    why = "stop"
                name = f"Vergleich: EMA21/34 ohne Squeeze ({timeframe})" if baseline else f"{NAME} ({timeframe})"
                trades.append(make_trade(name, sym, "long", df.index[i],
                                         entry, stop_ref, None, df.index[exit_idx],
                                         df.Close.iloc[exit_idx], why))
                i = exit_idx + 1
                continue
            i += 1
    return trades
