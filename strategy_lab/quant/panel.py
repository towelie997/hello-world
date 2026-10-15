"""Kursdaten als Tabellen (Datum x Symbol), um Dividenden und Splits bereinigt
(Gesamtrendite) – für Portfolio-Strategien mit langen Haltedauern nötig."""

from __future__ import annotations

import os
import time

import pandas as pd
import yfinance as yf

from .. import data

PANEL_DIR = os.path.join(data.CACHE_DIR, "panels")


def load_adjusted(symbols: list[str], name: str, max_age_h: float = 24) -> dict[str, pd.DataFrame]:
    """{'Open','High','Low','Close','Volume': DataFrame} bereinigt, Tagesdaten seit Beginn."""
    os.makedirs(PANEL_DIR, exist_ok=True)
    path = os.path.join(PANEL_DIR, f"{name}.pkl")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < max_age_h * 3600:
        return pd.read_pickle(path)
    frames = []
    for i in range(0, len(symbols), 100):
        part = symbols[i:i + 100]
        for attempt in range(3):
            df = yf.download(part, period="max", interval="1d", auto_adjust=True,
                             progress=False, group_by="column", threads=True)
            if not df.empty:
                break
            time.sleep(10 * (attempt + 1))
        frames.append(df)
    df = pd.concat(frames, axis=1)
    out = {}
    for col in ("Open", "High", "Low", "Close", "Volume"):
        x = df[col]
        if isinstance(x, pd.Series):
            x = x.to_frame(symbols[0])
        x.index = pd.to_datetime(x.index).tz_localize(None).normalize()
        out[col] = x.loc[:, ~x.columns.duplicated()].sort_index()
    pd.to_pickle(out, path)
    return out
