"""Glow Ribbon Flip – TradingView-Strategie von blitz_locked,
tradingview.com/script/OUOx3rYT (Pine-Code über pine-facade geladen)

Regeln aus dem Pine-Code (Standardwerte, Long und Short):
  * Basis = EMA(21), Band = Basis -/+ 2 x ATR(10). Das untere Band steigt nur
    (wie ein Supertrend), das obere fällt nur, solange der Kurs nicht durchbricht.
  * Trendwechsel ("Flip"): Schluss unter dem alten unteren Band -> Abwärtstrend,
    Schluss über dem alten oberen Band -> Aufwärtstrend. Flip = Einstieg in neue Richtung.
  * Pullback-Wiedereinstieg: ohne Position im Trend, Schluss kreuzt die EMA in
    Trendrichtung -> Einstieg.
  * Stop = aktuelles Band (wandert mit), Ziel = 2 R; R = Abstand Schluss–Band beim Signal.
Annahmen: Signal zum Kerzenschluss, Ausführung zur nächsten Eröffnung (wie Pine). Ziel
bezogen auf den tatsächlichen Einstiegskurs. Stop vor Ziel in derselben Kerze.
Positionsgröße und Hebel des Originals spielen für R keine Rolle. Tageskerzen seit 2005.
Vergleich: Schluss kreuzt die EMA21 -> Einstieg in diese Richtung, fester Stop 2 ATR(10),
Ziel 2 R (also ohne das mitlaufende Band und ohne Flip-Logik).
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "Glow Ribbon Flip"


def _bands(df, base_len=21, atr_len=10, mult=2.0):
    c = df.Close.values
    basis = df.Close.ewm(span=base_len, adjust=False).mean().values
    a = atr(df, atr_len).values
    lo_new, hi_new = basis - mult * a, basis + mult * a
    n = len(df)
    lo, hi, d = np.full(n, np.nan), np.full(n, np.nan), np.zeros(n, dtype=int)
    for t in range(n):
        if t == 0:
            lo[t], hi[t] = lo_new[t], hi_new[t]
            d[t] = 1 if c[t] > basis[t] else -1
            continue
        plo, phi = lo[t - 1], hi[t - 1]
        lo[t] = lo_new[t] if (lo_new[t] > plo or c[t - 1] < plo) else plo
        hi[t] = hi_new[t] if (hi_new[t] < phi or c[t - 1] > phi) else phi
        d[t] = d[t - 1]
        if d[t - 1] == 1 and c[t] < plo:
            d[t] = -1
        elif d[t - 1] == -1 and c[t] > phi:
            d[t] = 1
    return basis, a, lo, hi, d


def run(symbols, start="2005-01-01", longs=True, shorts=True, rr=2.0, baseline=False):
    trades = []
    if baseline:
        name = "Vergleich: EMA21-Kreuz, fester Stop (1d)"
    else:
        name = f"{NAME} (1d{'' if shorts else ', nur Long'})"
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 100:
            continue
        o, h, l, c = (df[k].values for k in ("Open", "High", "Low", "Close"))
        basis, a, lo, hi, d = _bands(df)
        first = int(np.searchsorted(df.index, pd.Timestamp(start)))
        pos, pending = 0, None          # pending = (Richtung, R-Abstand) für nächste Eröffnung
        entry = stop = target = dist = 0.0
        entry_t = None

        def close_pos(t, px, why):
            trades.append(make_trade(name, sym, "long" if pos == 1 else "short", entry_t,
                                     entry, entry - pos * dist, target, df.index[t], px, why))

        for t in range(max(first, 30), len(df)):
            # 1) Order aus der Vorkerze zur Eröffnung ausführen
            if pending is not None:
                side, pdist = pending
                pending = None
                if side == 0:
                    close_pos(t, o[t], "signal")
                    pos = 0
                elif side != pos:
                    if pos != 0:
                        close_pos(t, o[t], "signal")
                    pos, entry, dist, entry_t = side, o[t], pdist, df.index[t]
                    target = entry + pos * rr * dist
                    if baseline:
                        stop = entry - pos * dist
            # 2) Stop / Ziel innerhalb der Kerze (Stop zuerst)
            if pos == 1 and l[t] <= stop:
                close_pos(t, min(stop, o[t]), "stop"); pos = 0
            elif pos == 1 and h[t] >= target:
                close_pos(t, max(target, o[t]), "target"); pos = 0
            elif pos == -1 and h[t] >= stop:
                close_pos(t, max(stop, o[t]), "stop"); pos = 0
            elif pos == -1 and l[t] <= target:
                close_pos(t, min(target, o[t]), "target"); pos = 0
            # 3) Signale zum Schluss
            if baseline:
                up = c[t] > basis[t] and c[t - 1] <= basis[t - 1]
                dn = c[t] < basis[t] and c[t - 1] >= basis[t - 1]
                if up and longs and pos != 1:
                    pending = (1, 2 * a[t])
                elif dn and shorts and pos != -1:
                    pending = (-1, 2 * a[t])
                elif (up and pos == -1) or (dn and pos == 1):
                    pending = (0, 0.0)
                continue
            line = lo[t] if d[t] == 1 else hi[t]
            gap = abs(c[t] - line)
            flip_bull, flip_bear = d[t] == 1 and d[t - 1] != 1, d[t] == -1 and d[t - 1] != -1
            pull_bull = d[t] == 1 and d[t - 1] == 1 and c[t] > basis[t] and c[t - 1] <= basis[t - 1] and pos == 0
            pull_bear = d[t] == -1 and d[t - 1] == -1 and c[t] < basis[t] and c[t - 1] >= basis[t - 1] and pos == 0
            if gap > 0:
                if flip_bull:
                    pending = (1, gap) if longs else ((0, 0.0) if pos == -1 else None)
                elif flip_bear:
                    pending = (-1, gap) if shorts else ((0, 0.0) if pos == 1 else None)
                elif pull_bull and longs:
                    pending = (1, gap)
                elif pull_bear and shorts:
                    pending = (-1, gap)
            # 4) Stop folgt dem Band (gilt ab der nächsten Kerze)
            if pos == 1 and d[t] == 1:
                stop = lo[t]
            elif pos == -1 and d[t] == -1:
                stop = hi[t]
            if pending is not None and pending[0] != 0:
                stop = lo[t] if pending[0] == 1 else hi[t]
        if pos != 0:
            close_pos(len(df) - 1, c[-1], "end")
    return trades
