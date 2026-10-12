"""Alle Strategien testen und eine Rangliste schreiben.

    python -m strategy_lab.run_all            (aus dem Repo-Hauptordner)
"""

from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import asdict

import pandas as pd

from .engine import DEFAULT_COST, make_trade, summarize
from .strategies import (connors_rsi2, donchian_macd, ema50_pullback, ema_rsi_engulf, fvg_orb,
                         glow_ribbon, orb15, pattern_scalp, qs_ibs, squeeze_swing,
                         weekly_breakout, williams_r)

HERE = os.path.dirname(__file__)
RESULTS = os.path.join(HERE, "results")

INTRADAY = ["YM=F", "ES=F", "NQ=F", "SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA",
            "AMZN", "META", "GOOGL", "TSLA", "AMD", "AAOI", "GGLL"]
SWING = ["SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL",
         "TSLA", "AMD", "JPM", "XOM", "JNJ", "KO", "WMT", "GLD",
         # bewusst auch Verlierer der letzten Jahre (gegen Survivorship-Bias)
         "INTC", "BA", "PFE", "F", "C", "T", "VZ", "DIS"]
FOREX = ["GBPUSD=X", "EURUSD=X"]
FOREX_WIDE = ["GBPUSD=X", "EURUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "AUDJPY=X"]

VIDEOS = {
    "Sneaky Pivot": ("The Rumers", "zspMXJVbfAY", "15 Min, 60 Tage"),
    "ORB 15 Min": ("The Moving Average", "jlShztsY3oA", "5 Min, 60 Tage"),
    "ORB 15 Min + Trend": ("The Moving Average", "jlShztsY3oA", "5 Min, 60 Tage"),
    "5-Min Range + FVG (1 Min)": ("Casper Trading", "mzFXoK2pbNE", "1 Min, ~7 Tage"),
    "Pattern Scalp (Rumers)": ("The Rumers", "T0H_jpQXdVI", "5 Min, 60 Tage"),
    "EMA200 + RSI + Engulfing (1d)": ("TradingLab", "XBcMiYK7qYY", "Tageskerzen seit 2005"),
    "EMA200 + RSI + Engulfing (1h)": ("TradingLab", "XBcMiYK7qYY", "1 Std, 2 Jahre"),
    "Vergleich: grüne Kerze > EMA200 (1d)": ("–", "", "Tageskerzen seit 2005"),
    "Vergleich: grüne Kerze > EMA200 (1h)": ("–", "", "1 Std, 2 Jahre"),
    "EMA50 Pullback (1h)": ("Data Trader", "7Ds9djcEKB4", "Forex + Aktien 1 Std, 2 Jahre"),
    "EMA50 Pullback (1d)": ("Data Trader", "7Ds9djcEKB4", "Tageskerzen seit 2005"),
    "Squeeze + EMA21/34 (1d)": ("BrandonTrades", "OKl208tuiIs", "Tageskerzen seit 2005"),
    "Squeeze + EMA21/34 (1w)": ("BrandonTrades", "OKl208tuiIs", "Wochenkerzen seit 2005"),
    "Vergleich: EMA21/34 ohne Squeeze (1d)": ("–", "", "Tageskerzen seit 2005"),
    "Vergleich: EMA21/34 ohne Squeeze (1w)": ("–", "", "Wochenkerzen seit 2005"),
    "Williams %R (30m, base)": ("The Transparent Trader", "GyikfniCLqU", "Forex 30 Min, 60 Tage"),
    "Williams %R (30m, filter)": ("The Transparent Trader", "GyikfniCLqU", "Forex 30 Min, 60 Tage"),
    "Williams %R (1h, base)": ("The Transparent Trader", "GyikfniCLqU", "Forex 1 Std, 2 Jahre"),
    "Williams %R (1h, filter)": ("The Transparent Trader", "GyikfniCLqU", "Forex 1 Std, 2 Jahre"),
    "Williams %R (1h, day)": ("The Transparent Trader", "GyikfniCLqU", "Forex 1 Std, 2 Jahre"),
    # Quelle als (Name, Link) statt YouTube-ID, wenn nicht von YouTube
    "Connors RSI(2) (1d)": ("Connors & Alvarez (Buch 2008)", "", "Tageskerzen seit 2005"),
    "Vergleich: roter Tag > SMA200 (1d)": ("–", "", "Tageskerzen seit 2005"),
    "QS 3 Swing-Regeln (SPY, 1d)": ("Quantified Strategies", "lKzoUptU2io", "SPY Tageskerzen seit 2005"),
    "QS 3 Swing-Regeln (1d)": ("Quantified Strategies", "lKzoUptU2io", "Tageskerzen seit 2005"),
    "Vergleich: Kauf nach rotem Tag (1d)": ("–", "", "Tageskerzen seit 2005"),
    "Wochen-Ausbruch + MACD-Ausstieg (1w)": ("Financial Wisdom", "tPjz1esBQVc", "Wochenkerzen seit 2005"),
    "Vergleich: 6-Wochen-Hoch-Ausbruch (1w)": ("–", "", "Wochenkerzen seit 2005"),
    "Glow Ribbon Flip (1d)": ("TradingView: blitz_locked", "https://www.tradingview.com/script/OUOx3rYT/", "Tageskerzen seit 2005"),
    "Glow Ribbon Flip (1d, nur Long)": ("TradingView: blitz_locked", "https://www.tradingview.com/script/OUOx3rYT/", "Tageskerzen seit 2005"),
    "Vergleich: EMA21-Kreuz, fester Stop (1d)": ("–", "", "Tageskerzen seit 2005"),
    "Donchian 50 + MACD (1d)": ("TradingView: LordRobrecht", "https://www.tradingview.com/script/bGjB7COd/", "Tageskerzen seit 2005"),
    "Vergleich: Donchian 50 ohne MACD (1d)": ("–", "", "Tageskerzen seit 2005"),
}


def sneaky_pivot_trades():
    """Sneaky Pivot aus sneaky_pivot/backtest.py, mit denselben Kosten bewertet."""
    path = os.path.join(HERE, "..", "sneaky_pivot", "backtest.py")
    spec = importlib.util.spec_from_file_location("sp_backtest", path)
    sp = importlib.util.module_from_spec(spec)
    sys.modules["sp_backtest"] = sp
    spec.loader.exec_module(sp)
    args = type("A", (), dict(target="range", zone_pct=0.10, max_sneaky_wait=3,
                              entry_cutoff=pd.Timestamp("12:00").time(), stop_buffer_pct=0.02))()
    out = []
    for sym in INTRADAY:
        for t in sp.backtest_symbol(sym, args):
            out.append(make_trade("Sneaky Pivot", sym, t.side, f"{t.date} {t.entry_time}",
                                  t.entry, t.stop, t.target, f"{t.date} {t.exit_time}",
                                  t.exit, t.reason))
    return out


def main():
    jobs = [
        ("Sneaky Pivot", sneaky_pivot_trades),
        ("ORB 15 Min", lambda: orb15.run(INTRADAY)),
        ("ORB 15 Min + Trend", lambda: orb15.run(INTRADAY, trend_filter=True)),
        ("5-Min Range + FVG", lambda: fvg_orb.run(INTRADAY)),
        ("Pattern Scalp", lambda: pattern_scalp.run(INTRADAY)),
        ("EMA/RSI/Engulf 1d", lambda: ema_rsi_engulf.run(SWING, "1d", "max")),
        ("EMA/RSI/Engulf 1h", lambda: ema_rsi_engulf.run(SWING, "1h", "730d")),
        ("Vergleich 1d", lambda: ema_rsi_engulf.run(SWING, "1d", "max", baseline=True)),
        ("Vergleich 1h", lambda: ema_rsi_engulf.run(SWING, "1h", "730d", baseline=True)),
        ("EMA50 Pullback 1h FX", lambda: ema50_pullback.run(FOREX_WIDE, "1h", "730d")),
        ("EMA50 Pullback 1h Akt", lambda: ema50_pullback.run(SWING, "1h", "730d")),
        ("EMA50 Pullback 1d", lambda: ema50_pullback.run(SWING, "1d", "max")),
        ("Squeeze 1d", lambda: squeeze_swing.run(SWING, "1d")),
        ("Squeeze 1w", lambda: squeeze_swing.run(SWING, "1w")),
        ("Vergleich Squeeze 1d", lambda: squeeze_swing.run(SWING, "1d", baseline=True)),
        ("Vergleich Squeeze 1w", lambda: squeeze_swing.run(SWING, "1w", baseline=True)),
        ("Williams 30m base", lambda: williams_r.run(FOREX, "30m", "60d", "base")),
        ("Williams 30m filter", lambda: williams_r.run(FOREX, "30m", "60d", "filter")),
        ("Williams 1h base", lambda: williams_r.run(FOREX, "1h", "730d", "base")),
        ("Williams 1h filter", lambda: williams_r.run(FOREX, "1h", "730d", "filter")),
        ("Williams 1h day", lambda: williams_r.run(FOREX, "1h", "730d", "day")),
        ("Connors RSI2", lambda: connors_rsi2.run(SWING)),
        ("Vergleich RSI2", lambda: connors_rsi2.run(SWING, baseline=True)),
        ("QS Swing SPY", lambda: qs_ibs.run(["SPY"], label=" (SPY, 1d)")),
        ("QS Swing", lambda: qs_ibs.run(SWING, label=" (1d)")),
        ("Vergleich QS", lambda: qs_ibs.run(SWING, baseline=True, label=" (1d)")),
        ("Wochen-Ausbruch", lambda: weekly_breakout.run(SWING)),
        ("Vergleich Ausbruch", lambda: weekly_breakout.run(SWING, baseline=True)),
        ("Glow Ribbon", lambda: glow_ribbon.run(SWING)),
        ("Glow Ribbon Long", lambda: glow_ribbon.run(SWING, shorts=False)),
        ("Vergleich Glow", lambda: glow_ribbon.run(SWING, baseline=True)),
        ("Donchian+MACD", lambda: donchian_macd.run(SWING)),
        ("Vergleich Donchian", lambda: donchian_macd.run(SWING, baseline=True)),
    ]
    all_trades = []
    for label, fn in jobs:
        trades = fn()
        print(f"{label:<22} {len(trades):>5} Trades")
        all_trades += trades

    df = pd.DataFrame([asdict(t) for t in all_trades])
    df["_t"] = pd.to_datetime(df.entry_time, utc=True, format="mixed")
    df = df.sort_values(["strategy", "_t"], kind="stable").drop(columns="_t").reset_index(drop=True)
    os.makedirs(RESULTS, exist_ok=True)
    df.to_csv(os.path.join(RESULTS, "trades.csv"), index=False)

    rows = []
    for name, g in df.groupby("strategy", sort=False):
        s = summarize(g)
        channel, vid, data_desc = VIDEOS.get(name, ("", "", ""))
        rows.append({"strategie": name, "kanal": channel, "daten": data_desc, **s,
                     "video": vid if vid.startswith("http") else
                     (f"https://youtu.be/{vid}" if vid else "")})
    table = pd.DataFrame(rows).sort_values("profit_factor", ascending=False)
    table.to_csv(os.path.join(RESULTS, "ranking.csv"), index=False)

    print("\n=== Rangliste (nach Profit-Faktor, inkl. Kosten) ===")
    print(table.drop(columns=["video"]).to_string(index=False))

    per_symbol = (df.groupby(["strategy", "symbol"]).apply(lambda g: pd.Series(summarize(g)))
                  .reset_index())
    per_symbol.to_csv(os.path.join(RESULTS, "per_symbol.csv"), index=False)
    print(f"\nKosten: {DEFAULT_COST:.2%} je Seite (Forex: 1,5 Pips pro Trade). "
          f"Ergebnisse in {RESULTS}/")


if __name__ == "__main__":
    main()
