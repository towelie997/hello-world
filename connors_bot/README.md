# Connors RSI(2) – Bot für Interactive Brokers

Setzt die im Strategy Lab getestete Strategie automatisch um: alle S&P-500-Werte,
Kauf zum Schluss bei Schluss > SMA200 und RSI(2) < 5 (niedrigster RSI zuerst),
Verkauf zum Schluss bei Schluss > SMA5, höchstens N Positionen zu je 1/N des Depots.
Backtest dazu: `strategy_lab/portfolio.py` und README des Strategy Lab.

> **Erst 2–3 Monate auf dem Papierkonto laufen lassen.** Keine Anlageberatung.

## Wichtig bei 5.000 € Startkapital

Mindestgebühren je Order fressen bei kleinen Positionen den Vorteil auf (Backtest mit
~0,50 $ je Order, ~5.500 $ Depot):

| Positionen | je Position | Kosten je Order | Rendite p. a. | Max. Drawdown |
|---|---|---|---|---|
| **5** (Voreinstellung) | ~1.100 $ | ~0,045 % | 16,4 % | −35,7 % |
| 10 | ~550 $ | ~0,09 % | 7,6 % | −33,3 % |
| 20 | ~275 $ | ~0,18 % | 0,9 % | −38,0 % |

Darum `CB_MAX_POSITIONS=5`. Nur ganze Aktien; Werte über ~1.100 $ (≈ 2 % des Index)
fallen damit weg. Ab ~20.000 € lohnen sich 10–20 Positionen (kleinerer Drawdown).
Renditen sind wegen Survivorship-Bias zu günstig – siehe Strategy Lab.

## Ablauf je Handelstag

1. Start 10:00 New York (systemd-Timer), Bot prüft den NYSE-Kalender (Feiertage,
   verkürzte Tage) und **wartet bis 20 Min. vor Schluss** (normal 15:40 New York).
2. Abgleich mit dem Depot: Orders vom Vortag ausgeführt? Passt der Bestand nicht,
   **hält der Bot an** und meldet sich (Eintrag `halted` in `data/state.json`).
3. Tagesschlüsse der Vortage von Yahoo, aktueller Kurs von IBKR (Snapshot).
4. Verkäufe und Käufe als **Market-on-Close**-Orders (Ausführung zum Schlusskurs;
   Einsendeschluss 10 Min. vor Schluss – danach sendet der Bot nichts mehr).
5. Zusammenfassung ins Protokoll (`data/bot.log`) und optional per Telegram.

Schutz: nur eigene Positionen (andere im Konto werden ignoriert), höchstens ein Lauf pro
Tag, **Notbremse** bei 25 % unter Höchststand (keine Käufe mehr, Verkäufe laufen weiter),
Echtgeld nur mit echtem Konto **und** `CB_LIVE=JA`, Papier-Modus verweigert echte Konten.

## Einrichtung

1. **IBKR-Konto** mit Papierkonto; Marktdaten-Abo für US-Aktien (Papierkonto kann die
   Abos des echten Kontos mitnutzen). Möglichst ein eigenes (Unter-)Konto nur für den Bot.
   Margin-Konto ohne Kredit nutzen (Käufe mit Verkaufserlösen desselben Tages); der Bot
   kauft nie mehr als das verfügbare Geld.
2. **Server** (Linux-VPS) mit **IB Gateway** und **IBC** für das automatische tägliche
   Einloggen. API in IB Gateway aktivieren, Port 4002 (Papier), nur 127.0.0.1 erlauben.
3. Python einrichten:
   ```bash
   python3 -m venv ~/venv && ~/venv/bin/pip install -r connors_bot/requirements.txt
   cp connors_bot/deploy/connors-bot.env.example ~/connors-bot.env   # anpassen
   ```
4. Testen:
   ```bash
   python -m connors_bot.main --mode dry-run --offline   # ohne IB, nur Signale anzeigen
   python -m connors_bot.main --mode dry-run             # mit IB, keine Orders
   python -m pytest tests/test_connors_bot.py -q         # 7 Tests, ohne Netz
   ```
5. Zeitplan: `deploy/connors-bot.service` und `.timer` nach `/etc/systemd/system/`,
   dann `systemctl enable --now connors-bot.timer`.

## Einrichtung auf einem Mac mini

Der Mac mini eignet sich gut: leise, sparsam, immer an. Statt systemd nutzt macOS
**launchd** (Dateien in `deploy/macos/`).

