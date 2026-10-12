"""5-Min Range + Fair Value Gap – Casper Trading, youtu.be/mzFXoK2pbNE

Regeln aus dem Video:
  * Hoch/Tief der ersten 5-Minuten-Kerze (9:30–9:35 NY) markieren.
  * Auf dem 1-Minuten-Chart auf einen Ausbruch mit Schlusskurs außerhalb warten.
  * Einstieg, sobald ein Fair Value Gap (Lücke zwischen Kerze 1 und Kerze 3)
    in Ausbruchsrichtung entsteht – zum Schluss der dritten Kerze.
  * Stop an der Basis der Kerze, die zuerst außerhalb der Range geschlossen hat.
  * Ziel fest 1:2.
Annahmen: Fällt der Kurs in die Range zurück, beginnt die Suche neu;
ein Trade pro Tag; Einstieg bis 11:00; Ausstieg spätestens zum Handelsschluss.
Daten: Yahoo liefert 1-Minuten-Kerzen nur für die letzten ~8 Tage.
"""

from datetime import time

from .. import data
from ..engine import make_trade, simulate_exit

NAME = "5-Min Range + FVG (1 Min)"


def run(symbols, rr=2.0, cutoff=time(11, 0)):
    trades = []
    for sym in symbols:
        bars = data.regular_session(data.load(sym, "1m", "8d"))
        if bars.empty:
            continue
        for day, b in data.complete_days(bars, time(15, 55)).items():
            if len(b) < 10 or b.index[0].time() != time(9, 30):
                continue
            orh, orl = b.iloc[:5].High.max(), b.iloc[:5].Low.min()
            bo_side, bo_idx = None, None
            for i in range(5, len(b)):
                if b.index[i].time() > cutoff:
                    break
                c = b.iloc[i].Close
                if c > orh and bo_side != "long":
                    bo_side, bo_idx = "long", i
                elif c < orl and bo_side != "short":
                    bo_side, bo_idx = "short", i
                elif orl <= c <= orh:
                    bo_side, bo_idx = None, None
                if bo_side is None or i < 2 or i - 1 < bo_idx:
                    continue
                if bo_side == "long" and b.iloc[i].Low > b.iloc[i - 2].High:
                    stop = b.iloc[bo_idx].Low
                elif bo_side == "short" and b.iloc[i].High < b.iloc[i - 2].Low:
                    stop = b.iloc[bo_idx].High
                else:
                    continue
                entry = c
                risk = abs(entry - stop)
                if risk <= 0 or (bo_side == "long") != (entry > stop):
                    continue
                target = entry + rr * risk if bo_side == "long" else entry - rr * risk
                t, px, why = simulate_exit(b, i + 1, bo_side, stop, target)
                trades.append(make_trade(NAME, sym, bo_side, b.index[i], entry, stop, target, t, px, why))
                break
    return trades
