"""EMA50 Break + Pullback – Data Trader, youtu.be/7Ds9djcEKB4

Regeln aus dem Video:
  * Kurs lag unter dem 50er EMA und schließt darüber (Long; Short spiegelbildlich).
  * Pullback: mindestens zwei rote Kerzen in Folge. Linie am Hoch davor (Swing High).
  * Einstieg, wenn eine Kerze über dieser Linie schließt.
  * Ungültig, wenn der Kurs vorher wieder unter dem EMA schließt oder die
    Ausbruchskerze mehr als 3x so groß ist wie eine durchschnittliche Kerze.
  * Stop am Chandelier Stop (22 Kerzen, 3x ATR), Ziel 2:1.
Im Video auf Forex-Paaren gezeigt; getestet auf Forex und Aktien (1 Std, 2 Jahre)
sowie Aktien auf Tageskerzen.
"""

import pandas as pd

from .. import data
from ..engine import atr, make_trade, simulate_exit

NAME = "EMA50 Pullback"
PIP_COST = 0.75 * 0.0001  # Forex: 1,5 Pips pro Round-Turn


def run(symbols, interval="1h", period="730d", rr=2.0, start="2005-01-01"):
    trades = []
    for sym in symbols:
        df = data.load(sym, interval, period)
        if not sym.endswith("=X") and interval.endswith("h"):
            df = data.regular_session(df)
        if interval == "1d":
            df = df[df.index >= pd.Timestamp(start) - pd.Timedelta(days=400)]
        if len(df) < 100:
            continue
        cost = PIP_COST / df.Close.mean() if sym.endswith("=X") else None
        ema = df.Close.ewm(span=50, adjust=False).mean().values
        a = atr(df, 22).values
        hh = df.High.rolling(22).max().values
        ll = df.Low.rolling(22).min().values
        avg_rng = (df.High - df.Low).rolling(20).mean().values
        o, h, l, c = df.Open.values, df.High.values, df.Low.values, df.Close.values

        side, extreme, level, run_len = None, None, None, 0
        i = 60
        while i < len(df):
            # neuer EMA-Durchbruch
            if c[i - 1] < ema[i - 1] and c[i] > ema[i]:
                side, extreme, level, run_len = "long", h[i], None, 0
                i += 1
                continue
            if c[i - 1] > ema[i - 1] and c[i] < ema[i]:
                side, extreme, level, run_len = "short", l[i], None, 0
                i += 1
                continue
            if side is None:
                i += 1
                continue
            # Invalidierung: zurück auf die andere Seite des EMA
            if (side == "long" and c[i] < ema[i]) or (side == "short" and c[i] > ema[i]):
                side = None
                i += 1
                continue
            if level is None:
                against = c[i] < o[i] if side == "long" else c[i] > o[i]
                run_len = run_len + 1 if against else 0
                if not against:
                    extreme = max(extreme, h[i]) if side == "long" else min(extreme, l[i])
                if run_len >= 2:
                    level = extreme
                i += 1
                continue
            broke = c[i] > level if side == "long" else c[i] < level
            if broke:
                if h[i] - l[i] > 3 * avg_rng[i]:
                    side = None
                    i += 1
                    continue
                entry = c[i]
                stop = hh[i] - 3 * a[i] if side == "long" else ll[i] + 3 * a[i]
                if (side == "long" and stop < entry) or (side == "short" and stop > entry):
                    risk = abs(entry - stop)
                    target = entry + rr * risk if side == "long" else entry - rr * risk
                    t, px, why = simulate_exit(df, i + 1, side, stop, target, eod=False)
                    kw = {"cost": cost} if cost else {}
                    trades.append(make_trade(f"{NAME} ({interval})", sym, side, df.index[i],
                                             entry, stop, target, t, px, why, **kw))
                    i = df.index.get_loc(t) + 1
                    side = None
                    continue
                side = None
            i += 1
    return trades
