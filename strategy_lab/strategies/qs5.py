"""5 Swing-Strategien für den S&P 500 – Quantified Strategies, youtu.be/KuXV0LRfJx8

Regeln aus dem Video (nur Long, Kauf und Verkauf zum Schlusskurs, alle mit demselben
Ausstieg: Schluss über dem Vortageshoch):
  1. Schluss unter (10-Tage-Hoch − Band) und IBS < 0,3; Band aus dem 25-Tage-Durchschnitt
     von (Hoch − Tief).
  2. Montag und der zweite Tag in Folge mit tieferem Schluss ("Turnaround Tuesday").
  3. Schluss unter dem Tief der vorherigen 5 Handelstage.
  4. Tagesspanne kleiner als jede der 6 vorherigen Tage und ADX(5) > 40.
  5. Hoch über dem Hoch der letzten 10 Tage und IBS < 0,15.
  Alle 5 gemeinsam, eine Position pro Wert (wie im Video). KEIN Stop-Loss im Video.
Annahmen: Der Faktor für das Band in Regel 1 wird im Video nicht genannt – 2,5 (von
Quantified Strategies sonst veröffentlicht). ADX nach Wilder. "1 R" = 1 ATR(14).
Hinweis: Regel 5 widerspricht der Fassung im früheren QS-Video (lKzoUptU2io, dort "Hoch
UNTER dem 10-Tage-Hoch"); hier gilt dieses Video. Tageskerzen seit 2005, SPY und SWING.
Vergleich: "Kauf nach rotem Tag" aus qs_ibs.py (gleicher Ausstieg).
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "QS 5 Regeln"


def adx(df, n=5):
    h, l, c = df.High, df.Low, df.Close
    up, dn = h.diff(), -l.diff()
    pdm = up.where((up > dn) & (up > 0), 0.0)
    ndm = dn.where((dn > up) & (dn > 0), 0.0)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    a = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1 / n, adjust=False).mean() / a
    ndi = 100 * ndm.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def signals(df):
    o, h, l, c = df.Open, df.High, df.Low, df.Close
    ibs = ((c - l) / (h - l)).fillna(0.5)
    rng = h - l
    down = c < c.shift()
    r1 = (c < h.rolling(10).max() - 2.5 * rng.rolling(25).mean()) & (ibs < 0.3)
    r2 = (df.index.dayofweek == 0) & down & down.shift(fill_value=False)
    r3 = c < l.shift().rolling(5).min()
    r4 = (rng < rng.shift().rolling(6).min()) & (adx(df, 5) > 40)
    r5 = (h > h.shift().rolling(10).max()) & (ibs < 0.15)
    return r1 | r2 | r3 | r4 | r5


def run(symbols, start="2005-01-01", label=""):
    trades = []
    name = f"{NAME}{label}"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        sig = signals(df).to_numpy()
        h, c = df.High.to_numpy(), df.Close.to_numpy()
        a = atr(df).to_numpy()
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 30)
        while i < len(df) - 1:
            if not sig[i]:
                i += 1
                continue
            j = next((k for k in range(i + 1, len(df)) if c[k] > h[k - 1]), None)
            why = "signal" if j is not None else "end"
            j = len(df) - 1 if j is None else j
            trades.append(make_trade(name, sym, "long", df.index[i], c[i], c[i] - a[i], None,
                                     df.index[j], c[j], why))
            i = j + 1
    return trades
