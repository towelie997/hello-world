"""15-Min Opening Range Breakout – "The Moving Average", youtu.be/jlShztsY3oA

Regeln aus dem Video:
  * Hoch/Tief der ersten 15-Minuten-Kerze (9:30–9:45 NY) markieren.
  * Schließt eine Kerze über der Range -> Long, unter der Range -> Short.
  * Stop auf der anderen Seite der Range, Ziel 1:1,5.
Variante "trend": nur in Richtung des übergeordneten Trends
  (Vortagesschluss über/unter dem 50-Tage-Durchschnitt), wie im Video empfohlen.
Annahmen: Ausbruch auf 5-Min-Kerzen, ein Trade pro Tag, Einstieg bis 12:00,
Ausstieg spätestens zum Handelsschluss.
"""

from datetime import time

import pandas as pd

from .. import data
from ..engine import make_trade, simulate_exit

NAME = "ORB 15 Min"


def run(symbols, trend_filter=False, rr=1.5, cutoff=time(12, 0)):
    trades = []
    for sym in symbols:
        bars = data.regular_session(data.load(sym, "5m", "60d"))
        if bars.empty:
            continue
        daily = data.load(sym, "1d", "2y")
        sma50 = daily.Close.rolling(50).mean()
        for day, b in data.complete_days(bars, time(15, 55)).items():
            if len(b) < 6 or b.index[0].time() != time(9, 30):
                continue
            hist = daily[daily.index.date < day]
            if trend_filter:
                ref = sma50.loc[hist.index[-1]] if len(hist) else float("nan")
                if pd.isna(ref):
                    continue
                bias = 1 if hist.Close.iloc[-1] > ref else -1
            orh, orl = b.iloc[:3].High.max(), b.iloc[:3].Low.min()
            for i in range(3, len(b)):
                if b.index[i].time() > cutoff:
                    break
                c = b.iloc[i].Close
                side = "long" if c > orh else "short" if c < orl else None
                if side is None:
                    continue
                if trend_filter and (side == "long") != (bias == 1):
                    break
                entry = c
                stop = orl if side == "long" else orh
                risk = abs(entry - stop)
                target = entry + rr * risk if side == "long" else entry - rr * risk
                t, px, why = simulate_exit(b, i + 1, side, stop, target)
                name = NAME + (" + Trend" if trend_filter else "")
                trades.append(make_trade(name, sym, side, b.index[i], entry, stop, target, t, px, why))
                break
    return trades
