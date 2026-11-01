"""SuperTrend STRATEGY – KivancOzbilgic, TradingView (PUB;rcRbtoBiKGtjZq96XWjZtnEs2k2dBWaj,
ca. 25.600 Likes), tradingview.com/script/P5Gu6F8k. Pine-Code über pine-facade geladen.

Regeln aus dem Pine-Code: ATR(10) (Wilder, changeATR=true), Quelle hl2, Faktor 3.
  up = hl2 - 3*ATR, nachgezogen (max mit Vorwert, solange Vorschluss darüber);
  dn = hl2 + 3*ATR, nachgezogen (min mit Vorwert, solange Vorschluss darunter).
  Trend dreht auf +1, wenn Schluss > dn der Vorkerze; auf -1, wenn Schluss < up der Vorkerze.
  Kauf bei Wechsel auf +1, Leerverkauf bei Wechsel auf -1 (immer im Markt, Pine
  strategy.entry dreht die Position). Ausführung zur Eröffnung der Folgekerze.
KEIN Stop-Loss und kein Kursziel. "1 R" = 1 ATR(14) (Rechengröße). Das Datumsfenster im
Pine-Code (ab 2018) wird nicht übernommen: Tageskerzen seit 2005.
Vergleich: Kurs kreuzt EMA(20) (ebenfalls Wendesystem, Long+Short bzw. nur Long).
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr
from ._reversal import run_reversal

NAME = "KivancOzbilgic SuperTrend (1d)"


def supertrend(df, period=10, mult=3.0):
    a = atr(df, period).to_numpy()
    src = ((df.High + df.Low) / 2).to_numpy()
    c = df.Close.to_numpy()
    n = len(df)
    up, dn, tr = np.empty(n), np.empty(n), np.ones(n, dtype=int)
    for t in range(n):
        u, d = src[t] - mult * a[t], src[t] + mult * a[t]
        if t == 0:
            up[t], dn[t] = u, d
            continue
        up[t] = max(u, up[t - 1]) if c[t - 1] > up[t - 1] else u
        dn[t] = min(d, dn[t - 1]) if c[t - 1] < dn[t - 1] else d
        tr[t] = 1 if (tr[t - 1] == -1 and c[t] > dn[t - 1]) else (
            -1 if (tr[t - 1] == 1 and c[t] < up[t - 1]) else tr[t - 1])
    return tr


def run(symbols, start="2005-01-01", baseline=False, shorts=True):
    trades = []
    suffix = "" if shorts else ", nur Long"
    name = f"Vergleich: Kurs kreuzt EMA20 (1d{suffix})" if baseline else (
        f"KivancOzbilgic SuperTrend (1d{suffix})")
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        if baseline:
            c, e = df.Close, df.Close.ewm(span=20, adjust=False).mean()
            up = ((c > e) & (c.shift() <= e.shift())).to_numpy()
            dn = ((c < e) & (c.shift() >= e.shift())).to_numpy()
        else:
            tr = supertrend(df)
            prev = np.roll(tr, 1)
            prev[0] = tr[0]
            up, dn = (tr == 1) & (prev == -1), (tr == -1) & (prev == 1)
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 30)
        trades += run_reversal(df, sym, name, up, dn, first, longs=True, shorts=shorts,
                               atr=atr(df).to_numpy())
    return trades
