"""Momentum-Filter vor jede Long-Strategie schalten (Aktienauswahl).

Frage: Wird eine Strategie besser, wenn sie nur Aktien mit Momentum kauft?
Vorgehen: Die vorhandenen Trades aus results/trades.csv werden gefiltert – ein Trade
bleibt nur, wenn die Aktie am Einstieg das Momentum-Kriterium erfüllt. Gemessen wird
mit Daten BIS ZUM VORTAG (Wochenstrategien: bis zur Vorwoche), also ohne Blick in die
Zukunft. Geprüft werden nur reine Long-Strategien auf Tages-/Wochenkerzen mit der
ganzen SWING-Liste.

Kriterien (alle vorab festgelegt, Standardwerte aus der Literatur, nicht optimiert):
  sma200       Schluss über dem 200-Tage-Durchschnitt (Trendfilter, Faber 2007)
  abs_12_1     Rendite 12 Monate ohne letzten Monat > 0 (absolutes Momentum)
  rel_12_1     12-1-Rendite in der oberen Hälfte der SWING-Liste (relatives Momentum,
               Jegadeesh/Titman 1993) – die eigentliche Aktienauswahl
  rel_6m       6-Monats-Rendite in der oberen Hälfte der SWING-Liste
  rs_spy_6m    6-Monats-Rendite besser als SPY (relative Stärke zum Markt)
  near_52w     Schluss höchstens 10 % unter dem 52-Wochen-Hoch (George/Hwang 2004)
  dual         rel_12_1 UND abs_12_1 (Dual Momentum, Antonacci)

Kontrolle: Zufallstest wie in robustness.py, aber die zufälligen Einstiege werden nur aus
Tagen gezogen, an denen derselbe Filter erfüllt ist. So wird getrennt:
  pf_zufall_filter = was der Filter ALLEIN bringt (zufälliger Einstieg in Momentum-Aktien)
  p_signal         = ob das Signal der Strategie darüber hinaus etwas bringt
p-Werte nach Holm über alle Kombinationen korrigiert.
Vereinfachung: Gefilterte Trades werden nicht durch Trades ersetzt, die wegen der
"eine Position pro Wert"-Regel ursprünglich ausgelassen wurden.

    python -m strategy_lab.momentum_filter     (nach run_all)
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd

from . import data
from .engine import DEFAULT_COST
from .robustness import RECENT_YEARS, holm, profit_factor
from .run_all import SWING

HERE = os.path.dirname(__file__)
RESULTS = os.path.join(HERE, "results")
N_SIM = 5000
SEED = 7
FILTERS = ["sma200", "abs_12_1", "rel_12_1", "rel_6m", "rs_spy_6m", "near_52w", "dual"]


def momentum_flags(universe=SWING) -> dict[str, pd.DataFrame]:
    """{kriterium: DataFrame Datum x Symbol (bool)}, Stand jeweils Tagesschluss.
    Feiertage verschiedener Börsen (DAX/USA): letzter Schluss wird bis zu 5 Tage fortgeschrieben."""
    close = pd.DataFrame({s: data.load(s, "1d", "max").Close for s in universe}).sort_index()
    close = close[close.index >= "1995-01-01"].ffill(limit=5)
    spy = data.load("SPY", "1d", "max").Close.reindex(close.index).ffill(limit=5)
    r12_1 = close.shift(21) / close.shift(252) - 1
    r6 = close / close.shift(126) - 1
    rank = lambda x: x.rank(axis=1, pct=True) > 0.5
    f = {
        "sma200": close > close.rolling(200).mean(),
        "abs_12_1": r12_1 > 0,
        "rel_12_1": rank(r12_1) & r12_1.notna(),
        "rel_6m": rank(r6) & r6.notna(),
        "rs_spy_6m": r6.gt(spy / spy.shift(126) - 1, axis=0),
        "near_52w": close >= 0.9 * close.rolling(252).max(),
    }
    f["dual"] = f["rel_12_1"] & f["abs_12_1"]
    return {k: v.fillna(False) for k, v in f.items()}, close


def flag_at_entry(flags: pd.DataFrame, g: pd.DataFrame) -> np.ndarray:
    weekly = g.strategy.iloc[0].endswith("(1w)")
    t = pd.to_datetime(g.entry_time).dt.normalize() - pd.Timedelta(days=7 if weekly else 1)
    out = np.zeros(len(g), dtype=bool)
    for sym in g.symbol.unique():
        m = (g.symbol == sym).to_numpy()
        col = flags[sym]
        pos = col.index.searchsorted(t[m], side="right") - 1
        out[m] = np.where(pos >= 0, col.to_numpy()[np.clip(pos, 0, None)], False)
    return out


def random_pf(g: pd.DataFrame, close: pd.DataFrame, allowed: pd.DataFrame, rng,
              n_sim: int = N_SIM) -> np.ndarray:
    """PF (in %) zufälliger Einstiege an erlaubten Tagen, gleiche Werte und Haltedauern."""
    gains, losses = np.zeros(n_sim), np.zeros(n_sim)
    for sym, gs in g.groupby("symbol"):
        px = close[sym].dropna()
        idx = px.index
        ent = idx.searchsorted(pd.to_datetime(gs.entry_time).dt.normalize())
        ext = idx.searchsorted(pd.to_datetime(gs.exit_time).dt.normalize())
        hold = np.clip(ext - ent, 1, None)
        ok_days = np.flatnonzero(allowed[sym].reindex(idx, fill_value=False).to_numpy()
                                 & (idx >= pd.Timestamp("2005-01-01")))
        if len(ok_days) == 0:
            continue
        c = px.to_numpy()
        starts = rng.choice(ok_days, size=(n_sim, len(hold)))
        ends = np.minimum(starts + hold, len(c) - 1)
        ret = 100 * (c[ends] / c[starts] - 1 - 2 * DEFAULT_COST)
        gains += np.where(ret > 0, ret, 0).sum(axis=1)
        losses -= np.where(ret <= 0, ret, 0).sum(axis=1)
    return np.where(losses > 0, gains / np.where(losses > 0, losses, 1), np.inf)


def main(universe=SWING, src: str = "trades.csv", dst: str = "momentum_filter.csv",
         n_sim: int = N_SIM):
    trades = pd.read_csv(os.path.join(RESULTS, src))
    trades = trades[~trades.entry_time.str.contains(":") | trades.entry_time.str.endswith("00:00:00")]
    flags, close = momentum_flags(universe)
    everything = pd.DataFrame(True, index=close.index, columns=close.columns)
    rng = np.random.default_rng(SEED)
    rows = []
    for name, g in trades.groupby("strategy", sort=False):
        t = pd.to_datetime(g.entry_time, format="mixed")
        if (g.side != "long").any() or t.dt.year.min() > 2008 or g.symbol.nunique() < 0.9 * len(universe):
            continue
        last_year = t.dt.year.max()
        for fname in ["ohne Filter"] + FILTERS:
            keep = np.ones(len(g), bool) if fname == "ohne Filter" else flag_at_entry(flags[fname], g)
            gf = g[keep]
            if len(gf) < 30:
                continue
            tf = pd.to_datetime(gf.entry_time, format="mixed")
            yearly = [profit_factor(v.to_numpy()) for _, v in gf.r.groupby(tf.dt.year) if len(v) >= 5]
            recent = (tf.dt.year > last_year - RECENT_YEARS).to_numpy()
            act = profit_factor(gf.pct.to_numpy())
            sim = random_pf(gf, close, everything if fname == "ohne Filter" else flags[fname], rng, n_sim)
            rows.append({
                "strategie": name, "filter": fname, "trades": len(gf),
                "anteil_%": round(100 * len(gf) / len(g)),
                "pf": round(profit_factor(gf.r.to_numpy()), 2),
                "pf_letzte5": round(profit_factor(gf.r.to_numpy()[recent]), 2) if recent.sum() >= 10 else np.nan,
                "jahre_pf>1_%": round(100 * np.mean([y > 1 for y in yearly])),
                "avg_pct": round(gf.pct.mean(), 3),
                "pf_pct": round(act, 2),
                "pf_zufall_filter": round(float(np.median(sim)), 2),
                "p_signal": (1 + (sim >= act).sum()) / (n_sim + 1),
            })
    out = pd.DataFrame(rows)
    adj = holm({i: p for i, p in out.p_signal.items()})
    out["p_signal_holm"] = out.index.map(adj).round(4)
    base = out[out["filter"] == "ohne Filter"].set_index("strategie").pf
    out["pf_aenderung"] = (out.pf - out.strategie.map(base)).round(2)
    out.to_csv(os.path.join(RESULTS, dst), index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30, "display.max_rows", 500):
        print(out.to_string(index=False))
        print("\nØ PF-Änderung je Filter (über alle Strategien):")
        print(out[out["filter"] != "ohne Filter"].groupby("filter")
              [["pf_aenderung", "anteil_%"]].mean().round(2).sort_values("pf_aenderung", ascending=False))


if __name__ == "__main__":
    main()
