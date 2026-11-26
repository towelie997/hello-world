"""Trades in mehreren gzip-Teildateien speichern (GitHub nimmt keine Datei über 100 MB).

    write_trades(df, ".../big/trades.csv.gz")  ->  big/trades-01.csv.gz, trades-02.csv.gz, ...
    read_trades(".../big/trades.csv.gz")       ->  alle Teile wieder zusammen (oder die
                                                   Einzeldatei, falls es sie noch gibt)

Strategien werden nie auf zwei Teile verteilt. Ein Teil hat höchstens MAX_ROWS Zeilen
(bisher etwa 27 Byte je Zeile komprimiert -> ca. 30 MB je Teil, viel Abstand zur Grenze).
"""

from __future__ import annotations

import glob
import os

import pandas as pd

MAX_ROWS = 1_000_000


def _parts(path: str) -> list[str]:
    stem = path[: -len(".csv.gz")] if path.endswith(".csv.gz") else path
    return sorted(glob.glob(f"{stem}-[0-9][0-9].csv.gz"))


def read_trades(path: str) -> pd.DataFrame:
    if os.path.exists(path):
        return pd.read_csv(path)
    parts = _parts(path)
    if not parts:
        raise FileNotFoundError(path)
    return pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)


def write_trades(df: pd.DataFrame, path: str, max_rows: int = MAX_ROWS) -> list[str]:
    stem = path[: -len(".csv.gz")]
    for old in _parts(path) + ([path] if os.path.exists(path) else []):
        os.remove(old)
    groups, cur, n = [], [], 0
    for _, g in df.groupby("strategy", sort=False):
        if cur and n + len(g) > max_rows:
            groups.append(cur)
            cur, n = [], 0
        cur.append(g)
        n += len(g)
    if cur:
        groups.append(cur)
    out = []
    for k, gs in enumerate(groups, 1):
        p = f"{stem}-{k:02d}.csv.gz"
        pd.concat(gs).to_csv(p, index=False)
        out.append(p)
    return out
