"""20 years old Turtles strategy – tmr0, TradingView (PUB;2008, 6.500 Likes),
tradingview.com/script/Q1O23zJP (Pine-Code über pubscripts-suggest-json geladen)

Regeln aus dem Pine-Code (zwei Systeme wie bei den "Turtles", Long und Short):
  * Schnell: Long bei Hoch > 20-Tage-Hoch (Vortage), schließen bei Tief <= 10-Tage-Tief;
    Short bei Tief < 20-Tage-Tief, schließen bei Hoch >= 10-Tage-Hoch.
  * Langsam: dasselbe mit 55 / 20 Tagen.
  * Ausführung zur Eröffnung der Folgekerze. KEIN Stop-Loss (anders als die originalen
    Turtles mit 2N-Stop), kein Kursziel.
Annahmen: Beide Systeme laufen als getrennte Handelsfolgen (das Original verrechnet Long
und Short der beiden Systeme zu einer Nettoposition – vereinfacht). "1 R" = 1 ATR(14).
Tageskerzen seit 2005. Kontrolle: Variante nur Long; zusätzlich Zufallstest der Robustheit.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "Turtles tmr0"


def _system(df, sym, name, n_in, n_out, first, longs, shorts, a):
    h, l, o, c = (df[k].to_numpy() for k in ("High", "Low", "Open", "Close"))
    hi_in = df.High.rolling(n_in).max().shift().to_numpy()
    lo_in = df.Low.rolling(n_in).min().shift().to_numpy()
    lo_out = df.Low.rolling(n_out).min().shift().to_numpy()
    hi_out = df.High.rolling(n_out).max().shift().to_numpy()
    out, pos, entry, t_in, risk = [], 0, 0.0, 0, 0.0
    for t in range(first, len(df) - 1):
        if pos == 1 and l[t] <= lo_out[t]:
            out.append(make_trade(name, sym, "long", df.index[t_in], entry, entry - risk, None,
                                  df.index[t + 1], o[t + 1], "signal"))
            pos = 0
        elif pos == -1 and h[t] >= hi_out[t]:
            out.append(make_trade(name, sym, "short", df.index[t_in], entry, entry + risk, None,
                                  df.index[t + 1], o[t + 1], "signal"))
            pos = 0
        if pos == 0:
            if longs and h[t] > hi_in[t]:
                pos, entry, t_in, risk = 1, o[t + 1], t + 1, a[t]
            elif shorts and l[t] < lo_in[t]:
                pos, entry, t_in, risk = -1, o[t + 1], t + 1, a[t]
    if pos != 0:
        out.append(make_trade(name, sym, "long" if pos == 1 else "short", df.index[t_in], entry,
                              entry - pos * risk, None, df.index[-1], c[-1], "end"))
    return out


def run(symbols, start="2005-01-01", longs=True, shorts=True):
    trades = []
    name = f"{NAME} (1d{'' if shorts else ', nur Long'})"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 120:
            continue
        a = atr(df).to_numpy()
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 60)
        trades += _system(df, sym, name, 20, 10, first, longs, shorts, a)
        trades += _system(df, sym, name, 55, 20, first, longs, shorts, a)
    return trades
