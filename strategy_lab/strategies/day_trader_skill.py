"""Day Trader Skill (Claude-Skill-Paket) – Jake Schincariol, github.com/Jakeschincariol/day-trader-skill
(Stand Commit 3d0f4ef, 20.10.2026; ca. 640 GitHub-Sterne). Regeln aus trader-entry/SKILL.md,
trader-exit/SKILL.md und trader-scanner/scan.py.

Regeln (Opening-Range-Breakout, nur Long, 5-Minuten-Kerzen, New-York-Zeit):
  Opening Range = Hoch/Tief der ersten 15 Minuten (Kerzen 9:30, 9:35, 9:40).
  Einstieg: erste abgeschlossene Kerze nach der Range, die ÜBER dem Range-Hoch SCHLIESST
  (ein Docht reicht nicht); Einstieg zu deren Schluss. Keine Einstiege nach 15:30.
  Ein Signal pro Tag und Wert. Stop = Mitte der Range (Standard "or-mid"),
  Ziel = 2 R (Standard) bzw. 1 R (Beispiel im README). Spätestens 15:55 glattstellen.
Annahmen: Der Skill ist ein Werkzeug, Ein-/Ausstieg nach seinen Standardwerten. Glattstellung
zum Schluss der 15:50-Kerze. Kein Long, wenn der Stop über dem Einstieg läge (der Skill
verweigert das ebenfalls). Der optionale Volumenfilter ("--min-volume-x") wird nicht getestet:
die Intraday-Daten hier enthalten kein Volumen. Die Tages-Setups des Scanners (breakout_20d, bull_flag, oversold …)
haben keine eigene Ausstiegsregel und werden nicht getestet.
Daten: Yahoo 5 Min, nur ca. 60 Handelstage -> kleine Stichprobe.
Vergleich: Kauf zum Schluss der ersten Kerze nach der Range (9:45) ohne Ausbruchsbedingung,
Stop im gleichen Abstand (halbe Range-Breite), gleiches Ziel und Glattstellung.
"""

from datetime import time

from .. import data
from ..engine import make_trade, simulate_exit


def run(symbols, rr=2.0, baseline=False):
    trades = []
    if baseline:
        name = f"Vergleich: Kauf 9:45 ohne Ausbruch ({rr:g}R)"
    else:
        name = f"Day Trader Skill ORB ({rr:g}R)"
    for sym in symbols:
        bars = data.regular_session(data.load(sym, "5m", "60d"))
        if bars.empty:
            continue
        for day, b in data.complete_days(bars, time(15, 50)).items():
            if len(b) < 6 or b.index[0].time() != time(9, 30):
                continue
            b = b[[t.time() <= time(15, 50) for t in b.index]]
            rng = b.iloc[:3]
            orh, orl = rng.High.max(), rng.Low.min()
            mid = (orh + orl) / 2
            for i in range(3, len(b) - 1):
                if b.index[i].time() > time(15, 25):          # Kerze schließt nach 15:30
                    break
                c = b.iloc[i].Close
                if baseline:
                    entry, stop = c, c - (orh - orl) / 2
                else:
                    if not c > orh:
                        continue
                    entry, stop = c, mid
                if stop >= entry:
                    break
                target = entry + rr * (entry - stop)
                t, px, why = simulate_exit(b, i + 1, "long", stop, target)
                trades.append(make_trade(name, sym, "long", b.index[i], entry, stop, target,
                                         t, px, why))
                break
    return trades
