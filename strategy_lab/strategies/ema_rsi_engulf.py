"""EMA 200 + RSI + Engulfing – TradingLab, youtu.be/XBcMiYK7qYY

Regeln aus dem Video (nur Long):
  * Kurs über dem 200er EMA (Trend).
  * RSI(14) über 50 (Momentum).
  * Bullische Engulfing-Kerze: Vorkerze rot, Eröffnung <= Vortagesschluss,
    Schluss > Eröffnung der Vorkerze. Einstieg zum Schlusskurs dieser Kerze.
  * Stop: 2x die Länge der Einstiegskerze unter dem Einstieg. Ziel 2:1.
Laut Video "für alle Zeitebenen" – getestet auf Tageskerzen (lange Historie)
und Stundenkerzen (2 Jahre). Eine Position pro Wert gleichzeitig.
"""

import pandas as pd

from .. import data
from ..engine import make_trade, rsi, simulate_exit

NAME = "EMA200 + RSI + Engulfing"


def run(symbols, interval="1d", period="max", rr=2.0, start="2005-01-01", baseline=False):
    """baseline=True: Vergleichsstrategie ohne RSI/Engulfing – kauft jede grüne Kerze
    über dem EMA200, gleiche Stop-/Ziel-Regeln. Zeigt, ob die Signale etwas bringen."""
    trades = []
    for sym in symbols:
        df = data.load(sym, interval, period)
        if interval.endswith("h"):
            df = data.regular_session(df) if not sym.endswith("-USD") else df
        if len(df) < 250:
            continue
        ema = df.Close.ewm(span=200, adjust=False).mean()
        r = rsi(df.Close)
        o, h, l, c = df.Open.values, df.High.values, df.Low.values, df.Close.values
        i = 201
        while i < len(df):
            if interval == "1d" and df.index[i] < pd.Timestamp(start):
                i += 1
                continue
            engulf = c[i - 1] < o[i - 1] and c[i] > o[i] and o[i] <= c[i - 1] and c[i] > o[i - 1]
            signal = (c[i] > o[i]) if baseline else (engulf and r.iloc[i] > 50)
            if signal and c[i] > ema.iloc[i]:
                length = h[i] - l[i]
                entry, stop = c[i], c[i] - 2 * length
                target = entry + rr * (entry - stop)
                t, px, why = simulate_exit(df, i + 1, "long", stop, target, eod=False)
                name = f"Vergleich: grüne Kerze > EMA200 ({interval})" if baseline else f"{NAME} ({interval})"
                trades.append(make_trade(name, sym, "long", df.index[i],
                                         entry, stop, target, t, px, why))
                i = df.index.get_loc(t) + 1
                continue
            i += 1
    return trades
