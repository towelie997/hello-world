"""Ichimoku-Cloud-Strategie – Trade Pro, youtu.be/KE_SAzserLE ("Complete Ichimoku Cloud
Trading Strategy", ca. 590.000 Aufrufe)

Regeln aus dem Video (Long; Short spiegelbildlich), Einstieg zum Schluss der Kerze, an der
erstmals ALLE vier Bedingungen erfüllt sind:
  1. Schluss über der Wolke (Wolke an der aktuellen Kerze).
  2. Die Wolke 26 Kerzen voraus ist grün (Senkou A > Senkou B, heute berechnet).
  3. Umwandlungslinie (Tenkan 9) über der Basislinie (Kijun 26).
  4. Nachlaufende Linie (Schluss, 26 Kerzen zurückversetzt) über der Wolke an jener Stelle.
  Stop "knapp unter der Wolke" (Short: über der Wolke), Ziel 2 R.
Annahmen: Standardwerte 9/26/52, Verschiebung 26. Stop = untere (Short: obere) Wolkenkante
beim Einstieg. Das Video nennt keinen Zeitrahmen; getestet mit Tageskerzen seit 2005.
Die optionalen Ausstiege (Lagging Span kreuzt Kurs, Basislinie als Trailing) sind nicht
Teil der Grundregeln und werden nicht genutzt. Eine Position je Wert.
Vergleich: nur Bedingung 1 (Schluss über/unter der Wolke, frisch), gleicher Stop/Ziel.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import make_trade, simulate_exit

NAME = "Trade Pro Ichimoku (1d)"


def mid(df, n):
    return (df.High.rolling(n).max() + df.Low.rolling(n).min()) / 2


def run(symbols, start="2005-01-01", baseline=False, shorts=True):
    trades = []
    name = "Vergleich: nur Schluss über/unter Wolke (1d)" if baseline else (
        NAME if shorts else "Trade Pro Ichimoku (1d, nur Long)")
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 300:
            continue
        c = df.Close
        tenkan, kijun = mid(df, 9), mid(df, 26)
        span_a, span_b = (tenkan + kijun) / 2, mid(df, 52)
        top = np.maximum(span_a.shift(26), span_b.shift(26))      # Wolke an Kerze t
        bot = np.minimum(span_a.shift(26), span_b.shift(26))
        lag_top = np.maximum(span_a.shift(52), span_b.shift(52))  # Wolke an Kerze t-26
        lag_bot = np.minimum(span_a.shift(52), span_b.shift(52))
        if baseline:
            lg, sh = c > top, c < bot
        else:
            lg = (c > top) & (span_a > span_b) & (tenkan > kijun) & (c > lag_top)
            sh = (c < bot) & (span_a < span_b) & (tenkan < kijun) & (c < lag_bot)
        lg = (lg & ~lg.shift(fill_value=False)).to_numpy()
        sh = (sh & ~sh.shift(fill_value=False)).to_numpy()
        C, T, B = c.to_numpy(), top.to_numpy(), bot.to_numpy()
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 80)
        while i < len(df) - 1:
            side = "long" if lg[i] else ("short" if (sh[i] and shorts) else None)
            if side is None:
                i += 1
                continue
            stop = B[i] if side == "long" else T[i]
            risk = C[i] - stop if side == "long" else stop - C[i]
            if not np.isfinite(risk) or risk <= 0:
                i += 1
                continue
            target = C[i] + 2 * risk if side == "long" else C[i] - 2 * risk
            t_out, px, why = simulate_exit(df, i + 1, side, stop, target, eod=False)
            trades.append(make_trade(name, sym, side, df.index[i], C[i], stop, target,
                                     t_out, px, why))
            i = df.index.get_loc(t_out) + 1
    return trades
