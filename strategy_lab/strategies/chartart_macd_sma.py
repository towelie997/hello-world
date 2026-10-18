"""MACD + SMA 200 Strategy – ChartArt, TradingView (PUB;2004, 31.700 Likes),
tradingview.com/script/yMCa3XZD (Pine-Code über pubscripts-suggest-json geladen)

Regeln aus dem Pine-Code (MACD hier aus EINFACHEN Durchschnitten, wie im Original):
  * fast = SMA(12), slow = SMA(26), MACD = fast - slow, Signal = SMA(9) des MACD,
    Histogramm = MACD - Signal, sehr langsam = SMA(200).
  * Long: Histogramm kreuzt über 0, MACD > 0, fast > slow, Schluss vor 26 Kerzen > SMA200.
    Kauf-Stop am Tief der Signalkerze.
  * Short: spiegelbildlich, Verkaufs-Stop am Hoch der Signalkerze.
  * Gegensignal dreht die Position. KEIN Stop-Loss, kein Kursziel im Original.
Annahmen: Der Kauf-Stop am Tief liegt unter dem Kurs und wird in der Folgekerze sofort
ausgelöst -> Ausführung zur Eröffnung (mindestens am Tief). Das Original löscht offene
Orders, wenn SMA26 < SMA200 – bei sofortiger Ausführung ohne Wirkung. Tageskerzen seit 2005.
"1 R" = 1 ATR(14) (nur Rechengröße).
Vergleich: jede Histogramm-Kreuzung ohne die Trend-Bedingungen.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr
from ._reversal import run_reversal

NAME = "ChartArt MACD + SMA200"


def run(symbols, start="2005-01-01", longs=True, shorts=True, baseline=False):
    trades = []
    if baseline:
        name = "Vergleich: jede MACD-Kreuzung (1d)"
    else:
        name = f"{NAME} (1d{'' if shorts else ', nur Long'})"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 260:
            continue
        c = df.Close
        fast, slow, vslow = c.rolling(12).mean(), c.rolling(26).mean(), c.rolling(200).mean()
        macd = fast - slow
        hist = macd - macd.rolling(9).mean()
        up = (hist > 0) & (hist.shift() <= 0)
        dn = (hist < 0) & (hist.shift() >= 0)
        if baseline:
            ls, ss = up, dn
        else:
            ls = up & (macd > 0) & (fast > slow) & (c.shift(26) > vslow)
            ss = dn & (macd < 0) & (fast < slow) & (c.shift(26) < vslow)
        o, lo, hi = df.Open.to_numpy(), df.Low.to_numpy(), df.High.to_numpy()
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 230)
        trades += run_reversal(df, sym, name, ls.to_numpy(), ss.to_numpy(), first, longs, shorts,
                               fill_long=lambda t: max(o[t], lo[t - 1]),
                               fill_short=lambda t: min(o[t], hi[t - 1]),
                               atr=atr(df).to_numpy())
    return trades
