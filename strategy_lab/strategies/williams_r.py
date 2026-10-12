"""Williams %R Mean Reversion – The Transparent Trader, youtu.be/GyikfniCLqU

Regeln aus dem Video (GBP/USD, 30-Min-Kerzen):
  * Williams %R mit Länge 10.
  * Schluss unter -90 -> Kauf zur nächsten Eröffnung; über -10 -> Leerverkauf.
  * Stop-and-Reverse: das Gegensignal schließt die Position und dreht sie.
  * Stop 250 Pips.
  * Verbesserung "filter": Long nur, wenn der Vortag stark war (Schluss > Eröffnung),
    Short nur, wenn er schwach war.
  * Verbesserung "day": zusätzlich Ausstieg um 17:00 New York (Ende Forex-Tag).
Kosten: 1,5 Pips pro Round-Turn statt prozentualer Kosten.
Daten: 30-Min-Kerzen nur ~60 Tage, daher zusätzlich 1-Std-Kerzen (2 Jahre).
"""

from datetime import time

import pandas as pd

from .. import data
from ..engine import make_trade

NAME = "Williams %R"
PIP = 0.0001


def run(symbols, interval="30m", period="60d", variant="base", length=10, stop_pips=250):
    trades = []
    for sym in symbols:
        df = data.load(sym, interval, period)
        if df.empty:
            continue
        daily = data.load(sym, "1d", "5y")
        prev_strong = (daily.Close > daily.Open).shift(1)
        prev_strong.index = prev_strong.index.date
        hh, ll = df.High.rolling(length).max(), df.Low.rolling(length).min()
        wr = -100 * (hh - df.Close) / (hh - ll)
        cost = 0.75 * PIP / df.Close.mean()   # je Seite

        bar_len = pd.Timedelta(interval.replace("m", "min"))
        pos = None  # (side, entry_idx, entry, stop)

        def close_pos(idx, price, why):
            side, ei, entry, stop = pos
            trades.append(make_trade(f"{NAME} ({interval}, {variant})", sym, side, df.index[ei],
                                     entry, stop, None, df.index[idx], price, why, cost=cost))

        for i in range(length, len(df) - 1):
            bar = df.iloc[i]
            # Stop prüfen
            if pos is not None:
                side, ei, entry, stop = pos
                if (side == "long" and bar.Low <= stop) or (side == "short" and bar.High >= stop):
                    close_pos(i, stop, "stop")
                    pos = None
            bar_end = (df.index[i] + bar_len).time()
            if pos is not None and variant == "day" and df.index[i].time() < time(17, 0) \
                    and (bar_end >= time(17, 0) or bar_end < df.index[i].time()):
                close_pos(i, bar.Close, "eod")
                pos = None
            signal = "long" if wr.iloc[i] < -90 else "short" if wr.iloc[i] > -10 else None
            if signal is None:
                continue
            nxt = df.iloc[i + 1]
            if pos is not None and pos[0] != signal:
                close_pos(i + 1, nxt.Open, "signal")
                pos = None
            if pos is None:
                if variant in ("filter", "day"):
                    strong = prev_strong.get(df.index[i].date())
                    if strong is None or pd.isna(strong) or (signal == "long") != bool(strong):
                        continue
                entry = nxt.Open
                stop = entry - stop_pips * PIP if signal == "long" else entry + stop_pips * PIP
                pos = (signal, i + 1, entry, stop)
        if pos is not None:
            close_pos(len(df) - 1, df.iloc[-1].Close, "end")
    return trades
