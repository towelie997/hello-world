"""Welche Momentum-Kandidaten werden die größten Gewinner? – Vorab festgelegte Prüfung.

    python -m strategy_lab.quant.momentum_research   (schreibt results/quant/momentum_*.csv)

Vorgehen (fest, bevor Ergebnisse vorlagen):
  * Jedes Monatsende: Kandidaten = die 40 besten Werte der TOP 200 nach 12-1-Rendite
    (oberes Fünftel). Ziel: Rendite im Folgemonat (inkl. Dividenden).
  * 12 Merkmale aus der Fachliteratur, jeweils mit erwarteter Richtung (siehe FEATURES).
  * Rangkorrelation (Spearman, "IC") je Monat zwischen Merkmal und Folgerendite, nur
    innerhalb der Kandidaten; Mittelwert und t-Wert.
  * Entdeckung 2005–2015, Holm-korrigiert (einseitig in erwarteter Richtung). Nur was dort
    besteht, wird im unberührten Prüfzeitraum 2016–2026 getestet (einseitig p < 0,05).
  * Bestandene Merkmale -> Portfolio: aus den 40 Kandidaten die 20 mit dem besten
    (kombinierten) Merkmalswert; Vergleich mit normalem Momentum (beste 20) und mit
    100 Zufallsauswahlen von 20 aus denselben 40 Kandidaten.
"""

from __future__ import annotations

import math
import os

import numpy as np
import pandas as pd

from . import strategies as S
from .engine import backtest, sharpe, stats
from .panel import load_adjusted
from .run import ETF, OUT, START, eligible_panel, period_sharpes
from ..robustness import holm
from ..universe import DAX40, SP500_ALL

HERE = os.path.dirname(__file__)
N_CAND, N_PICK = 40, 20
SPLIT = "2015-12-31"

# Merkmal: (Beschreibung, Quelle) – alle so gepolt, dass "größer = erwartet besser"
FEATURES = {
    "mom_12_1": ("12-1-Rendite selbst (stärkste Gewinner)", "Jegadeesh & Titman 1993"),
    "gleichmaessig": ("gleichmäßiger Anstieg statt Sprünge (−Informations-Diskretheit)",
                      "Da, Gurun & Warachka 2014 'Frog in the Pan'"),
    "resid_mom": ("Residual-Momentum: Rendite über dem Markt (Beta-bereinigt) / Restschwankung",
                  "Blitz, Huij & Martens 2011"),
    "nahe_hoch": ("Nähe zum 52-Wochen-Hoch", "George & Hwang 2004"),
    "sharpe_mom": ("12-1-Rendite / Schwankung (Rendite je Risiko)", "Rachev et al. 2007"),
    "trend_r2": ("Trendqualität: R² der Regression über 12 Monate", "Clenow 2015"),
    "niedrige_vola": ("niedrige 12-Monats-Schwankung", "Frazzini & Pedersen 2014"),
    "kein_volumenschub": ("kein Umsatzanstieg (−Umsatz 3 M / 12 M)", "Lee & Swaminathan 2000"),
    "mom_12_7": ("mittelfristiges Momentum 12-7 Monate", "Novy-Marx 2012"),
    "sektor_mom": ("Momentum des Sektors (Ø 12-1 der Sektor-Werte)", "Moskowitz & Grinblatt 1999"),
    "kein_lotterie": ("kein extremer Tagesgewinn im letzten Monat (−Max-Tagesrendite)",
                      "Bali, Cakici & Whitelaw 2011"),
    "rueckschlag_1m": ("Rücksetzer im letzten Monat (−1-Monats-Rendite)", "Jegadeesh 1990"),
}


