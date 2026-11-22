"""Price and Volume Breakout Buy Strategy – TradeDots, TradingView
(PUB;bf6c3d4744be458db3a63fb9555e5352, ca. 5.400 Likes), tradingview.com/script/jc2hs2qK
(Pine-Code über pine-facade geladen)

Regeln aus dem Pine-Code (Standardwerte, Richtung "Long"):
  Kauf, wenn keine Position offen ist und
    Schluss > höchstes Hoch der 60 Vorkerzen UND Volumen > höchstes Volumen der 60 Vorkerzen
    UND Schluss > SMA(200).
  Verkauf, wenn 5 Schlusskurse in Folge unter der SMA(200) liegen.
  (Short-Variante im Code spiegelbildlich, aber Standard ist nur Long.)
  Orders zur Eröffnung der Folgekerze (Pine-Standard). KEIN Stop-Loss, kein Kursziel.
"1 R" = 1 ATR(14). Tageskerzen seit 2005.
Vergleich: gleicher Ausbruch und Ausstieg ohne Volumenbedingung.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "TradeDots Kurs + Volumen-Ausbruch (1d)"


def run(symbols, start="2005-01-01", baseline=False):
    trades = []
    name = "Vergleich: 60-Tage-Ausbruch ohne Volumen (1d)" if baseline else NAME
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 260:
            continue
        vol = data.load_volume(sym).reindex(df.index)
        c = df.Close
        sma = c.rolling(200).mean()
        entry = (c > df.High.rolling(60).max().shift()) & (c > sma)
        if not baseline:
            entry &= vol > vol.rolling(60).max().shift()
        below = (c < sma).astype(int).rolling(5).sum() == 5
        entry, below = entry.to_numpy(), below.to_numpy()
        O, C, A = df.Open.to_numpy(), c.to_numpy(), atr(df).to_numpy()
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 201)
        pos, t_in = False, None
        for t in range(first, len(df) - 1):
            if pos and below[t]:
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
