"""Entscheidet, welche Orders heute gesendet werden (ohne Broker-Zugriff, gut testbar)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .signals import is_entry, is_exit


@dataclass
class Intent:
    action: str        # "BUY" / "SELL"
    symbol: str
    qty: int
    price: float       # Referenzkurs (Kurs kurz vor Schluss)
    reason: str


def plan(positions: dict, kpis: dict[str, dict], equity: float, cash: float,
         peak_equity: float, max_positions: int, rsi_entry: float = 5.0,
         max_drawdown: float = 0.25) -> tuple[list[Intent], list[str]]:
    """positions: Bot-Positionen {sym: {qty, ...}}; kpis: {sym: snapshot()} mit Live-Kurs.
    equity: Depotwert für die Positionsgröße (USD); cash: verfügbares Geld (USD)."""
    intents, msgs = [], []
    # 1) Verkäufe: Schluss > SMA5 (fehlt der Kurs, wird gehalten und gewarnt)
    for sym, p in positions.items():
        k = kpis.get(sym)
        if k is None:
            msgs.append(f"Kein Kurs für {sym} – Position bleibt")
            continue
        if is_exit(k):
            intents.append(Intent("SELL", sym, int(p["qty"]), k["close"], "Schluss > SMA5"))
    # 2) Notbremse
    if peak_equity > 0 and equity < (1 - max_drawdown) * peak_equity:
        msgs.append(f"NOTBREMSE: Depot {equity:,.0f} $ liegt mehr als {max_drawdown:.0%} unter "
                    f"dem Höchststand {peak_equity:,.0f} $ – keine neuen Käufe")
        return intents, msgs
    # 3) Käufe: niedrigster RSI(2) zuerst, bis die Plätze voll sind
    free = max_positions - len(positions) + sum(i.action == "SELL" for i in intents)
    cands = sorted((k["rsi2"], sym) for sym, k in kpis.items()
                   if sym not in positions and is_entry(k, rsi_entry))
    budget = equity / max_positions
    money = cash + sum(i.qty * i.price for i in intents)   # Verkaufserlöse zum selben Schluss
    for _, sym in cands:
        if free <= 0:
            break
        price = kpis[sym]["close"]
        qty = math.floor(min(budget, money) / price)
        if qty < 1:
            msgs.append(f"{sym}: Kurs {price:.2f} $ zu hoch für {budget:,.0f} $ je Position")
            continue
        intents.append(Intent("BUY", sym, qty, price, f"RSI(2) {kpis[sym]['rsi2']:.1f}"))
        money -= qty * price
        free -= 1
    return intents, msgs