def features(close, volume, spy, sectors):
    r = close.pct_change(fill_method=None)
    rm = spy.pct_change(fill_method=None)
    f = {}
    f["mom_12_1"] = close.shift(21) / close.shift(252) - 1
    win = 231                                        # Tage t-252 .. t-21
    pos = (r > 0).astype(float).where(r.notna()).rolling(win).mean().shift(21)
    neg = (r < 0).astype(float).where(r.notna()).rolling(win).mean().shift(21)
    f["gleichmaessig"] = -(np.sign(f["mom_12_1"]) * (neg - pos))
    w = 252
    cov = r.rolling(w).cov(rm)
    var_m = rm.rolling(w).var()
    beta = cov.div(var_m, axis=0)
    var_i = r.rolling(w).var()
    res_vol = np.sqrt((var_i - cov ** 2 / var_m.to_numpy()[:, None]).clip(lower=1e-12))
    s_i = r.rolling(win).sum().shift(21)
    s_m = rm.rolling(win).sum().shift(21)
    f["resid_mom"] = (s_i - beta.mul(s_m, axis=0)) / (res_vol * np.sqrt(win))
    f["nahe_hoch"] = close / close.rolling(252).max()
    vol = r.rolling(252).std()
    f["sharpe_mom"] = f["mom_12_1"] / (vol * np.sqrt(252))
    _, r2 = S._reg_slope_r2(np.log(close), 252)
    f["trend_r2"] = r2
    f["niedrige_vola"] = -vol
    dv = close * volume
    f["kein_volumenschub"] = -(dv.rolling(63).mean() / dv.rolling(252).mean())
    f["mom_12_7"] = close.shift(147) / close.shift(252) - 1
    sec = pd.Series(sectors).reindex(close.columns)
    m = f["mom_12_1"]
    sec_mean = m.T.groupby(sec.to_numpy()).transform("mean").T
    f["sektor_mom"] = sec_mean
    f["kein_lotterie"] = -r.rolling(21).max()
    f["rueckschlag_1m"] = -(close / close.shift(21) - 1)
    return f


