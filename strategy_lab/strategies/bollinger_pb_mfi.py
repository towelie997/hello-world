"""Percent B Money Flow – John Bollinger ("Bollinger on Bollinger Bands"), beschrieben in der
StockCharts ChartSchool:
chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/percent-b-money-flow

Regeln aus dem Artikel:
  Kauf, wenn %B über 0,80 und der Money Flow Index (MFI) über 80 steigt.
  Verkauf (Short), wenn %B unter 0,20 und MFI unter 20 fällt.
  Stops mit dem Parabolic SAR (Bollingers Vorschlag).
Annahmen: Bollinger-Bänder 20/2, MFI(14) (Standard). Signal = beide Bedingungen am selben
Schlusskurs erfüllt und am Vortag noch nicht beide. Einstieg zum Schluss. Parabolic SAR
0,02/0,02/0,2, startet beim tiefsten Tief (Short: höchsten Hoch) der letzten 5 Kerzen,
wird täglich nachgezogen; Ausstieg bei Berührung (Kurslücke: zur Eröffnung) oder beim
Gegensignal (zum Schluss). Die "Tweaks" (MACD-Einstieg, ADX < 15) gehören nicht zur
Grundregel und werden nicht genutzt. Tageskerzen seit 2005.
Vergleich: nur %B (ohne MFI), gleicher Stop/Ausstieg.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import make_trade

NAME = "Bollinger %B + MFI (1d)"


def mfi(df, vol, n=14):
    tp = (df.High + df.Low + df.Close) / 3
    raw = tp * vol
    pos = raw.where(tp > tp.shift(), 0.0).rolling(n).sum()
    neg = raw.where(tp < tp.shift(), 0.0).rolling(n).sum()
    return 100 - 100 / (1 + pos / neg)


def run(symbols, start="2005-01-01", baseline=False, shorts=True):
    trades = []
    name = "Vergleich: nur %B 0,8/0,2 + SAR (1d)" if baseline else (
        NAME if shorts else "Bollinger %B + MFI (1d, nur Long)")
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        vol = data.load_volume(sym).reindex(df.index)
        c = df.Close
        m, sd = c.rolling(20).mean(), c.rolling(20).std(ddof=0)
        pb = (c - (m - 2 * sd)) / (4 * sd)
        if baseline:
            lg, sh = pb > 0.8, pb < 0.2
        else:
            f = mfi(df, vol)
            lg, sh = (pb > 0.8) & (f > 80), (pb < 0.2) & (f < 20)
        lg = (lg & ~lg.shift(fill_value=False)).to_numpy()
        sh = (sh & ~sh.shift(fill_value=False)).to_numpy()
        O, H, L, C = (df[x].to_numpy() for x in ("Open", "High", "Low", "Close"))
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 40)
        while i < len(df) - 1:
            side = "long" if lg[i] else ("short" if (sh[i] and shorts) else None)
            if side is None:
                i += 1
                continue
            if side == "long":
                sar, ep = L[i - 4:i + 1].min(), H[i]
            else:
                sar, ep = H[i - 4:i + 1].max(), L[i]
            stop0, af = sar, 0.02
            j, px, why = len(df) - 1, C[-1], "end"
            for k in range(i + 1, len(df)):
                if side == "long":
                    sar = min(sar + af * (ep - sar), L[k - 1], L[k - 2])
                    if L[k] <= sar:
                        j, px, why = k, min(sar, O[k]), "stop"
                        break
                    if sh[k]:
                        j, px, why = k, C[k], "signal"
                        break
                    if H[k] > ep:
                        ep, af = H[k], min(af + 0.02, 0.2)
                else:
                    sar = max(sar + af * (ep - sar), H[k - 1], H[k - 2])
                    if H[k] >= sar:
                        j, px, why = k, max(sar, O[k]), "stop"
                        break
                    if lg[k]:
                        j, px, why = k, C[k], "signal"
                        break
                    if L[k] < ep:
                        ep, af = L[k], min(af + 0.02, 0.2)
            if (side == "long" and stop0 >= C[i]) or (side == "short" and stop0 <= C[i]):
                i += 1
                continue
            trades.append(make_trade(name, sym, side, df.index[i], C[i], stop0, None,
                                     df.index[j], px, why))
            i = j + 1
    return trades