**1. Mac dauerhaft wach halten** (Systemeinstellungen → Energie):
- „Automatischen Ruhezustand verhindern, wenn der Bildschirm aus ist“ an
- „Nach Stromausfall automatisch starten“ an
- im Terminal zusätzlich: `sudo pmset -a sleep 0 disksleep 0 autorestart 1`
- Automatische macOS-Updates mit Neustart ausschalten (nur Sicherheitsupdates von Hand,
  am Wochenende).
- Automatische Anmeldung des Benutzers einschalten (Benutzer & Gruppen), damit IB Gateway
  nach einem Neustart wieder startet. Bei aktivem FileVault geht das nicht – dann nach
  jedem Neustart einmal selbst anmelden.

**2. Python und Bot:**
```bash
xcode-select --install                       # Git und Entwicklerwerkzeuge
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.12
git clone https://github.com/towelie997/hello-world.git ~/hello-world
cd ~/hello-world && git checkout claude/quirky-cannon-ke5yz8
python3.12 -m venv ~/venv-connors
~/venv-connors/bin/pip install -r connors_bot/requirements.txt pytest
~/venv-connors/bin/python -m pytest tests/test_connors_bot.py -q
cp connors_bot/deploy/connors-bot.env.example ~/connors-bot.env
```
In `~/connors-bot.env` jede Zeile mit `export ` beginnen lassen (z. B.
`export CB_MAX_POSITIONS=5`) und `export CB_MODE=paper` ergänzen.

**3. IB Gateway + IBC:** IB Gateway (stabile Version, macOS) von der IBKR-Webseite
installieren, IBC für macOS nach dessen Anleitung einrichten (Zugangsdaten des
**Papierkontos** nur in der IBC-`config.ini`). In IB Gateway: API → Einstellungen →
„ActiveX and Socket Clients“ an, Port 4002, nur 127.0.0.1, „Read-Only API“ **aus**.
Hinweis: Für echte Konten verlangt IBKR regelmäßig eine Bestätigung per IBKR-Mobile-App
(2FA) – beim Papierkonto entfällt das.

**4. Zeitplan einrichten** (`DEINNAME` in beiden Dateien durch deinen Benutzernamen ersetzen):
```bash
cp connors_bot/deploy/macos/*.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.connorsbot.ibgateway.plist
launchctl load ~/Library/LaunchAgents/com.connorsbot.daily.plist
```
Der Bot startet Mo–Fr um 15:00 deutscher Zeit und wartet bis 20 Min. vor dem
US-Börsenschluss (meist 21:40 bzw. 22:40 Uhr deutscher Zeit, an verkürzten Tagen früher).
Protokolle: `~/Library/Logs/connors-bot.log` und `connors_bot/data/bot.log`.

**5. Erster Test mit IB Gateway** (Papierkonto angemeldet):
```bash
cd ~/hello-world && ~/venv-connors/bin/python -m connors_bot.main --mode dry-run
```
Zeigt die Orders an, die heute gesendet würden – ohne zu handeln.

## Einstellungen (Umgebungsvariablen)

| Variable | Standard | Bedeutung |
|---|---|---|
| `CB_MAX_POSITIONS` | 5 | Höchstzahl Positionen (je 1/N des Depots) |
| `CB_STOP_PCT` | none | z. B. `0.10` = Stop 10 % (GTC-Order nach Kauf); laut Test eher nicht |
| `CB_MAX_DRAWDOWN` | 0.25 | Notbremse: keine Käufe unter 75 % des Höchststands |
| `CB_CAPITAL_LIMIT_USD` | – | Bot nutzt höchstens so viel vom Konto |
| `CB_IB_PORT` | 4002 | IB Gateway Papier 4002 / echt 4001; TWS 7497 / 7496 |
| `CB_MARKET_DATA_TYPE` | 1 | 1 = Echtzeit (Abo nötig), 3 = verzögert (nur zum Testen) |
| `CB_TELEGRAM_TOKEN`, `CB_TELEGRAM_CHAT_ID` | – | Nachrichten aufs Handy |

## Bekannte Grenzen

- Signal aus dem Kurs **~20 Min. vor Schluss**, nicht dem echten Schlusskurs – Werte knapp
  an der Schwelle können abweichen. Die Papier-Phase zeigt, wie stark.
- Kurshistorie von Yahoo (kostenlos, gelegentlich lückenhaft); fehlt ein Wert, wird er
  an dem Tag übersprungen.
- Snapshots für ~500 Werte dauern 1–2 Minuten (Pakete à 80 wegen IBKR-Datenlimit).
- Steuern: IBKR führt keine deutsche Abgeltungssteuer ab (Anlage KAP).
- Vor dem Echtgeld-Start Gebühren, Marktdaten-Kosten und MOC-Regeln bei IBKR prüfen.
