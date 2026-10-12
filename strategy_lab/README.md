# Strategy Lab – YouTube-Trading-Strategien im Backtest

Beliebte Trading-Strategien von YouTube, nach den Regeln aus dem jeweiligen Video
programmiert und mit echten Kursdaten getestet. Alle Strategien laufen über dieselbe
Engine mit denselben Kosten, damit die Ergebnisse vergleichbar sind.

```bash
pip install -r sneaky_pivot/requirements.txt
python -m strategy_lab.run_all        # aus dem Repo-Hauptordner
```

Ergebnisse: `strategy_lab/results/ranking.csv` (Rangliste), `trades.csv` (jeder Trade),
`per_symbol.csv` (je Strategie und Wert).

## So liest man die Tabelle

- **R** = Vielfaches des Risikos pro Trade (Abstand Einstieg–Stop). −1 R = Stop ausgelöst.
- **Profit-Faktor** = Summe der Gewinne ÷ Summe der Verluste. Unter 1 = Verlust,
  ab ca. 1,3 interessant, ab 2 stark.
- **Max. Drawdown** = größter Rückgang der aufsummierten Ergebnisse, in R.
- **Kosten**: 0,01 % je Seite bei Aktien/Futures, 1,5 Pips pro Trade bei Forex.
- **„Vergleich“-Zeilen** sind keine Video-Strategien, sondern Kontrollgruppen:
  dieselben Ein- und Ausstiegsregeln ohne das besondere Signal aus dem Video. Ist die
  Video-Strategie nicht besser als ihr Vergleich, bringt das Signal nichts.

## Rangliste (Stand 12.10.2026)

