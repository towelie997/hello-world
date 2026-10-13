"""Robustheits-Prüfung für alle Strategien in results/trades.csv.

Grundsatz: Kein einzelner, von Hand gewählter Zeitraum darf das Urteil bestimmen.
Darum gibt es keine feste Trennung in "Entwicklung" und "Test", sondern:

1. Trennjahr-Sensitivität: Für JEDES mögliche Trennjahr (2008–2023) wird der
   Profit-Faktor vor und nach dem Trennjahr berechnet. Robust heißt: in allen
   Varianten auf beiden Seiten > 1.
2. Kalenderjahre: festes Raster, jedes Jahr einzeln (nur Jahre mit >= 5 Trades).
3. Marktphasen nach objektiver Regel statt nach Datum: "Bärenmarkt" = S&P 500
   (SPY) mehr als 20 % unter seinem bisherigen Höchststand am Einstiegstag.
   Erfasst 2008/09, COVID 2020 und 2022 automatisch, ohne Daten auszuwählen.
4. Zufallstest: gleiche Werte, gleiche Haltedauern, gleiche Kosten – aber
   zufällige Einstiegstage (N_SIM Durchläufe). p-Wert = Anteil der Zufalls-
   durchläufe, die mindestens so gut sind wie die Strategie.
5. Bootstrap: Trades N_BOOT-mal mit Zurücklegen gezogen -> 5-%-Quantil des PF.
6. Mehrfachtests: p-Werte des Zufallstests nach Holm korrigiert, weil viele
   Strategien getestet werden und sonst einige allein durch Glück auffallen.
7. Jüngere Jahre (nur Zusatzinfo, fließt NICHT ins Urteil ein): Profit-Faktor der
   letzten 5 Kalenderjahre, Anteil positiver Jahre mit Gewichtung nach Alter
   (letzte 5 Jahre x3, die 8 Jahre davor x2, ältere x1) und ein Hinweis, wenn die
   Strategie zuletzt klar schwächer ist (PF letzte 5 Jahre <= 1 oder < 80 % des
   Gesamt-PF). Die Jahre zählen relativ zum jüngsten Trade-Jahr in trades.csv.

Urteil "robust" (Kriterien vorab festgelegt, nicht nachträglich angepasst):
  a) Zufallstest: Holm-korrigiertes p < 0,05
  b) Bootstrap: 5-%-Quantil des Profit-Faktors > 1
  c) mindestens 70 % der Kalenderjahre mit Profit-Faktor > 1
  d) Trennjahr-Sensitivität: kleinster PF vor UND nach jedem Trennjahr > 1
Zufallstest und Trennjahre nur für Tages-/Wochenstrategien; Intraday-Daten
reichen dafür nicht (zu kurzer Zeitraum).

    python -m strategy_lab.robustness
"""

from __future__ import annotations

import math
import os

import numpy as np
import pandas as pd

from . import data
from .engine import DEFAULT_COST

HERE = os.path.dirname(__file__)
RESULTS = os.path.join(HERE, "results")
N_SIM = 1000
N_BOOT = 2000
SPLIT_YEARS = range(2008, 2024)
MIN_TRADES_YEAR = 5
SEED = 42
RECENT_YEARS = 5                       # "letzte Jahre" – nur Zusatzinfo
YEAR_WEIGHTS = ((5, 3), (13, 2))       # (Alter < x Jahre, Gewicht); sonst Gewicht 1
RECENT_WARN_RATIO = 0.8


def profit_factor(x: np.ndarray) -> float:
    gains, losses = x[x > 0].sum(), -x[x <= 0].sum()
    return float(gains / losses) if losses > 0 else math.inf


def is_daily(df: pd.DataFrame) -> bool:
    """Tages-/Wochenstrategie: Einstiegszeiten ohne Uhrzeit (00:00)."""
    t = pd.to_datetime(df.entry_time, utc=True, format="mixed")
    return bool((t.dt.hour == 0).all() and t.dt.year.min() < 2015)


def bear_market_days() -> pd.Series:
    """True an Tagen, an denen SPY > 20 % unter seinem bisherigen Hoch liegt."""
    spy = data.load("SPY", "1d", "max").Close
    return (spy / spy.cummax() - 1) < -0.20


def holm(pvals: dict) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for k, (name, p) in enumerate(items):
        running = max(running, min(1.0, (m - k) * p))
        out[name] = running
    return out


def random_entry_test(g: pd.DataFrame, rng: np.random.Generator) -> tuple[float, float, float]:
    """PF (auf % je Trade) der Strategie vs. zufällige Einstiege mit gleicher Haltedauer."""
    sims = np.zeros((N_SIM, 0))
    actual = []
    for sym, gs in g.groupby("symbol"):
        px = data.load(sym, "1d", "max")
        if px.empty:
            continue
        close = px.Close.to_numpy()
        idx = px.index
        ent = idx.searchsorted(pd.to_datetime(gs.entry_time, utc=True, format="mixed")
                               .dt.tz_localize(None).dt.normalize())
        ext = idx.searchsorted(pd.to_datetime(gs.exit_time, utc=True, format="mixed")
                               .dt.tz_localize(None).dt.normalize())
        hold = np.clip(ext - ent, 1, None)
        lo = idx.searchsorted(pd.to_datetime(gs.entry_time, utc=True, format="mixed")
                              .dt.tz_localize(None).min())
        hi = len(close) - 1 - hold
        ok = hi > lo
        if not ok.any():
            continue
        hold, hi = hold[ok], hi[ok]
        actual.append(gs.pct.to_numpy()[ok])
        starts = rng.integers(lo, hi + 1, size=(N_SIM, len(hold)))
        ret = close[starts + hold] / close[starts] - 1 - 2 * DEFAULT_COST
        sims = np.concatenate([sims, 100 * ret], axis=1)
    if sims.shape[1] == 0:
        return math.nan, math.nan, math.nan
    act = profit_factor(np.concatenate(actual))
    sim_pf = np.array([profit_factor(row) for row in sims])
    p = (1 + (sim_pf >= act).sum()) / (N_SIM + 1)
    return act, float(np.median(sim_pf)), float(p)


