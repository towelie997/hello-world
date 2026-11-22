"""The Pre-Holiday Effect – StockCharts ChartSchool:
chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/the-pre-holiday-effect

Regeln aus dem Artikel (kurzfristige Variante, nur Long): Aktien ein bzw. zwei Handelstage vor
einem Börsenfeiertag kaufen und gleich nach dem Feiertag verkaufen (Beispiele: Kauf zum
Schluss bzw. nahe Eröffnung vor dem Feiertag, Verkauf zur Eröffnung danach).
Annahmen: Feiertag = ein Wochentag (Mo–Fr), an dem SPY nicht gehandelt wurde (aus den
Kursdaten abgeleitet, ohne festen Kalender; erfasst auch Sonderschließungen wie 2012/2018).
Kauf zum Schluss des letzten (Variante: vorletzten) Handelstags davor, Verkauf zur Eröffnung
des ersten Handelstags danach. Die langfristige Variante (bis Jahresende halten) wird nicht
getestet. KEIN Stop-Loss. "1 R" = 1 ATR(14). Tageskerzen seit 2005.
Vergleich: gleicher Ablauf über normale Wochenenden (Kauf Freitagsschluss, Verkauf
Montagseröffnung) ohne Feiertag.
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade


def holiday_eves(index):
    """Positionen der letzten Handelstage vor einem Feiertag bzw. vor einem normalen
    Wochenende (nur Wochenende dazwischen)."""
    eve, wkend = [], []
    for i in range(len(index) - 1):
        a, b = index[i], index[i + 1]
        gap = pd.bdate_range(a, b)[1:-1]          # Wochentage dazwischen ohne Handel
        if len(gap):
            eve.append(i)
        elif (b - a).days == 3 and a.dayofweek == 4:
            wkend.append(i)
    return eve, wkend


def run(symbols, start="2005-01-01", days_before=1, baseline=False):
    trades = []
    if baseline:
        name = "Vergleich: normales Wochenende Fr→Mo (1d)"
    else:
        name = f"ChartSchool Pre-Holiday ({days_before} Tag{'e' if days_before > 1 else ''} vorher, 1d)"
    spy = data.load("SPY", "1d", "max")
    eve, wkend = holiday_eves(spy.index)
    events = [spy.index[i] for i in (wkend if baseline else eve)]
    nxt = {spy.index[i]: spy.index[i + 1] for i in (wkend if baseline else eve)}
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        A = atr(df)
        for d in events:
            if d < pd.Timestamp(start) or d not in df.index or nxt[d] not in df.index:
                continue
            k = df.index.get_loc(d) - (0 if baseline else days_before - 1)
            t_in, t_out = df.index[k], nxt[d]
            e, a = df.Close.loc[t_in], A.loc[t_in]
            trades.append(make_trade(name, sym, "long", t_in, e, e - a, None, t_out,
                                     df.Open.loc[t_out], "time"))
    return [x for x in trades if np.isfinite(x.r)]
