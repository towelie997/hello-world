"""S&P-500-Liste (Wikipedia), wöchentlich zwischengespeichert, mit Ersatz aus dem Repo."""

from __future__ import annotations

import io
import os
import time

import pandas as pd
import requests

URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def sp500(cache_dir: str) -> list[str]:
    """Symbole im Wikipedia-Format (z. B. BRK.B)."""
    path = os.path.join(cache_dir, "sp500.csv")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < 7 * 86400:
        return pd.read_csv(path).symbol.tolist()
    try:
        html = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
        syms = sorted(pd.read_html(io.StringIO(html))[0].Symbol.astype(str))
        if len(syms) < 490:
            raise ValueError(f"nur {len(syms)} Symbole")
        os.makedirs(cache_dir, exist_ok=True)
        pd.DataFrame({"symbol": syms}).to_csv(path, index=False)
        return syms
    except Exception:
        if os.path.exists(path):
            return pd.read_csv(path).symbol.tolist()
        from strategy_lab.universe import SP500_ALL      # Ersatz: Liste aus dem Repo
        return [s.replace("-", ".") for s in SP500_ALL]


def yahoo_symbol(sym: str) -> str:
    return sym.replace(".", "-")


def ib_symbol(sym: str) -> str:
    return sym.replace(".", " ")
