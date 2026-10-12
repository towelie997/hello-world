# Strategy Lab – Trading-Strategien aus YouTube, TradingView & Büchern im Backtest

Beliebte Trading-Strategien von YouTube, TradingView und aus Fachbüchern, nach den Regeln
der jeweiligen Quelle programmiert und mit echten Kursdaten getestet. Alle Strategien laufen über dieselbe
Engine mit denselben Kosten, damit die Ergebnisse vergleichbar sind.

```bash
pip install -r sneaky_pivot/requirements.txt
python -m strategy_lab.run_all        # aus dem Repo-Hauptordner
```

Ergebnisse: `strategy_lab/results/ranking.csv` (Rangliste), `trades.csv` (jeder Trade),
`per_symbol.csv` (je Strategie und Wert).

## So liest man die Tabelle

- **R** = Vielfaches des Risikos pro Trade (Abstand Einstieg–Stop). −1 R = Stop ausgelöst.
  Strategien **ohne Stop-Loss im Original** (Connors RSI(2), Quantified Strategies und ihre
  Vergleiche) rechnen mit 1 R = 1 ATR(14) beim Einstieg – nur eine Rechengröße, Verluste
  können dort weit über −1 R gehen.
- **Profit-Faktor** = Summe der Gewinne ÷ Summe der Verluste. Unter 1 = Verlust,
  ab ca. 1,3 interessant, ab 2 stark.
- **Max. Drawdown** = größter Rückgang der aufsummierten Ergebnisse, in R.
- **Kosten**: 0,01 % je Seite bei Aktien/Futures, 1,5 Pips pro Trade bei Forex.
- **„Vergleich“-Zeilen** sind keine Video-Strategien, sondern Kontrollgruppen:
  dieselben Ein- und Ausstiegsregeln ohne das besondere Signal der Quelle. Ist die
  Strategie nicht besser als ihr Vergleich, bringt das Signal nichts.

## Rangliste (Stand 12.10.2026)