def main():
    etf = load_adjusted(ETF, "etf")
    pool = load_adjusted(SP500_ALL + DAX40, "pool")
    cal = etf["Close"]["SPY"].dropna().index
    cal = cal[cal >= "2003-01-01"]
    ec = etf["Close"].reindex(cal)
    cash = ec["SHY"].ffill()
    pc = pool["Close"].reindex(cal).ffill(limit=5)
    pv = pool["Volume"].reindex(cal).fillna(0)
    elig = eligible_panel(cal, pc.columns, pit=True) & pc.notna()
    sectors = pd.read_csv(os.path.join(HERE, "sektoren.csv")).set_index("symbol").sektor.to_dict()
    F = features(pc, pv, ec["SPY"], sectors)

    ends = [d for d in S.month_ends(cal) if d >= pd.Timestamp(START)]
    rows = []
    for d, nxt in zip(ends[:-1], ends[1:]):
        m = F["mom_12_1"].loc[d].where(elig.loc[d]).dropna()
        cand = m.sort_values(ascending=False).index[:N_CAND]
        if len(cand) < N_CAND:
            continue
        fwd = pc.loc[nxt, cand] / pc.loc[d, cand] - 1
        rec = {"datum": d}
        for k in FEATURES:
            x = F[k].loc[d, cand]
            ok = x.notna() & fwd.notna()
            rec[k] = x[ok].rank().corr(fwd[ok].rank()) if ok.sum() > 10 else np.nan
        rows.append(rec)
    ic = pd.DataFrame(rows).set_index("datum")

    def summarize(sub):
        out = {}
        for k in FEATURES:
            s = sub[k].dropna()
            t = s.mean() / (s.std() / math.sqrt(len(s)))
            p = 0.5 * math.erfc(t / math.sqrt(2))     # einseitig: IC > 0
            out[k] = (s.mean(), t, p, (s > 0).mean())
        return out

    disc, val = summarize(ic[ic.index <= SPLIT]), summarize(ic[ic.index > SPLIT])
    adj = holm({k: v[2] for k, v in disc.items()})
    table = []
    for k, (desc, src) in FEATURES.items():
        passed_d = adj[k] < 0.05
        passed_v = passed_d and val[k][2] < 0.05
        table.append({"merkmal": k, "beschreibung": desc, "quelle": src,
                      "ic_2005_15": round(disc[k][0], 3), "t_2005_15": round(disc[k][1], 2),
                      "p_holm_2005_15": round(adj[k], 4),
                      "ic_2016_26": round(val[k][0], 3), "t_2016_26": round(val[k][1], 2),
                      "p_2016_26": round(val[k][2], 4), "monate_ic_pos_%": round(100 * val[k][3]),
                      "entdeckt": passed_d, "bestaetigt": passed_v})
    t = pd.DataFrame(table)
    t.to_csv(os.path.join(OUT, "momentum_merkmale.csv"), index=False)
    ic.to_csv(os.path.join(OUT, "momentum_ic_monatlich.csv"))
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(t.drop(columns=["beschreibung", "quelle"]).to_string(index=False))

    # Portfolios: Auswahl von 20 aus 40 Kandidaten nach Merkmal(en)
    confirmed = list(t.loc[t.bestaetigt, "merkmal"])
    test_sets = {f"nach {k}": [k] for k in FEATURES if k != "mom_12_1"}
    if len(confirmed) > 1:
        test_sets["kombiniert (bestätigte)"] = confirmed

    def picks(keys, d):
        m = F["mom_12_1"].loc[d].where(elig.loc[d]).dropna()
        cand = m.sort_values(ascending=False).index[:N_CAND]
        if len(cand) < N_CAND:
            return None, None
        z = sum((F[k].loc[d, cand].rank(pct=True)).fillna(0.5) for k in keys)
        return cand, z.sort_values(ascending=False).index[:N_PICK]

    def targets(keys=None, rng=None):
        rows = {}
        for d in ends:
            if keys is None and rng is None:
                m = F["mom_12_1"].loc[d].where(elig.loc[d]).dropna()
                sel = m.sort_values(ascending=False).index[:N_PICK]
            else:
                cand, sel = picks(keys or ["mom_12_1"], d)
                if cand is None:
                    continue
                if rng is not None:
                    sel = rng.choice(np.array(cand), N_PICK, replace=False)
            w = pd.Series(0.0, index=pc.columns)
            w[list(sel)] = 1.0 / N_PICK
            rows[d] = w
        return pd.DataFrame(rows).T

    base, _ = backtest(targets(), pc, cash, 0.0005, start=START)
    rng = np.random.default_rng(1)
    rand = [sharpe(backtest(targets(rng=rng), pc, cash, 0.0005, start=START)[0], cash) for _ in range(100)]
    pb = period_sharpes(base, cash)
    res = [{"auswahl": "normales Momentum (beste 20)", **stats(base, cash), "abschnitte_besser_als_normal": "–"}]
    for name, keys in test_sets.items():
        ret, _ = backtest(targets(keys), pc, cash, 0.0005, start=START)
        st = stats(ret, cash)
        ps = period_sharpes(ret, cash)
        res.append({"auswahl": name, **st,
                    "abschnitte_besser_als_normal": f"{sum(a > b for a, b in zip(ps, pb))}/4",
                    "p_vs_zufall_aus_40": round((1 + sum(x >= st["sharpe"] for x in rand)) / 101, 3),
                    "sharpe_2016_26": round(sharpe(ret[ret.index > SPLIT], cash), 2)})
    res.append({"auswahl": "Zufall: 20 aus den 40 Kandidaten (Median)", "sharpe": round(float(np.median(rand)), 2)})
    r = pd.DataFrame(res)
    r.to_csv(os.path.join(OUT, "momentum_auswahl.csv"), index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 20):
        print(r.to_string(index=False))


if __name__ == "__main__":
    main()
