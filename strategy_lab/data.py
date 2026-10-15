"""Kursdaten von Yahoo Finance mit lokalem Cache (yfinance drosselt viele Abrufe)."""

from __future__ import annotations

import os
import time as _time
from datetime import time

import pandas as pd
import yfinance as yf

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
NY = "America/New_York"


def load(symbol: str, interval: str, period: str) -> pd.DataFrame:
    """OHLC-Daten; Intraday-Index in New-York-Zeit, Tagesdaten mit Datumsindex."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{symbol}_{interval}_{period}.pkl".replace("=", "_"))
    if os.path.exists(path) and _time.time() - os.path.getmtime(path) < 12 * 3600:
        return pd.read_pickle(path)
    df = pd.DataFrame()
    for attempt in range(3):
        df = yf.download(symbol, period=period, interval=interval,
                         progress=False, auto_adjust=False)
        if not df.empty:
            break
        _time.sleep(5 * (attempt + 1))
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if interval == "1d" and "Volume" in df:
        vol = df["Volume"].copy()
        vol.index = pd.to_datetime(vol.index).tz_localize(None).normalize()
        vol.to_pickle(path.replace(".pkl", "_vol.pkl"))
    df = df[["Open", "High", "Low", "Close"]].dropna()
    if interval.endswith(("m", "h")):
        df.index = df.index.tz_convert(NY)
    else:
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
    df.to_pickle(path)
    return df


def load_volume(symbol: str) -> pd.Series:
    """Tägliche Stückzahl (Volume); wird beim Laden der Tageskerzen mitgespeichert."""
    path = os.path.join(CACHE_DIR, f"{symbol}_1d_max_vol.pkl".replace("=", "_"))
    price = os.path.join(CACHE_DIR, f"{symbol}_1d_max.pkl".replace("=", "_"))
    if not os.path.exists(path) and os.path.exists(price):
        os.remove(price)                       # Kurs-Cache ohne Volumen -> neu laden
    if not os.path.exists(path):
        load(symbol, "1d", "max")
    return pd.read_pickle(path) if os.path.exists(path) else pd.Series(dtype=float)


def regular_session(df: pd.DataFrame) -> pd.DataFrame:
    """Nur reguläre US-Handelszeit 9:30–16:00 New York."""
    t = df.index.time
    return df[(t >= time(9, 30)) & (t < time(16, 0))]


def complete_days(df: pd.DataFrame, last_bar: time) -> dict:
    """{datum: bars} für alle Tage, deren letzte Kerze mindestens `last_bar` erreicht."""
    days = {d: g for d, g in df.groupby(df.index.date)}
    return {d: g for d, g in days.items() if g.index[-1].time() >= last_bar}
