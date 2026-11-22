"""Narrow Range Day NR7 – Toby Crabel ("Day Trading with Short Term Price Patterns and Opening
Range Breakout", 1990), beschrieben in der StockCharts ChartSchool:
chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/narrow-range-day-nr7

Regeln aus dem Artikel:
  NR7-Tag = Tag mit der kleinsten Spanne (Hoch − Tief) der letzten 7 Tage.
  Long, wenn der Kurs am Folgetag über das Hoch des NR7-Tags steigt; Short, wenn er unter
  das Tief fällt. Ein Bruch auf der Gegenseite macht das Signal ungültig (-> Stop).
  Crabel nahm Gewinne schnell mit: zum Schluss des ersten Tages oder beim ersten
  gewinnbringenden Schlusskurs.
Annahmen: Einstieg nur am Tag direkt nach dem NR7-Tag, per Stop-Order am Hoch (Short: Tief),
bei Kurslücke zur Eröffnung. Stop = Gegenseite des NR7-Tags. Durchbricht der Kurs am
Einstiegstag beide Seiten (Reihenfolge unbekannt), wird konservativ gerechnet: Einstieg auf
der Seite, die näher an der Eröffnung liegt, und am selben Tag ausgestoppt. Ausstieg beim
ersten Schlusskurs im Gewinn (Variante: Schluss des Einstiegstags). Stop vor Signal.
Tageskerzen seit 2005.
Vergleich: gleicher Ablauf mit jedem Vortag statt nur NR7-Tagen.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import make_trade


def run(symbols, start="2005-01-01", baseline=False, exit_rule="profit"):
    trades = []
    ex = "erster Gewinn-Schluss" if exit_rule == "profit" else "Schluss Einstiegstag"
    name = (f"Vergleich: Ausbruch aus jedem Vortag ({ex}, 1d)" if baseline
            else f"Crabel NR7 ({ex}, 1d)")
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 30:
            continue
        rng = df.High - df.Low
        nr = (rng <= rng.rolling(7).min()) if not baseline else pd.Series(True, df.index)
        nr = nr.to_numpy()
        O, H, L, C = (df[x].to_numpy() for x in ("Open", "High", "Low", "Close"))
        i = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 10)
        while i < len(df) - 1:
            j = i + 1
            if not nr[i]:
                i += 1
                continue
            up, dn = H[j] > H[i], L[j] < L[i]
            if not up and not dn:
                i += 1
                continue
            if up and dn:                         # beide Seiten: konservativ ein Verlust
                up = (H[i] - O[j]) <= (O[j] - L[i])
            side = "long" if up else "short"
            entry = max(O[j], H[i]) if up else min(O[j], L[i])
            stop = L[i] if up else H[i]
            if abs(entry - stop) < 1e-9:              # Spanne 0 (Datenlücke): kein Risiko messbar
                i += 1
                continue
            if H[j] > H[i] and L[j] < L[i]:
                trades.append(make_trade(name, sym, side, df.index[j], entry, stop, None,
                                         df.index[j], stop, "stop"))
                i = j
                continue
            k_out, px, why = len(df) - 1, C[-1], "end"
            for k in range(j, len(df)):
                if k > j:                         # Stop am Einstiegstag nicht prüfbar
                    if side == "long" and L[k] <= stop:
                        k_out, px, why = k, min(stop, O[k]), "stop"
                        break
                    if side == "short" and H[k] >= stop:
                        k_out, px, why = k, max(stop, O[k]), "stop"
                        break
                gain = C[k] > entry if side == "long" else C[k] < entry
                if exit_rule == "close" or gain:
                    k_out, px, why = k, C[k], "signal"
                    break
            trades.append(make_trade(name, sym, side, df.index[j], entry, stop, None,
                                     df.index[k_out], px, why))
            i = k_out
    return [x for x in trades if np.isfinite(x.r)]
