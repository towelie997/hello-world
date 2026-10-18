"""Bollinger + RSI, Double Strategy v1.1 – ChartArt, TradingView (PUB;2187, 48.900 Likes),
tradingview.com/script/uCV8I4xA (Pine-Code über pubscripts-suggest-json geladen)

Regeln aus dem Pine-Code:
  * RSI(6) und Bollinger-Bänder (SMA 200, 2 Standardabweichungen) auf den Schlusskurs.
  * Long: RSI kreuzt über 50 UND Schluss kreuzt über das untere Band (gleiche Kerze).
  * Short: RSI kreuzt unter 50 UND Schluss kreuzt unter das obere Band.
  * Einstieg per Stop-Order am Band in der Folgekerze; Gegensignal dreht die Position.
  * KEIN Stop-Loss und kein Kursziel im Original.
Annahmen: Die Stop-Order liegt unter (Long) bzw. über (Short) dem Kurs und wird in der
Folgekerze praktisch sofort ausgelöst -> Ausführung zum Eröffnungskurs, mindestens am Band.
Tageskerzen seit 2005. "1 R" = 1 ATR(14) (nur Rechengröße).
Vergleich: nur die Bollinger-Kreuzung, ohne RSI-Bedingung.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, rsi
from ._reversal import run_reversal

NAME = "ChartArt Bollinger + RSI"


def run(symbols, start="2005-01-01", longs=True, shorts=True, baseline=False):
    trades = []
    if baseline:
        name = "Vergleich: nur Bollinger-Kreuz (1d)"
    else:
        name = f"{NAME} (1d{'' if shorts else ', nur Long'})"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 260:
            continue
        c = df.Close
        basis = c.rolling(200).mean()
        dev = 2 * c.rolling(200).std(ddof=0)
        lo, up = basis - dev, basis + dev
        r = rsi(c, 6)
        x_lo = (c > lo) & (c.shift() <= lo.shift())
        x_up = (c < up) & (c.shift() >= up.shift())
        r_up = (r > 50) & (r.shift() <= 50)
        r_dn = (r < 50) & (r.shift() >= 50)
        ls = (x_lo if baseline else x_lo & r_up).to_numpy()
        ss = (x_up if baseline else x_up & r_dn).to_numpy()
        o, lo_v, up_v = df.Open.to_numpy(), lo.to_numpy(), up.to_numpy()
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 201)
        trades += run_reversal(df, sym, name, ls, ss, first, longs, shorts,
                               fill_long=lambda t: max(o[t], lo_v[t - 1]),
                               fill_short=lambda t: min(o[t], up_v[t - 1]),
                               atr=atr(df).to_numpy())
    return trades