| Strategie | Quelle | Daten | Trades | Treffer | Ø je Trade | Profit-Faktor | Max. DD |
|---|---|---|---|---|---|---|---|
| Vergleich: 6-Wochen-Hoch-Ausbruch (1w) | – | Wochenkerzen seit 2005 | 1154 | 35,7 % | +0,98 R | **2,68** | −61 R |
| Squeeze + EMA21/34 (1w) | [BrandonTrades](https://youtu.be/OKl208tuiIs) | Wochenkerzen seit 2005 | 575 | 35,0 % | +1,17 R | **2,54** | −31 R |
| Vergleich: EMA21/34 ohne Squeeze (1w) | – | Wochenkerzen seit 2005 | 1283 | 30,4 % | +1,24 R | **2,47** | −90 R |
| QS 3 Swing-Regeln (SPY, 1d) | [Quantified Strategies](https://youtu.be/lKzoUptU2io) | SPY Tageskerzen seit 2005 | 527 | 70,8 % | +0,32 R | **1,92** | −17 R |
| Wochen-Ausbruch + MACD-Ausstieg (1w) | [Financial Wisdom](https://youtu.be/tPjz1esBQVc) | Wochenkerzen seit 2005 | 807 | 36,9 % | +0,49 R | **1,88** | −32 R |
| Connors RSI(2) (1d) | Connors & Alvarez (Buch 2008) | Tageskerzen seit 2005 | 1994 | 69,6 % | +0,28 R | **1,77** | −45 R |
| Vergleich: EMA21/34 ohne Squeeze (1d) | – | Tageskerzen seit 2005 | 6395 | 27,2 % | +0,49 R | **1,50** | −380 R |
| Glow Ribbon Flip (1d, nur Long) | [TV: blitz_locked](https://www.tradingview.com/script/OUOx3rYT/) | Tageskerzen seit 2005 | 2431 | 40,7 % | +0,19 R | **1,46** | −44 R |
| EMA200 + RSI + Engulfing (1d) | [TradingLab](https://youtu.be/XBcMiYK7qYY) | Tageskerzen seit 2005 | 1606 | 42,5 % | +0,26 R | **1,43** | −25 R |
| Squeeze + EMA21/34 (1d) | [BrandonTrades](https://youtu.be/OKl208tuiIs) | Tageskerzen seit 2005 | 2589 | 29,8 % | +0,37 R | **1,42** | −139 R |
| QS 3 Swing-Regeln (1d) | [Quantified Strategies](https://youtu.be/lKzoUptU2io) | Tageskerzen seit 2005 | 13492 | 67,1 % | +0,17 R | **1,40** | −125 R |
| Vergleich: grüne Kerze > EMA200 (1d) | – | Tageskerzen seit 2005 | 4244 | 40,8 % | +0,21 R | **1,34** | −69 R |
| Vergleich: Kauf nach rotem Tag (1d) | – | Tageskerzen seit 2005 | 22662 | 67,5 % | +0,12 R | **1,28** | −214 R |
| Vergleich: roter Tag > SMA200 (1d) | – | Tageskerzen seit 2005 | 19432 | 67,3 % | +0,09 R | **1,26** | −121 R |
| EMA200 + RSI + Engulfing (1h) | [TradingLab](https://youtu.be/XBcMiYK7qYY) | 1 Std, 2 Jahre | 1989 | 38,1 % | +0,11 R | **1,16** | −42 R |
| Donchian 50 + MACD (1d) | [TV: LordRobrecht](https://www.tradingview.com/script/bGjB7COd/) | Tageskerzen seit 2005 | 2060 | 37,3 % | +0,06 R | **1,14** | −66 R |
| Vergleich: grüne Kerze > EMA200 (1h) | – | 1 Std, 2 Jahre | 3354 | 38,9 % | +0,10 R | **1,14** | −72 R |
| Vergleich: Donchian 50 ohne MACD (1d) | – | Tageskerzen seit 2005 | 2121 | 38,1 % | +0,06 R | **1,14** | −70 R |
| EMA50 Pullback (1d) | [Data Trader](https://youtu.be/7Ds9djcEKB4) | Tageskerzen seit 2005 | 1653 | 36,8 % | +0,09 R | **1,14** | −49 R |
| Glow Ribbon Flip (1d) | [TV: blitz_locked](https://www.tradingview.com/script/OUOx3rYT/) | Tageskerzen seit 2005 | 4573 | 34,7 % | +0,03 R | **1,07** | −80 R |
| Vergleich: EMA21-Kreuz, fester Stop (1d) | – | Tageskerzen seit 2005 | 17677 | 30,8 % | +0,01 R | **1,03** | −92 R |
| EMA50 Pullback (1h) | [Data Trader](https://youtu.be/7Ds9djcEKB4) | Forex + Aktien 1 Std, 2 Jahre | 2468 | 33,8 % | −0,02 R | **0,97** | −108 R |
| Williams %R (1h, filter) | [The Transparent Trader](https://youtu.be/GyikfniCLqU) | Forex 1 Std, 2 Jahre | 960 | 62,1 % | −0,00 R | **0,95** | −9 R |
| Williams %R (1h, base) | [The Transparent Trader](https://youtu.be/GyikfniCLqU) | Forex 1 Std, 2 Jahre | 1724 | 61,7 % | −0,00 R | **0,94** | −13 R |
| Williams %R (1h, day) | [The Transparent Trader](https://youtu.be/GyikfniCLqU) | Forex 1 Std, 2 Jahre | 1355 | 56,2 % | −0,01 R | **0,92** | −10 R |
| Williams %R (30m, filter) | [The Transparent Trader](https://youtu.be/GyikfniCLqU) | Forex 30 Min, 60 Tage | 149 | 60,4 % | −0,00 R | **0,88** | −2 R |
| ORB 15 Min | [The Moving Average](https://youtu.be/jlShztsY3oA) | 5 Min, 60 Tage | 838 | 44,9 % | −0,06 R | **0,85** | −72 R |
| Pattern Scalp | [The Rumers](https://youtu.be/T0H_jpQXdVI) | 5 Min, 60 Tage | 732 | 41,0 % | −0,12 R | **0,79** | −114 R |
| 5-Min Range + FVG | [Casper Trading](https://youtu.be/mzFXoK2pbNE) | 1 Min, ~7 Tage | 106 | 32,1 % | −0,20 R | **0,75** | −32 R |
| Williams %R (30m, base) | [The Transparent Trader](https://youtu.be/GyikfniCLqU) | Forex 30 Min, 60 Tage | 272 | 57,7 % | −0,01 R | **0,75** | −4 R |
| Sneaky Pivot | [The Rumers](https://youtu.be/zspMXJVbfAY) | 15 Min, 60 Tage | 295 | 40,0 % | −0,15 R | **0,71** | −60 R |
| ORB 15 Min + Trend | [The Moving Average](https://youtu.be/jlShztsY3oA) | 5 Min, 60 Tage | 410 | 40,5 % | −0,12 R | **0,70** | −66 R |

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
5. **Neu (Lauf 12.10.2026): Kurzfristige Rücksetzer kaufen funktioniert am besten.**
   *Connors RSI(2)* (1,77) und die *3 Swing-Regeln von Quantified Strategies* (1,92 auf SPY,
   1,40 auf allen Werten) schlagen ihre Vergleiche „Kauf nach rotem Tag“ (1,26 bzw. 1,28)
   deutlich – das sind die ersten Signale mit einem **echten Vorteil**. Stabil in allen
   fünf Zeiträumen (RSI(2): 1,54–2,20; QS: 1,33–1,49) und auch ohne die drei besten Werte
   (1,63 bzw. 1,34). Aber: **beide Originale haben keinen Stop-Loss.**
6. *Wochen-Ausbruch aus Konsolidierung* (Financial Wisdom, 1,88) ist profitabel, aber
   **schlechter als der simple Vergleich** „jeder Wochenschluss über dem 6-Wochen-Hoch“
   (2,68). Die Enge der Box und die Mindestgröße des Ausbruchs filtern eher Gewinner heraus.
   Der Vergleich lebt stark von TSLA, NVDA, AAPL (ohne sie 1,94).
7. Die beiden TradingView-Strategien bringen nichts Eigenes: *Donchian 50 + MACD* (1,14)
   ist exakt so gut wie Donchian ohne MACD (1,14). *Glow Ribbon Flip* ist mit Shorts kaum
   profitabel (1,07); nur Long (1,46) verdient es am Aktien-Aufwärtstrend – der Vergleich
   „EMA21-Kreuz mit festem Stop“ liegt bei 1,03.
8. Erneut: **Shorts auf Aktien kosten Geld** – alle Long+Short-Varianten sind schwächer
   als reine Long-Varianten.

## Grenzen

- Intraday-Daten von Yahoo: 1 Min nur ~7 Tage, 5/15/30 Min nur ~60 Tage, 1 Std ~2 Jahre.
  Day-Trading-Ergebnisse beruhen deshalb auf kurzen Zeiträumen.
- Video-Regeln sind oft unscharf („nah genug“, „bullische Kursbewegung“). Jede Annahme
  steht im Kopf der jeweiligen Datei unter `strategies/`.
- Treffen Stop und Ziel in derselben Kerze, wird der Stop angenommen (konservativ).
- Fundamentaldaten und Marktkapitalisierung (z. B. bei Financial Wisdom) lassen sich mit
  Yahoo-Kursdaten nicht prüfen und wurden weggelassen.
- Nicht getestet: [Tradeciety](https://youtu.be/dDLG5VEVRL8) – Strategie beruht auf
  Ermessen (Dreiecke, Zonen, Fibonacci) und lässt sich nicht eindeutig programmieren.

## Neue Strategie hinzufügen

1. Datei `strategies/<name>.py` mit einer Funktion `run(symbols, ...) -> list[Trade]` anlegen
   (Vorlage: `orb15.py` für Intraday, `ema_rsi_engulf.py` für Tageskerzen).
2. Im Kopf der Datei Quelle (Video, TradingView-Link, Buch), Regeln und eigene Annahmen dokumentieren.
3. In `run_all.py` in `jobs` und `VIDEOS` eintragen und `python -m strategy_lab.run_all` starten.
4. Wo möglich eine **Vergleichs-Variante** ohne das besondere Signal mittesten.

> Keine Anlageberatung. Vergangene Ergebnisse sagen nichts über zukünftige Gewinne aus.
