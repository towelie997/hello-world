"""Strategien aus Forschung und Hedgefonds-Praxis – jede liefert Zielgewichte je
Umschichtungstag (nur Daten bis zu diesem Tag). Parameter = Standardwerte der Quelle.

Aktien (Universum: monatliche TOP 200 nach Liquidität, siehe ../top200.py):
  momentum      Jegadeesh & Titman (1993), AQR: 12-1-Monats-Rendite, beste N, monatlich.
  clenow        Andreas Clenow, "Stocks on the Move" (2015): Trendstärke = annualisierte
                Steigung der log. Regression über 90 Tage x R², nur über SMA100, keine
                Kurslücke > 15 %, Kauf nur wenn S&P 500 > SMA200, Gewicht nach ATR(20)
                (0,1 % Tagesrisiko je Position), wöchentlich (mittwochs).
  low_vol       Haugen/Baker, Frazzini & Pedersen "Betting against Beta" (2014): die N
                Werte mit der niedrigsten 1-Jahres-Schwankung, monatlich.
  reversal      Lehmann (1990): die N größten Verlierer der letzten Woche, wöchentlich.
ETFs (Mehr-Anlageklassen):
  tsmom         Moskowitz, Ooi & Pedersen (2012), Trendfolge der CTAs (Man AHL, Winton):
                je Anlageklasse long, wenn 12-Monats-Rendite > Geldmarkt, Gewicht nach
                inverser Schwankung (63 Tage), ohne Hebel, monatlich.
  gem           Gary Antonacci, Dual Momentum "GEM" (2014): SPY vs. EFA vs. Anleihen (AGG).
  risk_parity   Bridgewater "All Weather"-Idee: inverse Schwankung über Aktien, lange und
                mittlere Anleihen, Gold, Rohstoffe, monatlich, ohne Hebel.
  turn_of_month Lakonishok & Smidt (1988): SPY nur vom vorletzten Handelstag des Monats
                bis zum 3. Handelstag des Folgemonats, sonst Geldmarkt.
Paarhandel (Gatev, Goetzmann & Rouwenhorst 2006) steht in pairs.py.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def month_ends(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    s = pd.Series(idx, index=idx)
    return pd.DatetimeIndex(s.groupby(idx.to_period("M")).max().values)


def weekdays(idx: pd.DatetimeIndex, weekday: int) -> pd.DatetimeIndex:
    """Letzter Handelstag jeder Woche, der <= dem gewünschten Wochentag ist."""
    s = pd.Series(idx, index=idx)
    wk = idx.to_period("W-SUN")
    cand = s[idx.weekday <= weekday].groupby(wk[idx.weekday <= weekday]).max()
    return pd.DatetimeIndex(cand.values)


def _equal_top(score: pd.DataFrame, dates, eligible, n, ascending=False) -> pd.DataFrame:
    rows = {}
    for d in dates:
        s = score.loc[d].where(eligible.loc[d]).dropna()
        if len(s) < n:
            continue
        pick = s.sort_values(ascending=ascending).index[:n]
        w = pd.Series(0.0, index=score.columns)
        w[pick] = 1.0 / n
        rows[d] = w
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------- Aktien
def momentum(close, eligible, n=20, lookback=252, skip=21):
    score = close.shift(skip) / close.shift(lookback) - 1
    return _equal_top(score, month_ends(close.index), eligible, n)


def low_vol(close, eligible, n=20, window=252):
    vol = close.pct_change(fill_method=None).rolling(window, min_periods=int(window * 0.9)).std()
    return _equal_top(vol, month_ends(close.index), eligible, n, ascending=True)


def reversal(close, eligible, n=20, days=5):
    score = close / close.shift(days) - 1
    return _equal_top(score, weekdays(close.index, 4), eligible, n, ascending=True)


def _reg_slope_r2(logp: pd.DataFrame, n: int):
    """Rollende lineare Regression von log(Kurs) auf die Zeit: Steigung je Tag und R²."""
    t = pd.Series(np.arange(len(logp), dtype=float), index=logp.index)
    y = logp
    sy = y.rolling(n).sum()
    sty = y.mul(t, axis=0).rolling(n).sum()
    syy = (y * y).rolling(n).sum()
    st_ = t.rolling(n).sum()
    stt = (t * t).rolling(n).sum()
    cov = sty.sub(st_ * 0, axis=0) - sy.mul(st_, axis=0) / n
    vart = stt - st_ * st_ / n
    vary = syy - sy * sy / n
    slope = cov.div(vart, axis=0)
    r2 = (slope ** 2).mul(vart, axis=0) / vary
    return slope, r2


def clenow(close, high, low, eligible, index_close, n_days=90, top_frac=0.2,
           risk=0.001, weekday=2):
    logp = np.log(close)
    slope, r2 = _reg_slope_r2(logp, n_days)
    score = ((np.exp(slope * 252) - 1) * r2)
    sma100 = close.rolling(100).mean()
    gap = close.pct_change(fill_method=None).abs().rolling(n_days).max()
    prev = close.shift()
    tr = pd.concat([(high - low).stack(), (high - prev).abs().stack(), (low - prev).abs().stack()],
                   axis=1).max(axis=1).unstack()
    atr = tr.rolling(20).mean()
    idx_ok = index_close > index_close.rolling(200).mean()
    rows, held = {}, set()
    for d in weekdays(close.index, weekday):
        ok = eligible.loc[d] & (close.loc[d] > sma100.loc[d]) & (gap.loc[d] < 0.15)
        s = score.loc[d].where(ok).dropna().sort_values(ascending=False)
        n_univ = int(eligible.loc[d].sum())
        top = list(s.index[: max(1, int(n_univ * top_frac))])
        size = (risk * close.loc[d] / atr.loc[d]).clip(upper=0.25)
        keep = [x for x in top if x in held]
        new = [x for x in top if x not in held] if idx_ok.reindex([d]).iloc[0] else []
        w = pd.Series(0.0, index=close.columns)
        total = 0.0
        for x in keep + new:
            sz = float(size.get(x, np.nan))
            if not np.isfinite(sz) or sz <= 0:
                continue
            if total + sz > 1.0:
                if x in keep:
                    sz = 1.0 - total
                else:
                    continue
            w[x] = sz
            total += sz
            if total >= 1.0:
                break
        held = set(w[w > 0].index)
        rows[d] = w
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------- ETFs
TSMOM_ASSETS = ["SPY", "IWM", "EFA", "EEM", "VNQ", "TLT", "IEF", "LQD", "GLD", "DBC"]
RP_ASSETS = ["SPY", "TLT", "IEF", "GLD", "DBC"]


def tsmom(close, assets=TSMOM_ASSETS, lookback=252, vol_window=63):
    px = close[assets]
    mom = px / px.shift(lookback) - 1
    cash_mom = close["SHY"] / close["SHY"].shift(lookback) - 1
    ivol = 1 / px.pct_change(fill_method=None).rolling(vol_window).std()
    rows = {}
    for d in month_ends(close.index):
        if mom.loc[d].isna().any() or ivol.loc[d].isna().any():
            continue
        base = ivol.loc[d] / ivol.loc[d].sum()
        rows[d] = base.where(mom.loc[d] > cash_mom.loc[d], 0.0)
    return pd.DataFrame(rows).T


def gem(close, lookback=252):
    m = close[["SPY", "EFA", "SHY"]] / close[["SPY", "EFA", "SHY"]].shift(lookback) - 1
    rows = {}
    for d in month_ends(close.index):
        if m.loc[d].isna().any() or pd.isna(close["AGG"].loc[d]):
            continue
        w = pd.Series(0.0, index=["SPY", "EFA", "AGG"])
        if m.loc[d, "SPY"] > m.loc[d, "SHY"]:
            w["SPY" if m.loc[d, "SPY"] >= m.loc[d, "EFA"] else "EFA"] = 1.0
        else:
            w["AGG"] = 1.0
        rows[d] = w
    return pd.DataFrame(rows).T


def risk_parity(close, assets=RP_ASSETS, vol_window=63):
    ivol = 1 / close[assets].pct_change(fill_method=None).rolling(vol_window).std()
    rows = {}
    for d in month_ends(close.index):
        v = ivol.loc[d]
        if v.isna().any():
            continue
        rows[d] = v / v.sum()
    return pd.DataFrame(rows).T


def turn_of_month(close, before=1, after=3):
    """Halten über die Tage -1 bis +3 um den Monatswechsel: Kauf zum Schluss des
    vorletzten Handelstags, Verkauf zum Schluss des 3. Handelstags im neuen Monat."""
    idx = close["SPY"].dropna().index
    pos = pd.Series(np.arange(len(idx)), index=idx)
    month = idx.to_period("M")
    first = pos.groupby(month).transform("min")
    last = pos.groupby(month).transform("max")
    rows = {}
    for d in idx:
        p, f, l = pos[d], first[d], last[d]
        if p == l - before:
            rows[d] = {"SPY": 1.0}
        elif p == f + after - 1:
            rows[d] = {"SPY": 0.0}
    return pd.DataFrame(rows).T.fillna(0.0)
