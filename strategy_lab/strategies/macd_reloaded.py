"""MACD ReLoaded STRATEGY – KivancOzbilgic, TradingView (PUB;5842955c…, ca. 7.700 Likes),
tradingview.com/script/VO6DY8s1 (Pine-Code über pine-facade geladen). Idee: Gerald Appel.

Regeln aus dem Pine-Code (Standardwerte): Durchschnittstyp "VAR" (Variable Index Dynamic
Average mit Chande-Momentum über 9 Kerzen):
  VAR_t = a*|CMO9|*x_t + (1 - a*|CMO9|)*VAR_{t-1},  a = 2/(Länge+1), Start bei 0.
  MACD = VAR12(close) - VAR26(close); Trigger = VAR9(MACD); hist = MACD - Trigger.
  Kauf, wenn hist über 0 kreuzt; Leerverkauf, wenn hist unter 0 kreuzt (Position dreht).
  Ausführung zur Eröffnung der Folgekerze. KEIN Stop-Loss, kein Kursziel.
Das Datumsfenster im Code (ab 2018) wird nicht übernommen: Tageskerzen seit 2005.
"1 R" = 1 ATR(14). Vergleich: klassischer EMA-MACD, Histogramm kreuzt 0
(chartart_macd_stoch.py, Vergleichsvariante).
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr
from ._reversal import run_reversal


def var_ma(x, length, n_cmo=9):
    x = np.nan_to_num(np.asarray(x, dtype=float))
    a = 2 / (length + 1)
    diff = np.diff(x, prepend=x[0])
    up = pd.Series(np.where(diff > 0, diff, 0.0)).rolling(n_cmo, min_periods=1).sum().to_numpy()
    dn = pd.Series(np.where(diff < 0, -diff, 0.0)).rolling(n_cmo, min_periods=1).sum().to_numpy()
    with np.errstate(invalid="ignore", divide="ignore"):
        cmo = np.nan_to_num((up - dn) / (up + dn))
    out = np.zeros(len(x))
    prev = 0.0
    for t in range(len(x)):
        w = a * abs(cmo[t])
        prev = w * x[t] + (1 - w) * prev
        out[t] = prev
    return out


def run(symbols, start="2005-01-01", shorts=True):
    trades = []
    name = "KivancOzbilgic MACD ReLoaded (1d" + ("" if shorts else ", nur Long") + ")"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 100:
            continue
        c = df.Close.to_numpy()
        macd = var_ma(c, 12) - var_ma(c, 26)
        hist = pd.Series(macd - var_ma(macd, 9), index=df.index)
        up = ((hist > 0) & (hist.shift() <= 0)).to_numpy()
        dn = ((hist < 0) & (hist.shift() >= 0)).to_numpy()
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 60)
        trades += run_reversal(df, sym, name, up, dn, first, longs=True, shorts=shorts,
                               atr=atr(df).to_numpy())
    return trades
