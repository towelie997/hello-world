"""Protokoll + optionale Telegram-Nachricht."""

from __future__ import annotations

import logging

import requests

log = logging.getLogger("connors_bot")


def send(cfg, text: str) -> None:
    log.info(text)
    if cfg.telegram_token and cfg.telegram_chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{cfg.telegram_token}/sendMessage",
                          data={"chat_id": cfg.telegram_chat_id, "text": text}, timeout=15)
        except Exception as e:  # Benachrichtigung darf den Handel nie stoppen
            log.warning("Telegram fehlgeschlagen: %s", e)
