"""Eigener Buchbestand des Bots (JSON), damit er nur seine eigenen Positionen handelt."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field


@dataclass
class State:
    positions: dict = field(default_factory=dict)  # sym -> {qty, entry_date, entry_price}
    pending: dict = field(default_factory=dict)    # sym -> {action, qty, date, ref_price}
    peak_equity: float = 0.0
    last_run: str = ""                              # Datum des letzten Order-Laufs
    halted: str = ""                                # Grund, falls Bot angehalten


def load(state_dir: str) -> State:
    path = os.path.join(state_dir, "state.json")
    if not os.path.exists(path):
        return State()
    with open(path) as f:
        return State(**json.load(f))


def save(state: State, state_dir: str) -> None:
    os.makedirs(state_dir, exist_ok=True)
    path = os.path.join(state_dir, "state.json")
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(asdict(state), f, indent=2, sort_keys=True)
    os.replace(tmp, path)


def reconcile(state: State, broker_pos: dict[str, dict]) -> list[str]:
    """Gleicht offene Orders vom Vortag mit dem Depot beim Broker ab.
    broker_pos: {sym: {"qty": float, "avg_cost": float}}. Gibt Warnungen zurück;
    bei Widersprüchen wird state.halted gesetzt (keine neuen Orders bis zur Prüfung)."""
    msgs = []
    for sym, p in list(state.pending.items()):
        held = broker_pos.get(sym, {}).get("qty", 0)
        if p["action"] == "BUY":
            if held >= p["qty"]:
                state.positions[sym] = {"qty": p["qty"], "entry_date": p["date"],
                                        "entry_price": broker_pos[sym]["avg_cost"]}
            else:
                msgs.append(f"Kauf {sym} ({p['qty']}) nicht ausgeführt – verworfen")
        else:
            if held == 0:
                state.positions.pop(sym, None)
            else:
                msgs.append(f"Verkauf {sym} nicht ausgeführt – noch {held} Stück im Depot")
        del state.pending[sym]
    for sym, p in list(state.positions.items()):
        held = broker_pos.get(sym, {}).get("qty", 0)
        if held == 0:
            # ganz weg: Stop-Order ausgelöst oder von Hand verkauft
            msgs.append(f"{sym} nicht mehr im Depot (Stop oder Handverkauf) – aus dem Bestand entfernt")
            del state.positions[sym]
        elif held != p["qty"]:
            state.halted = f"Depot passt nicht: {sym} Bot {p['qty']} / Broker {held}"
            msgs.append(state.halted)
    others = sorted(set(broker_pos) - set(state.positions))
    if others:
        msgs.append(f"Hinweis: fremde Positionen im Konto werden ignoriert: {', '.join(others)}")
    return msgs
