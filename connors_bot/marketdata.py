"""Tagesschlüsse der Vortage von Yahoo (wie im Backtest: unbereinigt um Dividenden)."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from .universe import yahoo_symbol


def daily_closes(symbols: list[str], today: pd.Timestamp) -> dict[str, pd.Series]:
    """{symbol: Schlusskurse} – nur abgeschlossene Tage VOR `today`."""
    ysyms = [yahoo_symbol(s) for s in symbols]
    df = yf.download(ysyms, period="2y", interval="1d", auto_adjust=False,
                     progress=False, group_by="column", threads=True)
    close = df["Close"] if isinstance(df.columns, pd.MultiIndex) else df[["Close"]].rename(
        columns={"Close": ysyms[0]})
    close.index = pd.to_datetime(close.index).tz_localize(None).normalize()
    close = close[close.index < today]
    return {s: close[y].dropna() for s, y in zip(symbols, ysyms) if y in close}
