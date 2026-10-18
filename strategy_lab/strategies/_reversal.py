"""Gemeinsamer Ablauf für Wendesysteme (immer im Markt, Gegensignal dreht die Position),
wie sie TradingView-Strategien mit strategy.entry ohne Stop/Ziel erzeugen.

Signal zum Kerzenschluss, Ausführung in der Folgekerze (wie Pine). Kein Stop-Loss:
"1 R" ist nur eine Rechengröße = 1 ATR(14) beim Signal.
"""

from __future__ import annotations

import numpy as np

from ..engine import make_trade


def run_reversal(df, sym, name, long_sig, short_sig, first, longs=True, shorts=True,
                 fill_long=None, fill_short=None, atr=None):
    """long_sig/short_sig: bool-Arrays (Signal zum Schluss von t, Order für t+1).
    fill_long/short(t): Ausführungskurs in Kerze t (Standard: Eröffnung)."""
    o, c = df.Open.to_numpy(), df.Close.to_numpy()
    fill_long = fill_long or (lambda t: o[t])
    fill_short = fill_short or (lambda t: o[t])
    trades, pos, entry, risk, t_in = [], 0, 0.0, 0.0, None

    def close_pos(t, px):
        trades.append(make_trade(name, sym, "long" if pos == 1 else "short", df.index[t_in],
                                 entry, entry - pos * risk, None, df.index[t], px, "signal"))

    for t in range(first, len(df) - 1):
        nxt = t + 1
        if long_sig[t] and pos != 1:
            px = fill_long(nxt)
            if pos == -1:
                close_pos(nxt, px)
                pos = 0
            if longs and px is not None:
                pos, entry, risk, t_in = 1, px, float(atr[t]), nxt
        elif short_sig[t] and pos != -1:
            px = fill_short(nxt)
            if pos == 1:
                close_pos(nxt, px)
                pos = 0
            if shorts and px is not None:
                pos, entry, risk, t_in = -1, px, float(atr[t]), nxt
    if pos != 0:
        trades.append(make_trade(name, sym, "long" if pos == 1 else "short", df.index[t_in],
                                 entry, entry - pos * risk, None, df.index[-1], c[-1], "end"))
    return [tr for tr in trades if np.isfinite(tr.r)]
