"""Wochen-Ausbruch aus Konsolidierung – Financial Wisdom, youtu.be/tPjz1esBQVc

Regeln aus dem Video (nur Long, Wochenkerzen):
  * Enge Seitwärtsphase ("Box") über mindestens 6 Wochenkerzen.
  * Ausbruchswoche schließt über dem Box-Hoch; Ausbruchsgröße (Schluss - Eröffnung
    der Ausbruchskerze) mindestens 2 % (Scanner-Filter; Wunsch des Autors: 5 %).
  * Einstieg: Kauf-Stop knapp über dem Schluss der Ausbruchswoche (in der Folgewoche).
  * Stop: Tief der Ausbruchskerze (Alternative im Video: unterer Teil der Box).
  * Ausstieg: Schließt die MACD-Linie (12/26/9) unter der Signallinie, wird das Tief
    dieser Woche markiert; fällt der Kurs danach darunter, wird verkauft.
Nicht programmierbar und weggelassen: Marktkapitalisierung > 500 Mio., Fundamentaldaten,
Scanner-Bewertung, "sauberes" Chartbild nach Augenmaß.
Annahmen: "eng" = Spanne der 6 Box-Wochen (Hoch bis Tief) höchstens 15 % vom Tief.
Kauf-Stop nur in der direkten Folgewoche gültig. Liegt das Wochentief der Einstiegswoche
unter dem Stop, gilt der Stop als ausgelöst (konservativ, Reihenfolge im Wochenbalken
unbekannt). Die MACD-Marke bleibt bis zum Ausstieg bestehen; neue Kreuzungen setzen sie neu.
Vergleich: jeder Wochenschluss über dem 6-Wochen-Hoch (ohne Enge, ohne Mindestgröße).
"""

import pandas as pd

from .. import data
from ..engine import make_trade
from .squeeze_swing import _weekly

NAME = "Wochen-Ausbruch + MACD-Ausstieg (1w)"


def run(symbols, start="2005-01-01", box=6, max_range=0.15, min_size=0.02, baseline=False):
    trades = []
    name = "Vergleich: 6-Wochen-Hoch-Ausbruch (1w)" if baseline else NAME
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if df.empty:
            continue
        w = _weekly(df)
        if len(w) < 60:
            continue
        o, h, l, c = w.Open, w.High, w.Low, w.Close
        box_hi = h.shift().rolling(box).max()
        box_lo = l.shift().rolling(box).min()
        tight = (box_hi - box_lo) / box_lo <= max_range
        size_ok = (c - o) / o >= min_size
        breakout = c > box_hi
        sig = breakout if baseline else breakout & tight & size_ok
        macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        bear_cross = (macd < macd.ewm(span=9, adjust=False).mean()) & \
                     (macd.shift() >= macd.ewm(span=9, adjust=False).mean().shift())
        i = box + 30
        while i < len(w) - 1:
            if w.index[i] < pd.Timestamp(start) or not sig.iloc[i]:
                i += 1
                continue
            trigger = c.iloc[i] * 1.001
            k = i + 1
            if h.iloc[k] < trigger:
                i += 1
                continue
            entry = max(o.iloc[k], trigger)
            stop = l.iloc[i]
            if stop >= entry:
                i += 1
                continue
            mark, exit_t, exit_px, why = None, None, None, None
            for j in range(k, len(w)):
                level = stop if mark is None else max(stop, mark)
                if l.iloc[j] <= level:
                    exit_t, exit_px = w.index[j], min(level, o.iloc[j]) if j > k else level
                    why = "stop" if mark is None or stop >= mark else "signal"
                    break
                if bear_cross.iloc[j]:
                    mark = l.iloc[j]
            if exit_t is None:
                exit_t, exit_px, why = w.index[-1], c.iloc[-1], "end"
            trades.append(make_trade(name, sym, "long", w.index[k], entry, stop, None,
                                     exit_t, exit_px, why))
            i = w.index.get_loc(exit_t) + 1
    return trades
