"""MACD + Stochastic, Double Strategy – ChartArt, TradingView (PUB;2304, ca. 8.000 Likes),
tradingview.com/script/G5ro3y87 (Pine-Code über pubscripts-suggest-json geladen)

Regeln aus dem Pine-Code (Standardwerte):
  MACD 12/26/9, Histogramm delta = MACD - Signal. Stochastik k = SMA3(stoch 14), d = SMA2(k).
  Long:  k kreuzt über d UND k < 29 UND delta kreuzt über 0 (alles in derselben Kerze).
  Short: k kreuzt unter d UND k > 71 UND delta kreuzt unter 0.
  strategy.entry dreht die Position (immer im Markt nach dem ersten Signal).
  Ausführung zur Eröffnung der Folgekerze. KEIN Stop-Loss, kein Kursziel (laut Code).
"1 R" = 1 ATR(14). Tageskerzen seit 2005.
Vergleich: nur MACD-Histogramm kreuzt die Nulllinie (ohne Stochastik), gleicher Ablauf.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr
from ._reversal import run_reversal

NAME = "ChartArt MACD + Stochastik (1d)"


def run(symbols, start="2005-01-01", baseline=False, shorts=True):
    trades = []
    suffix = "" if shorts else ", nur Long"
    name = f"Vergleich: MACD-Histogramm kreuzt 0 (1d{suffix})" if baseline else (
        f"ChartArt MACD + Stochastik (1d{suffix})")
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        h, l, c = df.High, df.Low, df.Close
        macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        delta = macd - macd.ewm(span=9, adjust=False).mean()
        k = (100 * (c - l.rolling(14).min()) / (h.rolling(14).max() - l.rolling(14).min())
             ).rolling(3).mean()
        d = k.rolling(2).mean()
        up0 = (delta > 0) & (delta.shift() <= 0)
        dn0 = (delta < 0) & (delta.shift() >= 0)
        if baseline:
            lg, sh = up0, dn0
        else:
            lg = (k > d) & (k.shift() <= d.shift()) & (k < 29) & up0
            sh = (k < d) & (k.shift() >= d.shift()) & (k > 71) & dn0
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 40)
        trades += run_reversal(df, sym, name, lg.to_numpy(), sh.to_numpy(), first,
                               longs=True, shorts=shorts, atr=atr(df).to_numpy())
    return trades
