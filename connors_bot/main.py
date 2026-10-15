"""Täglicher Lauf des Connors-RSI(2)-Bots.

    python -m connors_bot.main --mode dry-run --offline     # ohne IB, nur anzeigen
    python -m connors_bot.main --mode dry-run               # mit IB, nur anzeigen
    python -m connors_bot.main --mode paper --wait          # Papierkonto, wartet bis 20 Min. vor Schluss
    CB_LIVE=JA python -m connors_bot.main --mode live --wait  # echtes Geld (erst nach Papier-Phase!)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timezone

import exchange_calendars as xc
import pandas as pd

from . import marketdata, notify, planner, signals, state as st
from .broker import IBBroker, OfflineBroker
from .config import Config
from .gateway import Gateway
from .universe import sp500

log = logging.getLogger("connors_bot")
NY = "America/New_York"
MOC_CUTOFF_MIN = 10          # NYSE/Nasdaq: MOC-Orders bis 10 Min. vor Schluss


def session_close(now_utc: pd.Timestamp):
    """Heutiger Börsenschluss (UTC) oder None, wenn heute kein Handelstag ist."""
    cal = xc.get_calendar("XNYS")
    day = now_utc.tz_convert(NY).normalize().tz_localize(None)
    if not cal.is_session(day):
        return None, day
    return cal.session_close(day), day


def run(cfg: Config, mode: str, wait: bool, offline: bool, now=None) -> int:
    now = now or pd.Timestamp(datetime.now(timezone.utc))
    close, today = session_close(now)
    if close is None:
        log.info("Heute (%s) kein Handelstag an der NYSE – nichts zu tun", today.date())
        return 0
    target = close - pd.Timedelta(minutes=cfg.minutes_before_close)
    if mode != "dry-run" and st.load(cfg.state_dir).last_run == str(today.date()):
        log.info("Heute schon gehandelt – Ende")
        return 0
    gw = None
    if cfg.gateway_start_cmd and not offline:
        if wait:
            _sleep_until(target - pd.Timedelta(minutes=cfg.gateway_lead_minutes), "Gateway-Start")
        gw = Gateway(cfg.gateway_start_cmd, cfg.ib_host, cfg.ib_port,
                     os.path.join(cfg.state_dir, "gateway.log"))
        gw.start()
    try:
        return _run_session(cfg, mode, wait, offline, today, close, target, now)
    finally:
        if gw:
            gw.stop()


def _sleep_until(when: pd.Timestamp, what: str) -> None:
    now = pd.Timestamp(datetime.now(timezone.utc))
    if now < when:
        secs = (when - now).total_seconds()
        log.info("Warte bis %s New York (%s, %.0f Min.)", when.tz_convert(NY).strftime("%H:%M"),
                 what, secs / 60)
        time.sleep(secs)


def _run_session(cfg, mode, wait, offline, today, close, target, now) -> int:
    if wait:
        _sleep_until(target, "Handel")
        now = pd.Timestamp(datetime.now(timezone.utc))
    if mode != "dry-run" and now > close - pd.Timedelta(minutes=MOC_CUTOFF_MIN + 2):
        notify.send(cfg, f"Zu spät für MOC-Orders ({now.tz_convert(NY):%H:%M} NY) – kein Handel heute")
        return 1

    state = st.load(cfg.state_dir)
    if mode != "dry-run" and state.last_run == str(today.date()):
        log.info("Heute schon gehandelt – Ende")
        return 0

    broker = OfflineBroker(cfg, state) if offline else IBBroker(cfg)
    broker.connect()
    try:
        if mode == "paper" and not broker.is_paper():
            raise RuntimeError("--mode paper, aber das Konto ist KEIN Papierkonto")
        if mode == "live" and (broker.is_paper() or os.environ.get("CB_LIVE") != "JA"):
            raise RuntimeError("Echtgeld nur mit echtem Konto und CB_LIVE=JA")

        msgs = st.reconcile(state, broker.positions())
        if state.halted:
            notify.send(cfg, "BOT ANGEHALTEN: " + state.halted +
                        "\nBitte Depot prüfen, dann 'halted' in state.json leeren.")
            if mode != "dry-run":
                st.save(state, cfg.state_dir)
            return 2

        symbols = sorted(set(sp500(cfg.state_dir)) | set(state.positions))
        hist = marketdata.daily_closes(symbols, today)
        prices = broker.prices(symbols)
        kpis = {}
        for s in symbols:
            if s in hist and s in prices:
                k = signals.snapshot(signals.with_live_price(hist[s], prices[s], today))
                if k:
                    kpis[s] = k
        equity, cash = broker.account_usd()
        if cfg.capital_limit_usd:
            invested = sum(p["qty"] * prices.get(s, p["entry_price"]) for s, p in state.positions.items())
            equity = min(equity, cfg.capital_limit_usd)
            cash = max(0.0, min(cash, equity - invested))
        state.peak_equity = max(state.peak_equity, equity)
        intents, m2 = planner.plan(state.positions, kpis, equity, cash, state.peak_equity,
                                   cfg.max_positions, cfg.rsi_entry, cfg.max_drawdown)
        msgs += m2

        lines = [f"Connors RSI(2) {today.date()} [{mode}] Depot {equity:,.0f} $, "
                 f"{len(state.positions)}/{cfg.max_positions} Positionen, {len(kpis)} Werte mit Kurs"]
        lines += [f"{i.action} {i.qty} {i.symbol} @~{i.price:.2f} ({i.reason})" for i in intents] or ["Keine Orders"]
        if mode != "dry-run":
            for i in intents:
                try:
                    if i.action == "SELL":
                        broker.cancel_open_orders(i.symbol)          # evtl. Stop-Order löschen
                    stop = i.price * (1 - cfg.stop_pct) if (cfg.stop_pct and i.action == "BUY") else None
                    broker.place_moc(i.action, i.symbol, i.qty, stop)
                    state.pending[i.symbol] = {"action": i.action, "qty": i.qty,
                                               "date": str(today.date()), "ref_price": i.price}
                except Exception as e:
                    msgs.append(f"FEHLER {i.action} {i.symbol}: {e}")
            state.last_run = str(today.date())
            st.save(state, cfg.state_dir)
        notify.send(cfg, "\n".join(lines + msgs))
        return 0
    finally:
        broker.disconnect()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mode", choices=["dry-run", "paper", "live"], default="dry-run")
    ap.add_argument("--wait", action="store_true", help="bis kurz vor Börsenschluss warten")
    ap.add_argument("--offline", action="store_true", help="ohne IB (nur mit --mode dry-run)")
    a = ap.parse_args(argv)
    if a.offline and a.mode != "dry-run":
        ap.error("--offline nur mit --mode dry-run")
    cfg = Config()
    os.makedirs(cfg.state_dir, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.StreamHandler(),
                                  logging.FileHandler(os.path.join(cfg.state_dir, "bot.log"))])
    # IBKR-Hinweise (verzögerte Daten, Verbindungsstatus) nicht einzeln protokollieren;
    # echte Fehlermeldungen von IBKR bleiben sichtbar.
    logging.getLogger("ib_async").setLevel(logging.ERROR)
    try:
        return run(cfg, a.mode, a.wait, a.offline)
    except Exception as e:
        notify.send(cfg, f"BOT-FEHLER: {e}")
        log.exception("Abbruch")
        return 3


if __name__ == "__main__":
    sys.exit(main())