| Strategie | Video | Daten | Trades | Treffer | Ø je Trade | Profit-Faktor | Max. DD |
|---|---|---|---|---|---|---|---|
| Squeeze + EMA21/34 (1w) | [BrandonTrades](https://youtu.be/OKl208tuiIs) | Wochenkerzen seit 2005 | 575 | 35,0 % | +1,17 R | **2,54** | −31 R |
| Vergleich: EMA21/34 ohne Squeeze (1w) | – | Wochenkerzen seit 2005 | 1282 | 30,4 % | +1,24 R | **2,47** | −90 R |
| Vergleich: EMA21/34 ohne Squeeze (1d) | – | Tageskerzen seit 2005 | 6395 | 27,2 % | +0,49 R | **1,50** | −380 R |
| EMA200 + RSI + Engulfing (1d) | [TradingLab](https://youtu.be/XBcMiYK7qYY) | Tageskerzen seit 2005 | 1606 | 42,5 % | +0,26 R | **1,43** | −25 R |
| Squeeze + EMA21/34 (1d) | [BrandonTrades](https://youtu.be/OKl208tuiIs) | Tageskerzen seit 2005 | 2589 | 29,8 % | +0,37 R | **1,42** | −139 R |
| Vergleich: grüne Kerze > EMA200 (1d) | – | Tageskerzen seit 2005 | 4243 | 40,8 % | +0,21 R | **1,34** | −69 R |
| EMA200 + RSI + Engulfing (1h) | [TradingLab](https://youtu.be/XBcMiYK7qYY) | 1 Std, 2 Jahre | 1988 | 38,0 % | +0,11 R | **1,16** | −42 R |
| EMA50 Pullback (1d) | [Data Trader](https://youtu.be/7Ds9djcEKB4) | Tageskerzen seit 2005 | 1653 | 36,8 % | +0,09 R | **1,14** | −49 R |
| Vergleich: grüne Kerze > EMA200 (1h) | – | 1 Std, 2 Jahre | 3354 | 38,9 % | +0,10 R | **1,14** | −72 R |
| EMA50 Pullback (1h) | [Data Trader](https://youtu.be/7Ds9djcEKB4) | Forex + Aktien 1 Std, 2 Jahre | 2468 | 33,8 % | −0,02 R | **0,97** | −108 R |
| Williams %R (1h, filter) | [The Transparent Trader](https://youtu.be/GyikfniCLqU) | Forex 1 Std, 2 Jahre | 960 | 62,1 % | −0,00 R | **0,95** | −9 R |
| Williams %R (1h, base) | [The Transparent Trader](https://youtu.be/GyikfniCLqU) | Forex 1 Std, 2 Jahre | 1724 | 61,7 % | −0,00 R | **0,94** | −13 R |
| Williams %R (1h, day) | [The Transparent Trader](https://youtu.be/GyikfniCLqU) | Forex 1 Std, 2 Jahre | 1355 | 56,2 % | −0,01 R | **0,92** | −10 R |
| Williams %R (30m, filter) | [The Transparent Trader](https://youtu.be/GyikfniCLqU) | Forex 30 Min, 60 Tage | 149 | 60,4 % | −0,00 R | **0,88** | −2 R |
| ORB 15 Min | [The Moving Average](https://youtu.be/jlShztsY3oA) | 5 Min, 60 Tage | 824 | 44,9 % | −0,05 R | **0,86** | −72 R |
| Pattern Scalp | [The Rumers](https://youtu.be/T0H_jpQXdVI) | 5 Min, 60 Tage | 719 | 41,2 % | −0,12 R | **0,81** | −114 R |
| Williams %R (30m, base) | [The Transparent Trader](https://youtu.be/GyikfniCLqU) | Forex 30 Min, 60 Tage | 272 | 57,7 % | −0,01 R | **0,75** | −4 R |
| Sneaky Pivot | [The Rumers](https://youtu.be/zspMXJVbfAY) | 15 Min, 60 Tage | 286 | 39,5 % | −0,15 R | **0,72** | −60 R |
| ORB 15 Min + Trend | [The Moving Average](https://youtu.be/jlShztsY3oA) | 5 Min, 60 Tage | 404 | 40,6 % | −0,12 R | **0,71** | −66 R |
| 5-Min Range + FVG | [Casper Trading](https://youtu.be/mzFXoK2pbNE) | 1 Min, ~7 Tage | 92 | 30,4 % | −0,24 R | **0,70** | −30 R |

## Erkenntnisse

1. **Alle Day-Trading- und Scalping-Strategien verlieren Geld.** ORB, Pattern Scalp,
   Sneaky Pivot, FVG-Scalping und Williams %R liegen nach Kosten unter Profit-Faktor 1.
   Die „Verbesserung“ des ORB-Videos (Trendfilter) macht es sogar schlechter.
2. **Positiv sind nur Long-Strategien auf Tages- und Wochenkerzen** – aber vor allem,
   weil Aktien seit 2005 gestiegen sind. Die Kontrollgruppen ohne Video-Signal schneiden
   fast genauso gut oder besser ab:
   - *EMA200 + RSI + Engulfing* (1,43) ist nur wenig besser als „irgendeine grüne Kerze
     über dem EMA200“ (1,34). Das Signal hilft etwas, vor allem beim Drawdown (−25 R statt −69 R).
   - *Squeeze* bringt gegenüber „einfach über EMA21/34 kaufen“ praktisch nichts
     (2,54 vs. 2,47 wöchentlich, 1,42 vs. 1,50 täglich), halbiert aber die Zahl der Trades
     und den Drawdown.
3. Bei Einzelwerten große Unterschiede: die Strategien funktionieren bei den Gewinnern
   der letzten 20 Jahre (AAPL, NVDA, TSLA, QQQ) und kaum oder gar nicht bei VZ, T, PFE, KO.
   Trotz bewusst eingemischter Verlierer-Aktien bleibt ein **Survivorship-Bias**: Die
   Auswahl besteht aus Firmen, die es heute noch gibt.
4. Die Ergebnisse sind über die Zeiträume 2005–09, 2010–14, 2015–19, 2020–22 und
   2023–26 stabil positiv (Profit-Faktor jeweils > 1,2) – kein Zufallstreffer einzelner Jahre.

## Grenzen

- Intraday-Daten von Yahoo: 1 Min nur ~7 Tage, 5/15/30 Min nur ~60 Tage, 1 Std ~2 Jahre.
  Day-Trading-Ergebnisse beruhen deshalb auf kurzen Zeiträumen.
- Video-Regeln sind oft unscharf („nah genug“, „bullische Kursbewegung“). Jede Annahme
  steht im Kopf der jeweiligen Datei unter `strategies/`.
- Treffen Stop und Ziel in derselben Kerze, wird der Stop angenommen (konservativ).
- Nicht getestet: [Tradeciety](https://youtu.be/dDLG5VEVRL8) – Strategie beruht auf
  Ermessen (Dreiecke, Zonen, Fibonacci) und lässt sich nicht eindeutig programmieren.

## Neue Strategie hinzufügen

1. Datei `strategies/<name>.py` mit einer Funktion `run(symbols, ...) -> list[Trade]` anlegen
   (Vorlage: `orb15.py` für Intraday, `ema_rsi_engulf.py` für Tageskerzen).
2. Im Kopf der Datei Video-Link, Regeln und eigene Annahmen dokumentieren.
3. In `run_all.py` in `jobs` und `VIDEOS` eintragen und `python -m strategy_lab.run_all` starten.
4. Wo möglich eine **Vergleichs-Variante** ohne das Video-Signal mittesten.

> Keine Anlageberatung. Vergangene Ergebnisse sagen nichts über zukünftige Gewinne aus.
