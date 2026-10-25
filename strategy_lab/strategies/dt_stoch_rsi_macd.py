"""Stochastik + RSI + MACD – Data Trader, youtu.be/hh3BKTFE1dc

Regeln aus dem Video (im Video EUR/USD, 30 Minuten):
  * Long: Stochastik %K und %D beide im überverkauften Bereich (< 20); danach RSI(14) > 50
    und MACD-Linie kreuzt über die Signallinie, ohne dass die Stochastik zwischendurch
    überkauft (> 80) war.
  * Short: spiegelbildlich (beide > 80, RSI < 50, MACD kreuzt nach unten, nicht < 20 zwischendurch).
  * Stop: am nächsten Swing-Tief/-Hoch, höchstens 0,15 % vom Einstieg (Tipp aus dem Video).
  * Ziel: 1,5 x Risiko. Nur eine Position gleichzeitig.
Annahmen: Stochastik (14, 3, 3); MACD (12, 26, 9) mit EMAs; Swing-Tief = tiefstes Tief der
letzten 10 Kerzen; Einstieg zur Eröffnung der Folgekerze. Kosten 1,5 Pips je Trade (wie
Williams %R). Getestet auf FOREX_WIDE mit 30 Min (60 Tage) und 1 Std (2 Jahre).
Vergleich: dieselben Regeln ohne die Stochastik-Bedingung.
"""

import numpy as np

from .. import data
from ..engine import make_trade, rsi, simulate_exit

NAME = "Data Trader Stoch+RSI+MACD"


def run(symbols, interval="30m", period="60d", baseline=False, max_stop=0.0015, rr=1.5):
    trades = []
    name = (f"Vergleich: MACD+RSI ohne Stochastik ({interval})" if baseline
            else f"{NAME} ({interval})")
    for sym in symbols:
        df = data.load(sym, interval, period)
        if len(df) < 100:
            continue
        pip = 0.01 if "JPY" in sym else 0.0001
        cost = 0.75 * pip / df.Close.mean()
        h, l, c = df.High, df.Low, df.Close
        k_raw = 100 * (c - l.rolling(14).min()) / (h.rolling(14).max() - l.rolling(14).min())
        k = k_raw.rolling(3).mean()
        d = k.rolling(3).mean()
        r = rsi(c, 14).to_numpy()
        macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        sig = macd.ewm(span=9, adjust=False).mean()
        x_up = ((macd > sig) & (macd.shift() <= sig.shift())).to_numpy()
        x_dn = ((macd < sig) & (macd.shift() >= sig.shift())).to_numpy()
        K, D = k.to_numpy(), d.to_numpy()
        lo10, hi10 = l.rolling(10).min().to_numpy(), h.rolling(10).max().to_numpy()
        O = df.Open.to_numpy()
        arm_l = arm_s = False
        i = 40
        while i < len(df) - 1:
            if K[i] < 20 and D[i] < 20:
                arm_l, arm_s = True, False
            elif K[i] > 80 and D[i] > 80:
                arm_s, arm_l = True, False
            side = 0
            if x_up[i] and r[i] > 50 and (baseline or arm_l):
                side = 1
            elif x_dn[i] and r[i] < 50 and (baseline or arm_s):
                side = -1
            if side == 0:
                i += 1
                continue
            entry = O[i + 1]
            if side == 1:
                stop = max(lo10[i], entry * (1 - max_stop))
            else:
                stop = min(hi10[i], entry * (1 + max_stop))
            risk = abs(entry - stop)
            if not np.isfinite(risk) or risk <= 0 or (side == 1 and stop >= entry) or (side == -1 and stop <= entry):
                i += 1
                continue
            target = entry + side * rr * risk
            t, px, why = simulate_exit(df, i + 1, "long" if side == 1 else "short", stop, target, eod=False)
            trades.append(make_trade(name, sym, "long" if side == 1 else "short", df.index[i + 1],
                                     entry, stop, target, t, px, why, cost=cost))
            i = df.index.get_loc(t) + 1
            arm_l = arm_s = False
    return trades
