"""Anbindung an Interactive Brokers über ib_async (IB Gateway oder TWS muss laufen)."""

from __future__ import annotations

import logging
import math

from .universe import ib_symbol

log = logging.getLogger("connors_bot")


def _ok(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x)) and x > 0


def usd_per_base(account_values, base: str) -> float:
    """Wechselkurs aus den Kontodaten von IBKR (Tag 'ExchangeRate', Währung USD =
    Basiswährung je 1 USD) – braucht kein Marktdaten-Abo. Ersatz: Yahoo."""
    for v in account_values:
        if v.tag == "ExchangeRate" and v.currency == "USD":
            try:
                rate = float(v.value)
            except ValueError:
                continue
            if rate > 0:
                return 1.0 / rate
    import yfinance as yf
    px = yf.Ticker(f"{base}USD=X").history(period="5d").Close.dropna()
    if px.empty:
        raise RuntimeError(f"Kein Wechselkurs {base}USD (weder von IBKR noch von Yahoo)")
    log.warning("Wechselkurs %sUSD von Yahoo: %.4f", base, px.iloc[-1])
    return float(px.iloc[-1])


class IBBroker:
    def __init__(self, cfg):
        from ib_async import IB
        self.cfg, self.ib = cfg, IB()
        self._contracts = {}

    # Verbindung -------------------------------------------------------------
    def connect(self):
        self.ib.connect(self.cfg.ib_host, self.cfg.ib_port, clientId=self.cfg.ib_client_id,
                        timeout=20)
        self.ib.reqMarketDataType(self.cfg.market_data_type)

    def disconnect(self):
        self.ib.disconnect()

    def is_paper(self) -> bool:
        """IBKR-Papierkonten beginnen mit 'D' (z. B. DU1234567)."""
        return all(a.startswith("D") for a in self.ib.managedAccounts())

    # Kontrakte --------------------------------------------------------------
    def contracts(self, symbols):
        from ib_async import Stock
        todo = [s for s in symbols if s not in self._contracts]
        for i in range(0, len(todo), 50):
            batch = [Stock(ib_symbol(s), "SMART", "USD") for s in todo[i:i + 50]]
            self.ib.qualifyContracts(*batch)          # füllt conId direkt in den Objekten
            for s, c in zip(todo[i:i + 50], batch):
                if c.conId:
                    self._contracts[s] = c
        return {s: self._contracts[s] for s in symbols if s in self._contracts}

    # Daten ------------------------------------------------------------------
    def positions(self) -> dict:
        out = {}
        for p in self.ib.positions():
            c = p.contract
            if c.secType == "STK" and c.currency == "USD" and p.position:
                out[c.symbol.replace(" ", ".")] = {"qty": float(p.position),
                                                   "avg_cost": float(p.avgCost)}
        return out

    def prices(self, symbols) -> dict[str, float]:
        """Aktuelle Kurse als Snapshot, in Paketen (Standard-Limit: 100 Datenzeilen)."""
        cons = self.contracts(symbols)
        out, items = {}, list(cons.items())
        for i in range(0, len(items), self.cfg.snapshot_batch):
            batch = items[i:i + self.cfg.snapshot_batch]
            ticks = [(s, self.ib.reqMktData(c, "", snapshot=True)) for s, c in batch]
            for _ in range(30):
                self.ib.sleep(0.5)
                if all(_ok(t.marketPrice()) or _ok(t.last) for _, t in ticks):
                    break
            for s, t in ticks:
                px = t.marketPrice() if _ok(t.marketPrice()) else t.last
                if _ok(px):
                    out[s] = float(px)
        missing = len(symbols) - len(out)
        if missing:
            log.warning("%d Werte ohne Kurs (Marktdaten-Abo prüfen)", missing)
        return out

    def account_usd(self) -> tuple[float, float]:
        """(Depotwert, verfügbare Mittel) in USD, umgerechnet falls Basiswährung nicht USD."""
        vals = {(v.tag, v.currency): float(v.value) for v in self.ib.accountSummary()
                if v.tag in ("NetLiquidation", "AvailableFunds")}
        base = next(cur for (tag, cur) in vals if tag == "NetLiquidation")
        rate = 1.0 if base == "USD" else usd_per_base(self.ib.accountValues(), base)
        return vals[("NetLiquidation", base)] * rate, vals[("AvailableFunds", base)] * rate

    # Orders -----------------------------------------------------------------
    def cancel_open_orders(self, sym: str):
        for t in self.ib.openTrades():
            if t.contract.symbol == ib_symbol(sym):
                self.ib.cancelOrder(t.order)

    def place_moc(self, action: str, sym: str, qty: int, stop_price: float | None = None):
        """Market-on-Close; optional Stop (GTC) als Kind-Order, aktiv nach Ausführung."""
        from ib_async import Order
        c = self.contracts([sym])[sym]
        parent = Order(action=action, totalQuantity=qty, orderType="MOC", tif="DAY",
                       transmit=stop_price is None)
        trade = self.ib.placeOrder(c, parent)
        if stop_price is not None:
            child = Order(action="SELL", totalQuantity=qty, orderType="STP",
                          auxPrice=round(stop_price, 2), tif="GTC",
                          parentId=parent.orderId, transmit=True)
            self.ib.placeOrder(c, child)
        self.ib.sleep(2)
        status = trade.orderStatus.status
        if status not in ("PreSubmitted", "Submitted", "Filled"):
            raise RuntimeError(f"{action} {sym}: Status {status} – {trade.log[-1].message if trade.log else ''}")
        return status


class OfflineBroker:
    """Für Trockenläufe ohne IB: Kurse von Yahoo, Depot aus dem Bot-Speicher."""

    def __init__(self, cfg, state, equity_usd: float = 5500.0):
        self.cfg, self.state, self.equity = cfg, state, equity_usd

    def connect(self):
        pass

    def disconnect(self):
        pass

    def is_paper(self):
        return True

    def positions(self):
        return {s: {"qty": p["qty"], "avg_cost": p["entry_price"]}
                for s, p in self.state.positions.items()}

    def prices(self, symbols):
        import yfinance as yf

        from .universe import yahoo_symbol
        df = yf.download([yahoo_symbol(s) for s in symbols], period="5d", interval="1d",
                         auto_adjust=False, progress=False, group_by="column")["Close"]
        last = df.ffill().iloc[-1]
        return {s: float(last[yahoo_symbol(s)]) for s in symbols
                if yahoo_symbol(s) in last and _ok(float(last[yahoo_symbol(s)]))}

    def account_usd(self):
        return self.equity, self.equity

    def cancel_open_orders(self, sym):
        pass

    def place_moc(self, *a, **k):
        raise RuntimeError("Offline-Broker sendet keine Orders")
