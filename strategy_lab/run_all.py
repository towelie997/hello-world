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
from .strategies import (dt_stoch_rsi_macd, golden_cross, qs_connors6, tl_bb_rsi, turtles_tmr0,
                         chartart_bb_rsi, chartart_macd_sma, connors_rsi2, donchian_macd,
                         ema50_pullback, ema_rsi_engulf, fvg_orb, glow_ribbon, moving_momentum,
                         orb15, pattern_scalp, qs5, qs_ibs, squeeze_swing, weekly_breakout,
                         weinstein, williams_r)

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
    "QS 5 Regeln (SPY, 1d)": ("Quantified Strategies", "KuXV0LRfJx8", "SPY Tageskerzen seit 2005"),
    "QS 5 Regeln (1d)": ("Quantified Strategies", "KuXV0LRfJx8", "Tageskerzen seit 2005"),
    "Weinstein Stufe 2 (1w)": ("Trade With Trend (Weinstein)", "Ux_uuOj-gKs", "Wochenkerzen seit 2005"),
    "Vergleich: Stufe 2 ohne rel. Stärke (1w)": ("–", "", "Wochenkerzen seit 2005"),
    "ChartArt Bollinger + RSI (1d)": ("TradingView: ChartArt", "https://www.tradingview.com/script/uCV8I4xA/", "Tageskerzen seit 2005"),
    "ChartArt Bollinger + RSI (1d, nur Long)": ("TradingView: ChartArt", "https://www.tradingview.com/script/uCV8I4xA/", "Tageskerzen seit 2005"),
    "Vergleich: nur Bollinger-Kreuz (1d)": ("–", "", "Tageskerzen seit 2005"),
    "ChartArt MACD + SMA200 (1d)": ("TradingView: ChartArt", "https://www.tradingview.com/script/yMCa3XZD/", "Tageskerzen seit 2005"),
    "ChartArt MACD + SMA200 (1d, nur Long)": ("TradingView: ChartArt", "https://www.tradingview.com/script/yMCa3XZD/", "Tageskerzen seit 2005"),
    "Vergleich: jede MACD-Kreuzung (1d)": ("–", "", "Tageskerzen seit 2005"),
    "Moving Momentum (1d)": ("StockCharts ChartSchool (A. Hill)", "https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/moving-momentum", "Tageskerzen seit 2005"),
    "Moving Momentum (1d, nur Long)": ("StockCharts ChartSchool (A. Hill)", "https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/moving-momentum", "Tageskerzen seit 2005"),
    "Vergleich: Moving Momentum ohne Stochastik (1d)": ("–", "", "Tageskerzen seit 2005"),
    "TradingLab Bollinger + RSI (1d)": ("TradingLab", "pCmJ8wsAS_w", "Tageskerzen seit 2005"),
    "TradingLab Bollinger + RSI (1d, nur Long)": ("TradingLab", "pCmJ8wsAS_w", "Tageskerzen seit 2005"),
    "Vergleich: nur Bollinger 30 (1d)": ("–", "", "Tageskerzen seit 2005"),
    "Data Trader Stoch+RSI+MACD (30m)": ("Data Trader", "hh3BKTFE1dc", "Forex 30 Min, 60 Tage"),
    "Data Trader Stoch+RSI+MACD (1h)": ("Data Trader", "hh3BKTFE1dc", "Forex 1 Std, 2 Jahre"),
    "Vergleich: MACD+RSI ohne Stochastik (30m)": ("–", "", "Forex 30 Min, 60 Tage"),
    "Vergleich: MACD+RSI ohne Stochastik (1h)": ("–", "", "Forex 1 Std, 2 Jahre"),
    "ChartArt Golden Cross (1d)": ("TradingView: ChartArt", "https://www.tradingview.com/script/6ZReHYKn/", "Tageskerzen seit 2005"),
    "Vergleich: Kurs kreuzt SMA200 (1d)": ("–", "", "Tageskerzen seit 2005"),
    "Turtles tmr0 (1d)": ("TradingView: tmr0", "https://www.tradingview.com/script/Q1O23zJP/", "Tageskerzen seit 2005"),
    "Turtles tmr0 (1d, nur Long)": ("TradingView: tmr0", "https://www.tradingview.com/script/Q1O23zJP/", "Tageskerzen seit 2005"),
    "QS/Connors Double 5 (1d)": ("Quantified Strategies (Connors)", "gX8FjjKR7ec", "Tageskerzen seit 2005"),
    "QS/Connors 4 von 5 Tagen runter (1d)": ("Quantified Strategies (Connors)", "gX8FjjKR7ec", "Tageskerzen seit 2005"),
    "QS/Connors %b 3 Tage (1d)": ("Quantified Strategies (Connors)", "gX8FjjKR7ec", "Tageskerzen seit 2005"),
    "QS/Connors R3 (1d)": ("Quantified Strategies (Connors)", "gX8FjjKR7ec", "Tageskerzen seit 2005"),
    "QS/Connors RSI(5) 30/50 (1d)": ("Quantified Strategies (Connors)", "gX8FjjKR7ec", "Tageskerzen seit 2005"),
    "QS/Connors 3 Tage tiefere Hochs/Tiefs (1d)": ("Quantified Strategies (Connors)", "gX8FjjKR7ec", "Tageskerzen seit 2005"),
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
        ("QS 5 Regeln SPY", lambda: qs5.run(["SPY"], label=" (SPY, 1d)")),
        ("QS 5 Regeln", lambda: qs5.run(SWING, label=" (1d)")),
        ("Weinstein", lambda: weinstein.run(SWING)),
        ("Vergleich Weinstein", lambda: weinstein.run(SWING, baseline=True)),
        ("ChartArt BB+RSI", lambda: chartart_bb_rsi.run(SWING)),
        ("ChartArt BB+RSI Long", lambda: chartart_bb_rsi.run(SWING, shorts=False)),
        ("Vergleich BB", lambda: chartart_bb_rsi.run(SWING, baseline=True)),
        ("ChartArt MACD+SMA", lambda: chartart_macd_sma.run(SWING)),
        ("ChartArt MACD+SMA Long", lambda: chartart_macd_sma.run(SWING, shorts=False)),
        ("Vergleich MACD", lambda: chartart_macd_sma.run(SWING, baseline=True)),
        ("Moving Momentum", lambda: moving_momentum.run(SWING)),
        ("Moving Momentum Long", lambda: moving_momentum.run(SWING, shorts=False)),
        ("Vergleich Moving Mom.", lambda: moving_momentum.run(SWING, baseline=True)),
        ("TL BB+RSI", lambda: tl_bb_rsi.run(SWING)),
        ("TL BB+RSI Long", lambda: tl_bb_rsi.run(SWING, shorts=False)),
        ("Vergleich TL BB", lambda: tl_bb_rsi.run(SWING, baseline=True)),
        ("Golden Cross", lambda: golden_cross.run(SWING)),
        ("Vergleich Golden", lambda: golden_cross.run(SWING, baseline=True)),
        ("Turtles", lambda: turtles_tmr0.run(SWING)),
        ("Turtles Long", lambda: turtles_tmr0.run(SWING, shorts=False)),
        ("QSC double5", lambda: qs_connors6.run(SWING, "double5")),
        ("QSC tage_runter", lambda: qs_connors6.run(SWING, "tage_runter")),
        ("QSC prozent_b", lambda: qs_connors6.run(SWING, "prozent_b")),
        ("QSC r3", lambda: qs_connors6.run(SWING, "r3")),
        ("QSC rsi5", lambda: qs_connors6.run(SWING, "rsi5")),
        ("QSC drei_tage", lambda: qs_connors6.run(SWING, "drei_tage")),
        ("DataTrader 30m", lambda: dt_stoch_rsi_macd.run(FOREX_WIDE, "30m", "60d")),
        ("DataTrader 1h", lambda: dt_stoch_rsi_macd.run(FOREX_WIDE, "1h", "730d")),
        ("Vergleich DT 30m", lambda: dt_stoch_rsi_macd.run(FOREX_WIDE, "30m", "60d", baseline=True)),
        ("Vergleich DT 1h", lambda: dt_stoch_rsi_macd.run(FOREX_WIDE, "1h", "730d", baseline=True)),
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
