"""Moving Momentum – Arthur Hill, StockCharts ChartSchool
chartschool.stockcharts.com/.../trading-strategies/moving-momentum

Regeln aus dem Artikel:
  * Trend: SMA(20) über SMA(150) = nur Long; darunter = nur Short.
  * Rücksetzer: Stochastik fällt unter 20 (Long) bzw. steigt über 80 (Short).
  * Auslöser: MACD-Histogramm (12, 26, 9) dreht ins Positive (Long) bzw. Negative (Short).
Annahmen (im Artikel nicht festgelegt):
  * Stochastik = %K(14) mit 3-Tage-Glättung; der Rücksetzer muss in den letzten 10 Tagen
    vor dem Histogramm-Signal gelegen haben. Einstieg zum Schluss der Signalkerze.
  * Anfangs-Stop am Tief (Long) bzw. Hoch (Short) der letzten 10 Tage ("Unterstützung").
  * Ausstieg: Stop oder Trendwechsel (SMA20 kreuzt SMA150), zum Schluss.
Tageskerzen seit 2005. Vergleich: dieselben Regeln ohne die Stochastik-Bedingung.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import make_trade

NAME = "Moving Momentum"


def run(symbols, start="2005-01-01", longs=True, shorts=True, baseline=False, lookback=10):
    trades = []
    if baseline:
        name = "Vergleich: Moving Momentum ohne Stochastik (1d)"
    else:
        name = f"{NAME} (1d{'' if shorts else ', nur Long'})"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 200:
            continue
        o, h, l, c = (df[k] for k in ("Open", "High", "Low", "Close"))
        s20, s150 = c.rolling(20).mean(), c.rolling(150).mean()
        k = 100 * (c - l.rolling(14).min()) / (h.rolling(14).max() - l.rolling(14).min())
        stoch = k.rolling(3).mean()
        macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        hist = macd - macd.ewm(span=9, adjust=False).mean()
        pull_l = (stoch < 20).rolling(lookback).max().astype(bool)
        pull_s = (stoch > 80).rolling(lookback).max().astype(bool)
        up = (hist > 0) & (hist.shift() <= 0)
        dn = (hist < 0) & (hist.shift() >= 0)
        bull = s20 > s150
        long_sig = (bull & up & (baseline | pull_l)).to_numpy()
        short_sig = (~bull & dn & (baseline | pull_s) & s150.notna()).to_numpy()
        lo10 = l.rolling(lookback).min().to_numpy()
        hi10 = h.rolling(lookback).max().to_numpy()
        bv = bull.to_numpy()
        O, H, L, C = o.to_numpy(), h.to_numpy(), l.to_numpy(), c.to_numpy()
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 160)
        while i < len(df) - 1:
            side = 1 if (longs and long_sig[i]) else -1 if (shorts and short_sig[i]) else 0
            if side == 0:
                i += 1
                continue
            entry = C[i]
            stop = lo10[i] if side == 1 else hi10[i]
            if (side == 1 and stop >= entry) or (side == -1 and stop <= entry):
                i += 1
                continue
            exit_t, px, why = None, None, None
            for j in range(i + 1, len(df)):
                if side == 1 and L[j] <= stop:
                    exit_t, px, why = j, min(stop, O[j]), "stop"
                    break
                if side == -1 and H[j] >= stop:
                    exit_t, px, why = j, max(stop, O[j]), "stop"
                    break
                if bv[j] != (side == 1):
                    exit_t, px, why = j, C[j], "signal"
                    break
            if exit_t is None:
                exit_t, px, why = len(df) - 1, C[-1], "end"
            trades.append(make_trade(name, sym, "long" if side == 1 else "short", df.index[i],
                                     entry, stop, None, df.index[exit_t], px, why))
            i = exit_t + 1
    return trades
