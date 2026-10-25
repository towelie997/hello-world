"""6 Larry-Connors-Strategien (von Quantified Strategies leicht abgewandelt),
youtu.be/gX8FjjKR7ec – nach Connors, "High Probability ETF Trading" und "Short Term
Trading Strategies That Work".

Regeln aus dem Video (alle nur Long, nur wenn Schluss > SMA200, Ein-/Ausstieg zum Schluss):
  double5     Schluss auf 5-Tage-Tief -> Verkauf bei Schluss auf 5-Tage-Hoch.
  tage_runter Schluss < SMA5 und mind. 4 der letzten 5 Tage tiefer geschlossen
              -> Verkauf bei Schluss > Vortageshoch.
  prozent_b   %b(5 Tage, 2 Std.-Abw.) < 0,2 an 3 Tagen in Folge -> Verkauf bei Schluss > Vortageshoch.
  r3          RSI(2) 3 Tage in Folge gefallen und heute < 20 -> Verkauf bei RSI(2) > 70.
  rsi5        RSI(5) < 30 -> Verkauf, wenn RSI(5) über 50 kreuzt.
  drei_tage   Hoch und Tief 3 Tage in Folge tiefer -> Ausstieg im Video nicht genannt;
              Annahme: Schluss > Vortageshoch (Standard-Ausstieg von Quantified Strategies).
KEIN Stop-Loss im Video. "1 R" = 1 ATR(14) (nur Rechengröße). Tageskerzen seit 2005.
Vergleich: "roter Tag > SMA200" aus connors_rsi2.py.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade, rsi

TITLES = {"double5": "Double 5", "tage_runter": "4 von 5 Tagen runter", "prozent_b": "%b 3 Tage",
          "r3": "R3", "rsi5": "RSI(5) 30/50", "drei_tage": "3 Tage tiefere Hochs/Tiefs"}


def run(symbols, rule, start="2005-01-01"):
    trades = []
    name = f"QS/Connors {TITLES[rule]} (1d)"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 250:
            continue
        o, h, l, c = df.Open, df.High, df.Low, df.Close
        ok = c > c.rolling(200).mean()
        if rule == "double5":
            sig = c <= c.rolling(5).min()
            ex = (c >= c.rolling(5).max()).to_numpy()
        elif rule == "tage_runter":
            sig = (c < c.rolling(5).mean()) & ((c < c.shift()).astype(int).rolling(5).sum() >= 4)
        elif rule == "prozent_b":
            m, sd = c.rolling(5).mean(), c.rolling(5).std(ddof=0)
            pb = (c - (m - 2 * sd)) / (4 * sd)
            sig = (pb < 0.2).astype(int).rolling(3).sum() == 3
        elif rule == "r3":
            r2 = rsi(c, 2)
            fell = r2 < r2.shift()
            sig = fell & fell.shift(fill_value=False) & fell.shift(2, fill_value=False) & (r2 < 20)
            ex = (r2 > 70).to_numpy()
        elif rule == "rsi5":
            r5 = rsi(c, 5)
            sig = r5 < 30
            ex = ((r5 > 50) & (r5.shift() <= 50)).to_numpy()
        elif rule == "drei_tage":
            lower = (h < h.shift()) & (l < l.shift())
            sig = lower & lower.shift(fill_value=False) & lower.shift(2, fill_value=False)
        if rule in ("tage_runter", "prozent_b", "drei_tage"):
            ex = (c > h.shift()).to_numpy()
        sig = (sig & ok).to_numpy()
        C, a = c.to_numpy(), atr(df).to_numpy()
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 200)
        while i < len(df) - 1:
            if not sig[i]:
                i += 1
                continue
            j = next((k for k in range(i + 1, len(df)) if ex[k]), None)
            why = "signal" if j is not None else "end"
            j = len(df) - 1 if j is None else j
            trades.append(make_trade(name, sym, "long", df.index[i], C[i], C[i] - a[i], None,
                                     df.index[j], C[j], why))
            i = j + 1
    return trades
