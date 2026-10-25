"""Golden Cross, SMA 200 Long Only – ChartArt, TradingView (PUB;2811, 11.500 Likes),
tradingview.com/script/6ZReHYKn (Pine-Code über pubscripts-suggest-json geladen)

Regeln aus dem Pine-Code: Kauf, wenn SMA(50) über SMA(200) kreuzt; Verkauf, wenn SMA(50)
unter SMA(200) kreuzt. Nur Long. Ausführung zur Eröffnung der Folgekerze (Pine-Standard).
KEIN Stop-Loss, kein Kursziel. "1 R" = 1 ATR(14) (nur Rechengröße). Tageskerzen seit 2005.
Vergleich: Kurs kreuzt SMA(200) (statt SMA50 über SMA200), gleicher Ablauf.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr
from ._reversal import run_reversal

NAME = "ChartArt Golden Cross (1d)"


def run(symbols, start="2005-01-01", baseline=False):
    trades = []
    name = "Vergleich: Kurs kreuzt SMA200 (1d)" if baseline else NAME
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 260:
            continue
        c = df.Close
        fast = c if baseline else c.rolling(50).mean()
        slow = c.rolling(200).mean()
        up = ((fast > slow) & (fast.shift() <= slow.shift())).to_numpy()
        dn = ((fast < slow) & (fast.shift() >= slow.shift())).to_numpy()
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 201)
        trades += run_reversal(df, sym, name, up, dn, first, longs=True, shorts=False,
                               atr=atr(df).to_numpy())
    return trades
