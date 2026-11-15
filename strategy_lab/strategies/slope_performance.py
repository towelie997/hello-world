"""Slope Performance Trend – StockCharts ChartSchool (Arthur Hill):
chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/slope-performance-trend

Regeln aus dem Artikel (Monatskerzen, nur Long, sonst Kasse):
  Steigung = Steigung der linearen Regression der letzten 12 Monatsschlusskurse.
  Kauf, wenn die 12-Monats-Steigung des Kurses UND die des Kursverhältnisses zum S&P 500
  (Wert / SPY) positiv sind. Verkauf, wenn beide negativ sind.
Annahmen: Im Artikel für die 9 Sektor-ETFs gedacht; hier auf die SWING-Liste (bzw. die 200
Werte) angewandt, Vergleichsindex SPY (SPY selbst wird übersprungen). Signal und Handel zum
letzten Schlusskurs des Monats. KEIN Stop-Loss. "1 R" = 1 ATR(14) (Tageskerzen).
Tageskerzen seit 2005, daraus Monatsschlusskurse.
Vergleich: nur die Kurs-Steigung (ohne relative Stärke): Kauf bei positiver, Verkauf bei
negativer Steigung.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "ChartSchool Slope Performance Trend (1M)"


def slope(s, n=12):
    x = np.arange(n) - (n - 1) / 2
    return s.rolling(n).apply(lambda y: float(np.dot(x, y) / np.dot(x, x)), raw=True)


def month_end(df):
    g = df.index.to_period("M")
    return df.index[~g.duplicated(keep="last")]


def run(symbols, start="2005-01-01", baseline=False):
    trades = []
    name = "Vergleich: nur 12-Monats-Steigung des Kurses (1M)" if baseline else NAME
    spy = data.load("SPY", "1d", "max").Close
    for sym in symbols:
        if sym == "SPY":
            continue
        df = data.load(sym, "1d", "max")
        if len(df) < 300:
            continue
        me = month_end(df)
        me = me[:-1] if me[-1].to_period("M") == pd.Timestamp.today().to_period("M") else me
        c = df.Close.loc[me]
        rel = c / spy.reindex(me, method="ffill")
        sp, sr = slope(c), slope(rel)
        if baseline:
            buy, sell = sp > 0, sp < 0
        else:
            buy, sell = (sp > 0) & (sr > 0), (sp < 0) & (sr < 0)
        A = atr(df).reindex(me)
        pos, t_in = False, None
        for t in me[me >= pd.Timestamp(start)]:
            if not pos and buy.loc[t]:
                pos, t_in = True, t
            elif pos and sell.loc[t]:
                trades.append(make_trade(name, sym, "long", t_in, c.loc[t_in],
                                         c.loc[t_in] - A.loc[t_in], None, t, c.loc[t], "signal"))
                pos = False
        if pos:
            trades.append(make_trade(name, sym, "long", t_in, c.loc[t_in],
                                     c.loc[t_in] - A.loc[t_in], None, df.index[-1],
                                     df.Close.iloc[-1], "end"))
    return [x for x in trades if np.isfinite(x.r)]
