"""Trendfolge mit Donchian-Kanal + MACD – TradingView-Strategie von LordRobrecht,
tradingview.com/script/bGjB7COd (Pine-Code über pine-facade geladen)

Regeln aus dem Pine-Code (Standardwerte, Long und Short):
  * Long: Schluss über dem 50-Kerzen-Hoch (ohne aktuelle Kerze), MACD (12/26/9) über
    der Signallinie und Signallinie > 0.
  * Short: Schluss unter dem 50-Kerzen-Tief, MACD unter der Signallinie, Signallinie < 0.
  * Stop: 4 x ATR(14) vom Schluss der Signalkerze.
  * Long schließen: MACD kreuzt unter die Signallinie UND Signallinie < 0.
    Short schließen: MACD kreuzt über die Signallinie UND Signallinie > 0.
Besonderheiten des Originals: Der als "Trailing" gedachte Stop läuft wegen eines
Programmierfehlers (trail_offset ohne trail_points) nicht mit – er ist ein fester Stop.
Tritt das Einstiegssignal in offener Position erneut auf, setzt Pine den Stop neu auf
Schluss - 4 ATR (so auch hier). Kein Kursziel.
Annahmen: Signal zum Schluss, Ausführung zur nächsten Eröffnung; Gegensignal dreht die
Position. Tageskerzen seit 2005.
Vergleich: nur Donchian-Ausbruch ohne MACD-Bedingungen, gleicher Stop; Ausstieg nur
über Stop oder Gegensignal.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "Donchian 50 + MACD"


def run(symbols, start="2005-01-01", n=50, k=4.0, longs=True, shorts=True, baseline=False):
    trades = []
    name = "Vergleich: Donchian 50 ohne MACD (1d)" if baseline else f"{NAME} (1d)"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 2 * n:
            continue
        o, h, l, c = (df[x].values for x in ("Open", "High", "Low", "Close"))
        up = df.High.shift().rolling(n).max().values
        dn = df.Low.shift().rolling(n).min().values
        macd_s = df.Close.ewm(span=12, adjust=False).mean() - df.Close.ewm(span=26, adjust=False).mean()
        macd, sig = macd_s.values, macd_s.ewm(span=9, adjust=False).mean().values
        a = atr(df, 14).values
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), n + 30)
        pos, pending, stop, entry, risk, entry_t = 0, None, 0.0, 0.0, 0.0, None

        def close_pos(t, px, why):
            trades.append(make_trade(name, sym, "long" if pos == 1 else "short", entry_t,
                                     entry, entry - pos * risk, None, df.index[t], px, why))

        for t in range(first, len(df)):
            if pending is not None:
                side, new_stop = pending
                pending = None
                if side == 0:
                    close_pos(t, o[t], "signal"); pos = 0
                elif side != pos:
                    if pos != 0:
                        close_pos(t, o[t], "signal")
                    pos, entry, entry_t = side, o[t], df.index[t]
                    stop = new_stop
                    risk = abs(entry - stop)
                    if (pos == 1 and stop >= entry) or (pos == -1 and stop <= entry):
                        close_pos(t, o[t], "stop"); pos = 0
            if pos == 1 and l[t] <= stop:
                close_pos(t, min(stop, o[t]), "stop"); pos = 0
            elif pos == -1 and h[t] >= stop:
                close_pos(t, max(stop, o[t]), "stop"); pos = 0
            long_sig = c[t] > up[t] and (baseline or (macd[t] > sig[t] and sig[t] > 0))
            short_sig = c[t] < dn[t] and (baseline or (macd[t] < sig[t] and sig[t] < 0))
            close_long = not baseline and sig[t] > macd[t] and sig[t - 1] <= macd[t - 1] and sig[t] < 0
            close_short = not baseline and macd[t] > sig[t] and macd[t - 1] <= sig[t - 1] and sig[t] > 0
            if long_sig and longs:
                if pos == 1:
                    stop = c[t] - k * a[t]          # Pine setzt den Stop neu
                else:
                    pending = (1, c[t] - k * a[t])
            elif short_sig and shorts:
                if pos == -1:
                    stop = c[t] + k * a[t]
                else:
                    pending = (-1, c[t] + k * a[t])
            elif (close_long and pos == 1) or (close_short and pos == -1):
                pending = (0, 0.0)
            elif not longs and short_sig and pos == 1:
                pending = (0, 0.0)
        if pos != 0:
            close_pos(len(df) - 1, c[-1], "end")
    return trades
