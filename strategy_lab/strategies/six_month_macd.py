"""Six-Month Cycle MACD – Sy Harding ("Riding the Bear", 1999), beschrieben in der StockCharts
ChartSchool: chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/six-month-cycle-macd

Regeln aus dem Artikel (nur Long, sonst Kasse):
  Günstige Saison ab 16. Oktober, ungünstige ab 20. April (bzw. nächster Handelstag).
  Kauf am 16.10., wenn der MACD bullisch ist, sonst am ersten Tag danach, an dem er bullisch
  wird. Verkauf am 20.04., wenn der MACD bärisch ist, sonst am ersten Tag danach, an dem er
  bärisch wird. Bullisch = MACD über Signallinie ODER über 0 ("whichever comes first"),
  bärisch = MACD unter Signallinie ODER unter 0.
Annahmen: MACD 12/26/9 auf Tageskerzen, Handel zum Schlusskurs. Kommt in der günstigen Saison
kein bullisches Signal, gibt es in diesem Jahr keinen Kauf. Die "Tweaks" (Signale schon im
September/März vorwegnehmen) sind Ermessen und werden nicht genutzt. KEIN Stop-Loss.
"1 R" = 1 ATR(14). Tageskerzen seit 2005.
Vergleich: reine Saison 16.10.–20.04. ohne MACD, und die umgekehrte Saison 20.04.–16.10.
ohne MACD (zeigt, ob die Jahreszeit überhaupt einen Unterschied macht).
"""

import numpy as np
import pandas as pd

from .. import data
from ..engine import atr, make_trade

NAME = "Sy Harding Six-Month Cycle MACD (1d)"


def bull_season(idx):
    md = idx.month * 100 + idx.day
    return (md >= 1016) | (md < 420)


def run(symbols, start="2005-01-01", baseline=False, inverse=False):
    trades = []
    name = NAME
    if baseline:
        name = ("Vergleich: umgekehrte Saison 20.04.–16.10. (1d)" if inverse
                else "Vergleich: Saison 16.10.–20.04. ohne MACD (1d)")
    for sym in symbols:
        df = data.load(sym, "1d", "max")
        if len(df) < 60:
            continue
        c = df.Close
        macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
        sig = macd.ewm(span=9, adjust=False).mean()
        bullish = ((macd > sig) | (macd > 0)).to_numpy()
        bearish = ((macd < sig) | (macd < 0)).to_numpy()
        season = bull_season(df.index)
        if inverse:
            season = ~season
        if baseline:
            bullish, bearish = np.ones(len(df), bool), np.ones(len(df), bool)
        C, A = c.to_numpy(), atr(df).to_numpy()
        first = max(int(np.searchsorted(df.index, pd.Timestamp(start))), 40)
        pos, t_in = False, None
        for t in range(first, len(df)):
            if not pos and season[t] and bullish[t]:
                pos, t_in = True, t
            elif pos and not season[t] and bearish[t]:
                trades.append(make_trade(name, sym, "long", df.index[t_in], C[t_in],
                                         C[t_in] - A[t_in], None, df.index[t], C[t], "signal"))
                pos = False
        if pos:
            trades.append(make_trade(name, sym, "long", df.index[t_in], C[t_in],
                                     C[t_in] - A[t_in], None, df.index[-1], C[-1], "end"))
    return trades
