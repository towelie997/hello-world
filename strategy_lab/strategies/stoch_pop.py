"""Stochastic Pop and Drop – StockCharts ChartSchool (Arthur Hill), nach Jake Bernstein und
David Steckler (Stocks & Commodities, Aug. 2000).
chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/stochastic-pop-and-drop

Regeln aus dem Artikel:
  Long ("Pop"):  Stochastik(70) > 50 (Trend-Bias), ADX(14) < 20 (Seitwärtsphase),
                 Stochastik(14) steigt über 80, Volumen über dem 250-Tage-Schnitt.
  Short ("Drop"): Stochastik(70) < 50, ADX(14) < 20, Stochastik(14) fällt unter 20
                 (Volumen bei Short laut Artikel weniger wichtig -> nicht verlangt).
  Stop: unter dem Tief vor dem Anstieg (Short: über dem Hoch).
  Ausstieg: Stochastik(14) fällt unter 50 (Short: steigt über 50).
Annahmen: Stochastik als %K geglättet mit 3 (SharpCharts-Standard "Slow"). Stop = tiefstes
Tief (Short: höchstes Hoch) der letzten 10 Kerzen. Einstieg und Signal-Ausstieg zum
Schluss, Stop untertägig. Parabolic SAR als Alternative nicht genutzt. Tageskerzen seit 2005.
Vergleich: ohne ADX- und Volumenfilter (nur Bias + Stochastik-Kreuz).
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import make_trade
from .qs5 import adx

NAME = "ChartSchool Stochastic Pop & Drop (1d)"


def stoch(df, n, smooth=3):
    lo, hi = df.Low.rolling(n).min(), df.High.rolling(n).max()
    return (100 * (df.Close - lo) / (hi - lo)).rolling(smooth).mean()


def run(symbols, start="2005-01-01", baseline=False, shorts=True):
    trades = []
    name = "Vergleich: Stochastik-Kreuz ohne ADX/Volumen (1d)" if baseline else (
        NAME if shorts else "ChartSchool Stochastic Pop (1d, nur Long)")
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 300:
            continue
        vol = data.load_volume(sym).reindex(df.index)
        k14, k70, a14 = stoch(df, 14), stoch(df, 70), adx(df, 14)
        quiet = a14 < 20
        loud = vol > vol.rolling(250).mean()
        lg = (k70 > 50) & (k14 > 80) & (k14.shift() <= 80)
        sh = (k70 < 50) & (k14 < 20) & (k14.shift() >= 20)
        if not baseline:
            lg, sh = lg & quiet & loud, sh & quiet
        lg, sh = lg.to_numpy(), sh.to_numpy()
        K = k14.to_numpy()
        O, H, L, C = (df[x].to_numpy() for x in ("Open", "High", "Low", "Close"))
        lo10, hi10 = df.Low.rolling(10).min().to_numpy(), df.High.rolling(10).max().to_numpy()
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 260)
        while i < len(df) - 1:
            side = "long" if lg[i] else ("short" if (sh[i] and shorts) else None)
            if side is None:
                i += 1
                continue
            stop = lo10[i] if side == "long" else hi10[i]
            if (side == "long" and stop >= C[i]) or (side == "short" and stop <= C[i]):
                i += 1
                continue
            j, px, why = len(df) - 1, C[-1], "end"
            for k in range(i + 1, len(df)):
                if side == "long" and L[k] <= stop:
                    j, px, why = k, min(stop, O[k]), "stop"
                    break
                if side == "short" and H[k] >= stop:
                    j, px, why = k, max(stop, O[k]), "stop"
                    break
                if (side == "long" and K[k] < 50) or (side == "short" and K[k] > 50):
                    j, px, why = k, C[k], "signal"
                    break
            trades.append(make_trade(name, sym, side, df.index[i], C[i], stop, None,
                                     df.index[j], px, why))
            i = j + 1
    return trades
