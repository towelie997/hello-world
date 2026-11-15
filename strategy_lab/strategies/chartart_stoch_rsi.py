"""Stochastic + RSI, Double Strategy – ChartArt, TradingView (PUB;1897, ca. 7.000 Likes),
tradingview.com/script/IGJPEi7L (Pine-Code über pubscripts-suggest-json geladen)

Regeln aus dem Pine-Code (Standardwerte):
  Stochastik k = SMA3(stoch 14), d = SMA3(k); RSI(14).
  Long:  k kreuzt über d UND k < 20 UND RSI kreuzt über 30 (alles in derselben Kerze).
  Short: k kreuzt unter d UND k > 80 UND RSI kreuzt unter 70.
  strategy.entry dreht die Position (nach dem ersten Signal immer im Markt).
  Ausführung zur Eröffnung der Folgekerze. KEIN Stop-Loss, kein Kursziel.
"1 R" = 1 ATR(14). Tageskerzen seit 2005.
Vergleich: nur RSI kreuzt 30 / 70 (ohne Stochastik), gleicher Ablauf.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, rsi
from ._reversal import run_reversal


def run(symbols, start="2005-01-01", baseline=False, shorts=True):
    trades = []
    suffix = "" if shorts else ", nur Long"
    name = f"Vergleich: RSI kreuzt 30/70 (1d{suffix})" if baseline else (
        f"ChartArt Stochastik + RSI (1d{suffix})")
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        h, l, c = df.High, df.Low, df.Close
        k = (100 * (c - l.rolling(14).min()) / (h.rolling(14).max() - l.rolling(14).min())
             ).rolling(3).mean()
        d = k.rolling(3).mean()
        r = rsi(c, 14)
        r_up = (r > 30) & (r.shift() <= 30)
        r_dn = (r < 70) & (r.shift() >= 70)
        if baseline:
            lg, sh = r_up, r_dn
        else:
            lg = (k > d) & (k.shift() <= d.shift()) & (k < 20) & r_up
            sh = (k < d) & (k.shift() >= d.shift()) & (k > 80) & r_dn
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 40)
        trades += run_reversal(df, sym, name, lg.to_numpy(), sh.to_numpy(), first,
                               longs=True, shorts=shorts, atr=atr(df).to_numpy())
    return trades
