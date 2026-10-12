# Sneaky Pivot – Backtest & TradingView-Script

Umsetzung der Strategie aus dem YouTube-Video
[„How Trading Like an Idiot Makes Me $10,000/Month (15 Minutes a Day)“](https://youtu.be/zspMXJVbfAY) (The Rumers).

## Die Regeln

1. **15-Minuten-Chart**, keine Indikatoren.
2. **Magic Lines** zeichnen:
   - *Range High / Range Low* = Hoch / Tief des Vortags
   - *Swing High* = nächstes älteres Tageshoch über dem Range High
   - *Swing Low* = nächstes älteres Tagestief unter dem Range Low
3. Nur an den Linien handeln: oben verkaufen, unten kaufen.
4. **3-Kerzen-Muster** nach Börsenöffnung (9:30 New York):
   - Kerze 1 läuft kräftig an eine Linie (rot nach unten → Long-Setup, grün nach oben → Short-Setup)
   - „Sneaky“-Kerze: erste Gegenkerze (grün beim Long, rot beim Short)
   - Einstieg, sobald der Kurs über das Hoch (Long) bzw. unter das Tief (Short) der Sneaky-Kerze läuft
5. **Stop** hinter dem Tagestief/-hoch, **Ziel** an der gegenüberliegenden Range-Linie.

## 1. Backtest (Python)

```bash
pip install -r sneaky_pivot/requirements.txt
python sneaky_pivot/backtest.py                    # Ziel = gegenüberliegende Range-Linie
python sneaky_pivot/backtest.py --target swing     # Ziel = Swing-Linie
python sneaky_pivot/backtest.py --symbols SPY NVDA --zone-pct 0.05 --entry-cutoff 10:30
```

Optionen: `--zone-pct` (wie nah Kerze 1 an der Linie sein muss), `--max-sneaky-wait`,
`--entry-cutoff`, `--stop-buffer-pct`. Alle Trades landen als CSV in `sneaky_pivot/results/`.

Ergebnisse werden in **R** gemessen: 1 R = das Risiko eines Trades (Abstand Einstieg–Stop).
+1 R heißt „so viel gewonnen, wie riskiert“, −1 R heißt „Stop ausgelöst“.

### Ergebnis (Juli – Oktober 2026, 16 Werte, ca. 60 Handelstage)

| | Trades | Trefferquote | Ø pro Trade | Summe | Profit-Faktor | Max. Drawdown |
|---|---|---|---|---|---|---|
| Standard (Ziel Range) | 286 | 40,6 % | −0,11 R | −31,1 R | 0,78 | −52,6 R |
| Ziel Swing | 287 | 40,4 % | −0,10 R | −29,5 R | 0,79 | −52,0 R |
| nur Long | 133 | 42,1 % | −0,05 R | −7,1 R | 0,89 | −24,7 R |
| nur Short | 153 | 39,2 % | −0,16 R | −24,0 R | 0,68 | −36,1 R |

Auch mit anderen Einstellungen (Toleranz 0 / 5 / 25 %, Einstieg bis 10:30 oder 16:00,
nur 1 Kerze Wartezeit) bleibt das Ergebnis **negativ** (Profit-Faktor 0,73 – 0,89).
Das Ziel wird nur in ca. 5 % der Trades erreicht; die meisten enden am Stop oder zum Handelsschluss.

**Fazit:** In diesem Zeitraum hatte die Strategie – so wie sie im Video beschrieben ist –
keinen Vorteil. Einzelne Werte (AAPL, MSFT, TSLA, AAOI) lagen im Plus, aber bei 13–20 Trades
pro Wert ist das eher Zufall als Muster.

### Grenzen

- Kostenlose Yahoo-Daten liefern 15-Minuten-Kerzen nur für die letzten ~60 Tage.
- Gebühren und Slippage sind **nicht** eingerechnet (würden das Ergebnis weiter verschlechtern).
- „Nah genug an der Linie“ ist im Video Ermessenssache; hier per `--zone-pct` festgelegt.
- Treffen Stop und Ziel in derselben Kerze, wird konservativ der Stop angenommen.

## 2. TradingView-Script

Datei: [`sneaky_pivot.pine`](sneaky_pivot.pine)

1. TradingView öffnen → unten **Pine Editor**
2. Inhalt von `sneaky_pivot.pine` einfügen → **Zum Chart hinzufügen**
3. Chart auf **15 Minuten** stellen (reguläre Handelszeit)

Das Script zeichnet die vier Magic Lines, markiert LONG/SHORT-Einstiege, Stop, Ziel
und Ausgang. Über **Alarm erstellen → Sneaky Pivot Long/Short** bekommst du Benachrichtigungen.
Die Einstellungen entsprechen denen des Backtests.

> Keine Anlageberatung. Erst mit Papiergeld (Paper Trading) testen.
