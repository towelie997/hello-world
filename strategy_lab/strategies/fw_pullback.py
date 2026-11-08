"""Pullback-Strategie – Financial Wisdom, youtu.be/AKkeB8RJ6jM ("The Only Pullback Strategy
You'll Ever Need", ca. 129.000 Aufrufe)

Regeln aus dem Video (nur Long, Tageskerzen):
  1. Gesamtmarkt im Aufwärtstrend: EMA(10) über EMA(20) (Kanal-eigene Regel).
  2. Aktie im Aufwärtstrend mit steigendem 50-Tage-Durchschnitt.
  3. Rücksetzer von etwa 10–20 % vom jüngsten Hoch an eine Unterstützung (21-Tage-EMA
     oder 50-Tage-Linie).
  4. Einstieg Methode 1: Umkehrtag – eröffnet schwach, schließt stark.
  5. Stop knapp unter dem Tief des Umkehrtags.
Annahmen (im Video nicht genau festgelegt):
  Markt = SPY, EMA10 > EMA20 am Signaltag (gilt auch für DAX-Werte).
  Trend = Schluss > SMA(50) und SMA(50) höher als vor 20 Tagen.
  Rücksetzer = Tief des Umkehrtags 10–20 % unter dem höchsten Hoch der letzten 20 Tage und
  Tief <= EMA(21) (Berührung der Unterstützung).
  Umkehrtag = Eröffnung unter dem Vortagesschluss, Schluss über der Eröffnung und in der
  oberen Hälfte der Tagesspanne. Volumen ("vorzugsweise höher") nicht verlangt.
  Einstieg zum Schluss, Stop = Tief des Umkehrtags. Ausstieg nennt das Video nicht; das
  Beispiel spricht von 1:4 -> Ziel 4 R. "Überzeugung"/Fundamentaldaten nicht programmierbar.
Vergleich: Umkehrtag im Aufwärtstrend ohne Marktfilter und ohne 10–20 %-Rücksetzer.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import make_trade, simulate_exit

NAME = "Financial Wisdom Pullback (1d)"


def run(symbols, start="2005-01-01", baseline=False, rr=4.0):
    trades = []
    name = "Vergleich: Umkehrtag im Aufwärtstrend (1d)" if baseline else NAME
    spy = data.load("SPY", "1d", "max").Close
    market = (spy.ewm(span=10, adjust=False).mean() > spy.ewm(span=20, adjust=False).mean())
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 120:
            continue
        o, h, l, c = df.Open, df.High, df.Low, df.Close
        sma50 = c.rolling(50).mean()
        trend = (c > sma50) & (sma50 > sma50.shift(20))
        rev = (o < c.shift()) & (c > o) & (c > (h + l) / 2)
        sig = trend & rev
        if not baseline:
            dd = 1 - l / h.rolling(20).max()
            ema21 = c.ewm(span=21, adjust=False).mean()
            mk = market.reindex(df.index, method="ffill").fillna(False).astype(bool)
            sig = sig & mk & (dd >= 0.10) & (dd <= 0.20) & (l <= ema21)
        sig = sig.to_numpy()
        L, C = l.to_numpy(), c.to_numpy()
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 70)
        while i < len(df) - 1:
            if not sig[i] or C[i] <= L[i]:
                i += 1
                continue
            stop = L[i]
            target = C[i] + rr * (C[i] - stop)
            t_out, px, why = simulate_exit(df, i + 1, "long", stop, target, eod=False)
            trades.append(make_trade(name, sym, "long", df.index[i], C[i], stop, target,
                                     t_out, px, why))
            i = df.index.get_loc(t_out) + 1
    return trades
