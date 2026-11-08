"""Fractal Breakout Strategy – ChartArt, TradingView (PUB;2553, ca. 9.000 Likes),
tradingview.com/script/EjLwVtgp (Pine-Code über pubscripts-suggest-json geladen)

Regeln aus dem Pine-Code (v2, Standardwerte, nur Long):
  Fraktal-Hoch an Kerze t: High[t-2] höher als High[t-4], High[t-3], High[t-1], High[t].
  fractal_price = hl2 beim vorletzten Fraktal-Signal (valuewhen(..., hl2, 1)).
  fractal_average = Mittel von fractal_price[1..3]; Trend = fractal_average steigt.
  Einstieg: Trend und hl2 der Vorkerze > fractal_price ("no repainting").
  Ausstieg: Trend war vor 3 Kerzen aufwärts und ist jetzt nicht mehr aufwärts.
  Orders zur Eröffnung der Folgekerze (Pine-Standard). KEIN Stop-Loss, kein Kursziel.
"1 R" = 1 ATR(14) (Rechengröße). Tageskerzen seit 2005.
Vergleich: gleicher Ein-/Ausstieg ohne Fraktal-Trendfilter beim Einstieg.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "ChartArt Fractal Breakout (1d)"


def run(symbols, start="2005-01-01", baseline=False, n_time=3):
    trades = []
    name = "Vergleich: Fraktal-Ausbruch ohne Trendfilter (1d)" if baseline else NAME
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        h = df.High
        price = (df.High + df.Low) / 2
        top = (h.shift(2) > h.shift(3)) & (h.shift(2) > h.shift(4)) & (h.shift(2) > h.shift(1)) \
            & (h.shift(2) > h)
        fp = price[top].shift(1).reindex(df.index).ffill()
        fa = (fp.shift(1) + fp.shift(2) + fp.shift(3)) / 3
        trend = fa > fa.shift(1)
        brk = price.shift(1) > fp
        entry = (brk if baseline else (trend & brk)).to_numpy()
        tr = trend.to_numpy()
        ex = np.zeros(len(df), dtype=bool)
        ex[n_time:] = tr[:-n_time] & ~tr[n_time:]
        O, C, A = df.Open.to_numpy(), df.Close.to_numpy(), atr(df).to_numpy()
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 30)
        pos, t_in = False, None
        for t in range(first, len(df) - 1):
            if pos and ex[t]:
                trades.append(make_trade(name, sym, "long", df.index[t_in], O[t_in],
                                         O[t_in] - A[t_in - 1], None, df.index[t + 1],
                                         O[t + 1], "signal"))
                pos = False
            elif not pos and entry[t]:
                pos, t_in = True, t + 1
        if pos:
            trades.append(make_trade(name, sym, "long", df.index[t_in], O[t_in],
                                     O[t_in] - A[t_in - 1], None, df.index[-1], C[-1], "end"))
    return [x for x in trades if np.isfinite(x.r)]
