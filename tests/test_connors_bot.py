"""Tests für connors_bot – laufen ohne Netz und ohne Interactive Brokers.

    python -m pytest tests/test_connors_bot.py -q
"""

import numpy as np
import pandas as pd
import pytest

from connors_bot import main as bot_main
from connors_bot import planner, signals, state as st


def _random_walk(n=1500, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    close = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.015, n)))
    df = pd.DataFrame({"Close": close}, index=idx)
    df["Open"] = df.Close.shift().fillna(df.Close)
    df["High"] = df[["Open", "Close"]].max(axis=1) * 1.005
    df["Low"] = df[["Open", "Close"]].min(axis=1) * 0.995
    return df[["Open", "High", "Low", "Close"]]


def test_signals_match_backtest(monkeypatch):
    """Bot-Signale Tag für Tag == Trades des Backtests (strategy_lab)."""
    from strategy_lab.strategies import connors_rsi2
    df = _random_walk()
    monkeypatch.setattr(connors_rsi2.data, "load", lambda *a, **k: df)
    expected = [(pd.Timestamp(t.entry_time), pd.Timestamp(t.exit_time))
                for t in connors_rsi2.run(["X"], start="2015-01-01") if t.reason != "end"]
    got, entry = [], None
    for i in range(200, len(df)):
        day = df.index[i]
        k = signals.snapshot(signals.with_live_price(df.Close.iloc[:i], df.Close.iloc[i], day))
        if entry is None and signals.is_entry(k):
            entry = day
        elif entry is not None and day > entry and signals.is_exit(k):
            got.append((entry, day))
            entry = None
    assert len(expected) > 20
    assert got == expected


def _k(close, sma200, sma5, rsi2):
    return {"close": close, "sma200": sma200, "sma5": sma5, "rsi2": rsi2}


def test_plan_sells_then_buys_lowest_rsi_first():
    positions = {"AAA": {"qty": 10}}
    kpis = {"AAA": _k(50, 40, 45, 60),          # Schluss > SMA5 -> verkaufen
            "BBB": _k(100, 90, 105, 3.0),
            "CCC": _k(200, 150, 210, 1.0),
            "DDD": _k(80, 90, 85, 1.0)}         # unter SMA200 -> kein Kauf
    # Geld = 600 Bargeld + 500 Verkaufserlös; je Position 1000/2 = 500
    intents, _ = planner.plan(positions, kpis, equity=1000, cash=600, peak_equity=1000,
                              max_positions=2)
    assert [(i.action, i.symbol, i.qty) for i in intents] == [
        ("SELL", "AAA", 10), ("BUY", "CCC", 2), ("BUY", "BBB", 5)]


def test_plan_respects_cash_and_whole_shares():
    kpis = {"BBB": _k(100, 90, 105, 3.0), "EXP": _k(900, 800, 950, 1.0)}
    intents, msgs = planner.plan({}, kpis, equity=1000, cash=250, peak_equity=1000,
                                 max_positions=2)
    assert [(i.symbol, i.qty) for i in intents] == [("BBB", 2)]
    assert any("EXP" in m for m in msgs)


def test_plan_kill_switch_blocks_buys_not_sells():
    positions = {"AAA": {"qty": 5}}
    kpis = {"AAA": _k(50, 40, 45, 60), "BBB": _k(100, 90, 105, 3.0)}
    intents, msgs = planner.plan(positions, kpis, equity=700, cash=700, peak_equity=1000,
                                 max_positions=5, max_drawdown=0.25)
    assert [i.action for i in intents] == ["SELL"]
    assert any("NOTBREMSE" in m for m in msgs)


def test_reconcile_pending_and_mismatch():
    s = st.State(positions={"OLD": {"qty": 3, "entry_date": "d", "entry_price": 1}},
                 pending={"NEW": {"action": "BUY", "qty": 4, "date": "d", "ref_price": 10},
                          "OLD": {"action": "SELL", "qty": 3, "date": "d", "ref_price": 1},
                          "MISS": {"action": "BUY", "qty": 2, "date": "d", "ref_price": 5}})
    msgs = st.reconcile(s, {"NEW": {"qty": 4, "avg_cost": 10.1}, "FOREIGN": {"qty": 1, "avg_cost": 1}})
    assert set(s.positions) == {"NEW"} and s.positions["NEW"]["entry_price"] == 10.1
    assert not s.pending and not s.halted
    assert any("MISS" in m for m in msgs) and any("FOREIGN" in m for m in msgs)
    msgs = st.reconcile(s, {"NEW": {"qty": 2, "avg_cost": 10.1}})
    assert "NEW" in s.halted


def test_session_close_handles_holidays_and_half_days():
    close, _ = bot_main.session_close(pd.Timestamp("2026-11-27 15:00", tz="UTC"))
    assert close == pd.Timestamp("2026-11-27 18:00", tz="UTC")       # Tag nach Thanksgiving 13:00 NY
    close, _ = bot_main.session_close(pd.Timestamp("2026-11-26 15:00", tz="UTC"))
    assert close is None                                               # Thanksgiving
    close, _ = bot_main.session_close(pd.Timestamp("2026-07-06 15:00", tz="UTC"))
    assert close == pd.Timestamp("2026-07-06 20:00", tz="UTC")       # Sommerzeit: 16:00 NY


def test_live_mode_refuses_too_late(monkeypatch, tmp_path):
    from connors_bot.config import Config
    monkeypatch.setenv("CB_STATE_DIR", str(tmp_path))
    late = pd.Timestamp("2026-07-06 19:55", tz="UTC")                 # 15:55 NY
    assert bot_main.run(Config(), "paper", wait=False, offline=True, now=late) == 1
