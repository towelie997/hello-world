"""Heikin-Ashi PSAR Strategy – QuantNomad, TradingView (PUB;3Xncz0jk6WdXMtoUsh8PLZ04PWImlWra,
ca. 3.400 Likes), tradingview.com/script/0iKy7lyG (Pine-Code über pine-facade geladen)

Regeln aus dem Pine-Code (Standardwerte 0,02 / 0,02 / 0,2):
  Heikin-Ashi-Kerzen: haclose = (O+H+L+C)/4, haopen = (haopen[1]+haclose[1])/2,
  hahigh = max(H, haopen, haclose), halow = min(L, haopen, haclose).
  Parabolic SAR auf Heikin-Ashi-Werten; Richtungswechsel, wenn haclose den SAR der Vorkerze
  kreuzt (nicht das Tief/Hoch). Beim Wechsel: SAR = Extrempunkt der Vorkerze, AF = 0,02.
  Kauf beim Wechsel auf aufwärts, Leerverkauf beim Wechsel auf abwärts (Position dreht).
  Ausführung zur Eröffnung der Folgekerze. KEIN Stop-Loss, kein Kursziel.
  Wie im Code: Der AF wächst im Abwärtstrend, wenn das ECHTE Tief (nicht halow) den
  Extrempunkt unterschreitet.
Das Datumsfenster im Code (ab 2018) wird nicht übernommen: Tageskerzen seit 2005.
"1 R" = 1 ATR(14).
Vergleich: dieselbe SAR-Logik auf normalen Kerzen statt Heikin-Ashi.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr
from ._reversal import run_reversal


def sar_flips(o, h, l, c, heikin=True, start=0.02, inc=0.02, mx=0.2):
    n = len(c)
    if heikin:
        hc = (o + h + l + c) / 4
        ho = np.empty(n)
        ho[0] = (o[0] + c[0]) / 2
        for t in range(1, n):
            ho[t] = (ho[t - 1] + hc[t - 1]) / 2
        hh, hl = np.maximum(h, np.maximum(ho, hc)), np.minimum(l, np.minimum(ho, hc))
    else:
        hc, ho, hh, hl = c, o, h, l
    psar, af, ep, d = np.full(n, np.nan), np.zeros(n), np.zeros(n), np.zeros(n, dtype=int)
    up, dn = np.zeros(n, bool), np.zeros(n, bool)
    for t in range(1, n):
        init = t < 2
        l2s = (not init) and d[t - 1] == 1 and hc[t] <= psar[t - 1]
        s2l = (not init) and d[t - 1] == -1 and hc[t] >= psar[t - 1]
        change = init or l2s or s2l
        if init:
            d[t] = 1 if hc[t - 1] > ho[t - 1] else -1
        else:
            d[t] = -1 if l2s else (1 if s2l else d[t - 1])
        if change:
            af[t] = start
        elif (d[t] == 1 and hh[t] > ep[t - 1]) or (d[t] == -1 and l[t] < ep[t - 1]):
            af[t] = min(mx, af[t - 1] + inc)
        else:
            af[t] = af[t - 1]
        if change:
            ep[t] = hh[t] if d[t] == 1 else hl[t]
        else:
            ep[t] = max(ep[t - 1], hh[t]) if d[t] == 1 else min(ep[t - 1], hl[t])
        if init:
            psar[t] = hl[t - 1] if hc[t - 1] > ho[t - 1] else hh[t - 1]
        elif change:
            psar[t] = ep[t - 1]
        elif d[t] == 1:
            psar[t] = psar[t - 1] + af[t] * (ep[t] - psar[t - 1])
        else:
            psar[t] = psar[t - 1] - af[t] * (psar[t - 1] - ep[t])
        up[t], dn[t] = s2l, l2s
    return up, dn


def run(symbols, start="2005-01-01", baseline=False, shorts=True):
    trades = []
    suffix = "" if shorts else ", nur Long"
    name = f"Vergleich: PSAR auf normalen Kerzen (1d{suffix})" if baseline else (
        f"QuantNomad Heikin-Ashi PSAR (1d{suffix})")
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        o, h, l, c = (df[x].to_numpy() for x in ("Open", "High", "Low", "Close"))
        up, dn = sar_flips(o, h, l, c, heikin=not baseline)
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 30)
        trades += run_reversal(df, sym, name, up, dn, first, longs=True, shorts=shorts,
                               atr=atr(df).to_numpy())
    return trades
