"""Pattern Scalp – The Rumers, youtu.be/T0H_jpQXdVI

Regeln aus dem Video:
  * Erste 15-Minuten-Kerze abwarten und Hoch/Tief markieren.
  * Nur handeln, wenn sie eine "Manipulationskerze" ist: Spanne > 20 % der
    durchschnittlichen Tagesspanne (ATR 14 auf Tageskerzen).
  * Gegen die Richtung dieser Kerze handeln (Umkehr).
  * Auf 5-Min-Kerzen auf eine "John Wick"-Kerze warten (Hammer bzw. Shooting Star).
    Einstieg, sobald eine spätere Kerze deren Hoch (Long) / Tief (Short) bricht.
  * Stop am Tagestief (Long) bzw. Tageshoch (Short).
  * Ziel: andere Seite der Eröffnungs-Range.
Annahmen: Docht >= 2x Körper und >= 50 % der Kerzenspanne; ab der dritten
5-Min-Kerze; Einstieg bis 12:00; Ausstieg spätestens zum Handelsschluss.
Die "Power of Tower"-Variante (Engulfing, Einstieg bei 50 %) ist nicht enthalten.
"""

from datetime import time

from .. import data
from ..engine import atr, make_trade, simulate_exit

NAME = "Pattern Scalp (Rumers)"


def _is_wick(bar, side):
    rng = bar.High - bar.Low
    if rng <= 0:
        return False
    body = abs(bar.Close - bar.Open)
    wick = (min(bar.Open, bar.Close) - bar.Low) if side == "long" else (bar.High - max(bar.Open, bar.Close))
    return wick >= 2 * body and wick >= 0.5 * rng


def run(symbols, atr_pct=0.20, cutoff=time(12, 0)):
    trades = []
    for sym in symbols:
        bars = data.regular_session(data.load(sym, "5m", "60d"))
        if bars.empty:
            continue
        daily = data.load(sym, "1d", "2y")
        datr = atr(daily)
        for day, b in data.complete_days(bars, time(15, 55)).items():
            if len(b) < 6 or b.index[0].time() != time(9, 30):
                continue
            hist = datr[datr.index.date < day]
            if hist.empty:
                continue
            orh, orl = b.iloc[:3].High.max(), b.iloc[:3].Low.min()
            if orh - orl <= atr_pct * hist.iloc[-1]:
                continue
            side = "short" if b.iloc[2].Close > b.iloc[0].Open else "long"
            target = orh if side == "long" else orl
            wick_bar = None
            for i in range(2, len(b)):
                if b.index[i].time() > cutoff:
                    break
                bar = b.iloc[i]
                if wick_bar is not None:
                    hit = bar.High > wick_bar.High if side == "long" else bar.Low < wick_bar.Low
                    if hit:
                        entry = max(wick_bar.High, bar.Open) if side == "long" else min(wick_bar.Low, bar.Open)
                        upto = b.iloc[: i + 1]
                        stop = upto.Low.min() if side == "long" else upto.High.max()
                        if (side == "long" and target <= entry) or (side == "short" and target >= entry):
                            break
                        t, px, why = simulate_exit(b, i + 1, side, stop, target)
                        trades.append(make_trade(NAME, sym, side, b.index[i], entry, stop, target, t, px, why))
                        break
                if _is_wick(bar, side):
                    wick_bar = bar
    return trades
