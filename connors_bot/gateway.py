"""IB Gateway nur bei Bedarf starten und danach wieder beenden.

Market-on-Close-Orders liegen nach dem Absenden auf den Servern von IBKR – das Gateway
muss danach nicht weiterlaufen. So bleibt der Zugang (z. B. die IBKR-App) den Rest des
Tages frei.
"""

from __future__ import annotations

import logging
import os
import shlex
import signal
import socket
import subprocess
import time

log = logging.getLogger("connors_bot")


def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


class Gateway:
    """Startet den Befehl in eigener Prozessgruppe und beendet die ganze Gruppe wieder."""

    def __init__(self, cmd: str, host: str, port: int, log_path: str | None = None):
        self.cmd, self.host, self.port, self.log_path = cmd, host, port, log_path
        self.proc = None

    def start(self, timeout: float = 300) -> None:
        if port_open(self.host, self.port):
            log.info("IB Gateway läuft bereits – wird nicht neu gestartet und nicht beendet")
            return
        out = open(self.log_path, "a") if self.log_path else subprocess.DEVNULL
        log.info("Starte IB Gateway: %s", self.cmd)
        self.proc = subprocess.Popen(shlex.split(os.path.expanduser(self.cmd)), stdout=out,
                                     stderr=subprocess.STDOUT, start_new_session=True)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if port_open(self.host, self.port):
                log.info("IB Gateway erreichbar (Port %d)", self.port)
                time.sleep(10)            # Anmeldung und Datenverbindungen fertig werden lassen
                return
            if self.proc.poll() is not None:
                raise RuntimeError(f"IB Gateway-Start beendet mit Code {self.proc.returncode}")
            time.sleep(3)
        self.stop()
        raise RuntimeError(f"IB Gateway nach {timeout:.0f} s nicht erreichbar")

    def stop(self) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return
        log.info("Beende IB Gateway")
        try:
            os.killpg(self.proc.pid, signal.SIGTERM)
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(self.proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        self.proc = None