def year_weight(age: int) -> int:
    return next((w for limit, w in YEAR_WEIGHTS if age < limit), 1)


def analyze(name: str, g: pd.DataFrame, bear: pd.Series, rng, last_year: int) -> dict:
    r = g.r.to_numpy()
    t = pd.to_datetime(g.entry_time, utc=True, format="mixed").dt.tz_localize(None)
    row = {"strategie": name, "trades": len(g), "pf": round(profit_factor(r), 2)}

    boot = [profit_factor(rng.choice(r, size=len(r), replace=True)) for _ in range(N_BOOT)]
    row["pf_boot_5%"] = round(float(np.quantile(boot, 0.05)), 2)

    if not is_daily(g):
        row["typ"] = "intraday"
        return row
    row["typ"] = "tages/wochen"

    years = pd.Series(r).groupby(t.dt.year.to_numpy())
    yearly = {y: profit_factor(v.to_numpy()) for y, v in years if len(v) >= MIN_TRADES_YEAR}
    row["jahre"] = len(yearly)
    row["jahre_pf>1_%"] = round(100 * np.mean([v > 1 for v in yearly.values()]), 0)
    worst = min(yearly, key=yearly.get)
    row["schlechtestes_jahr"] = f"{worst} ({yearly[worst]:.2f})"

    recent = (t.dt.year > last_year - RECENT_YEARS).to_numpy()
    recent_years = {y: v for y, v in yearly.items() if y > last_year - RECENT_YEARS}
    weights = {y: year_weight(last_year - y) for y in yearly}
    row["pf_letzte5"] = round(profit_factor(r[recent]), 2) if recent.sum() >= 10 else math.nan
    row["trades_letzte5"] = int(recent.sum())
    row["jahre_letzte5_pf>1"] = f"{sum(v > 1 for v in recent_years.values())}/{len(recent_years)}"
    row["jahre_pf>1_gewichtet_%"] = round(
        100 * sum(w for y, w in weights.items() if yearly[y] > 1) / sum(weights.values()), 0)
    pf5 = row["pf_letzte5"]
    row["hinweis_letzte5"] = ("zuletzt schwächer" if not math.isnan(pf5)
                              and (pf5 <= 1 or pf5 < RECENT_WARN_RATIO * row["pf"]) else "")

    before, after = [], []
    for y in SPLIT_YEARS:
        b, a = r[(t.dt.year < y).to_numpy()], r[(t.dt.year >= y).to_numpy()]
        if len(b) >= 20 and len(a) >= 20:
            before.append(profit_factor(b))
            after.append(profit_factor(a))
    row["split_min_vorher"] = round(min(before), 2) if before else math.nan
    row["split_min_nachher"] = round(min(after), 2) if after else math.nan

    in_bear = bear.reindex(t.dt.normalize(), method="ffill").fillna(False).to_numpy()
    row["pf_baerenmarkt"] = round(profit_factor(r[in_bear]), 2) if in_bear.sum() >= 10 else math.nan
    row["trades_baerenmarkt"] = int(in_bear.sum())
    row["pf_ohne_baerenmarkt"] = round(profit_factor(r[~in_bear]), 2)

    act, med, p = random_entry_test(g, rng)
    row["pf_pct"] = round(act, 2)
    row["pf_zufall_median"] = round(med, 2)
    row["p_zufall"] = p
    return row


def main():
    df = pd.read_csv(os.path.join(RESULTS, "trades.csv"))
    rng = np.random.default_rng(SEED)
    bear = bear_market_days()
    last_year = int(pd.to_datetime(df.entry_time, utc=True, format="mixed").dt.year.max())
    rows = [analyze(name, g, bear, rng, last_year) for name, g in df.groupby("strategy", sort=False)]
    out = pd.DataFrame(rows)

    daily = out[out.typ == "tages/wochen"]
    adj = holm(dict(zip(daily.strategie, daily.p_zufall)))
    out["p_zufall_holm"] = out.strategie.map(adj)

    def verdict(x):
        if x.typ != "tages/wochen":
            return "nein" if x["pf_boot_5%"] <= 1 and x.pf <= 1 else "zu wenig Daten"
        checks = [x.p_zufall_holm < 0.05, x["pf_boot_5%"] > 1, x["jahre_pf>1_%"] >= 70,
                  x.split_min_vorher > 1 and x.split_min_nachher > 1]
        return "robust" if all(checks) else f"nein ({sum(checks)}/4)"

    out["urteil"] = out.apply(verdict, axis=1)
    out = out.sort_values(["typ", "pf"], ascending=[False, False])
    out.to_csv(os.path.join(RESULTS, "robustness.csv"), index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(out.to_string(index=False))


if __name__ == "__main__":
    main()
