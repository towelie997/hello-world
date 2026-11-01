"""Buy&Sell Strategy depends on AO+Stoch+RSI+ATR – SerdarYILMAZ, TradingView
(PUB;TfrUjDEBUT7M7cNaUcJOBmhkoI0Syx58, ca. 14.400 Likes), tradingview.com/script/RpYoQCVJ.
Pine-Code über pine-facade geladen.
Hinweis des Autors im Code: nur zum Lernen von Pine, nicht zum Handeln gedacht.

Regeln aus dem Pine-Code:
  Stochastik k = SMA3(stoch(14)); RSI(10); Awesome Oscillator AO = SMA5(hl2) - SMA34(hl2);
  ATR = RMA14(True Range).
  Long:  k < 20 und RSI < 30 und AO steigt (AO > AO der Vorkerze).
  Short: k > 80 und RSI > 70 und AO fällt.
  Stop = Tief − ATR (Short: Hoch + ATR), Ziel = Schluss + ATR (Short: Schluss − ATR),
  beide aus der Signalkerze. Einstieg zur Eröffnung der Folgekerze (Pine-Standard).
Annahmen: eine Position je Wert; Signale während einer offenen Position werden ignoriert
(in Pine würden gleichgerichtete Signale Stop/Ziel neu setzen und Gegensignale drehen –
das ist selten). Stop/Ziel können schon in der Einstiegskerze greifen, Stop vor Ziel.
Tageskerzen seit 2005.
Vergleich: nur Stochastik (k < 20 bzw. > 80), gleicher Stop/Ziel.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade, rsi, simulate_exit

NAME = "SerdarYILMAZ AO+Stoch+RSI+ATR (1d)"


def run(symbols, start="2005-01-01", baseline=False, shorts=True):
    trades = []
    name = "Vergleich: nur Stochastik 20/80 + ATR (1d)" if baseline else (
        NAME if shorts else "SerdarYILMAZ AO+Stoch+RSI+ATR (1d, nur Long)")
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        h, l, c = df.High, df.Low, df.Close
        k = (100 * (c - l.rolling(14).min()) / (h.rolling(14).max() - l.rolling(14).min())
             ).rolling(3).mean()
        hl2 = (h + l) / 2
        ao = hl2.rolling(5).mean() - hl2.rolling(34).mean()
        r = rsi(c, 10)
        if baseline:
            lg, sh = k < 20, k > 80
        else:
            lg = (k < 20) & (r < 30) & (ao > ao.shift())
            sh = (k > 80) & (r > 70) & (ao < ao.shift())
        lg, sh = lg.to_numpy(), sh.to_numpy()
        A = atr(df).to_numpy()
        O, H, L, C = (df[x].to_numpy() for x in ("Open", "High", "Low", "Close"))
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 40)
        while i < len(df) - 1:
            side = "long" if lg[i] else ("short" if (sh[i] and shorts) else None)
            if side is None:
                i += 1
                continue
            if side == "long":
                stop, target = L[i] - A[i], C[i] + A[i]
            else:
                stop, target = H[i] + A[i], C[i] - A[i]
            entry = O[i + 1]
            if (side == "long" and entry <= stop) or (side == "short" and entry >= stop):
                i += 1                     # Eröffnung schon jenseits des Stops: kein Trade
                continue
            t_out, px, why = simulate_exit(df, i + 1, side, stop, target, eod=False)
            trades.append(make_trade(name, sym, side, df.index[i + 1], entry, stop, target,
                                     t_out, px, why))
            i = df.index.get_loc(t_out) + 1
    return trades
