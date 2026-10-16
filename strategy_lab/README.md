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

> **Verbindlich für jeden wöchentlichen Lauf:**
> 1. Nach `run_all` immer `python -m strategy_lab.robustness` ausführen.
> 2. Kriterien und Parameter in `robustness.py` (Trennjahre, Bärenmarkt-Regel, Schwellen,
>    Seed, Zahl der Simulationen) **nicht ändern**, um ein Ergebnis zu verbessern. Keinen
>    eigenen Testzeitraum wählen und keine Jahre oder Krisen ausschließen.
> 3. Den Abschnitt „Robustheits-Prüfung“ unten aktualisieren und in der Abschlussnachricht
>    für jede neue Strategie das Urteil (robust bzw. x/4 Kriterien) nennen.
> 4. **Großer Test ist Pflicht** für jede neue Tages-/Wochenstrategie: in `big_test.py` in
>    `jobs` eintragen (mit Vergleichs-Variante) und `python -m strategy_lab.big_test --only
>    "<Name>"` ausführen (ersetzt nur deren Trades, rechnet Robustheit und Momentum-Filter
>    für alle neu). **Maßgeblich für Rangliste und Urteil „robust“ sind die 200 Werte**
>    (`results/big/`), die 26 Werte aus `run_all` sind nur der schnelle Vortest. Tabelle im
>    Abschnitt „Großer Test“ aktualisieren und in der Abschlussnachricht beide PF nennen.
>    Day-Trading/Forex bleiben bei den kleinen Listen (Yahoo liefert dafür zu kurze Historie).
>    Teil-Läufe nutzen die neuesten Kursdaten, ältere Strategien die vom letzten Volllauf –
>    darum etwa monatlich einmal den kompletten großen Test laufen lassen.
> 5. Vor dem Push `git pull --rebase origin claude/quirky-cannon-ke5yz8`, kein Force-Push.

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

> Schneller Vortest mit 26 Werten (`run_all`). Für Tages-/Wochenstrategien zählt die
> Tabelle im Abschnitt **„Großer Test: 200 Werte aus S&P 500 und DAX“** weiter unten.

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

## Robustheits-Prüfung

```bash
python -m strategy_lab.robustness     # nach run_all; schreibt results/robustness.csv
```

Kein einzelner, von Hand gewählter Zeitraum entscheidet. Geprüft wird (Details im Kopf von
`robustness.py`):

- **Alle Trennjahre 2008–2023:** Profit-Faktor vor und nach jedem möglichen Trennjahr.
- **Jedes Kalenderjahr einzeln** (festes Raster, Jahre mit mind. 5 Trades).
- **Marktphasen nach objektiver Regel:** Bärenmarkt = SPY > 20 % unter seinem Hoch
  (erfasst 2008/09, COVID 2020 und 2022 automatisch, ohne Daten auszuwählen).
- **Zufallstest:** gleiche Werte und Haltedauern, zufällige Einstiegstage, 1.000 Durchläufe.
  Gegenprobe mit zufälligen Trades ergibt p ≈ 0,5 – der Test bevorzugt keine Seite.
- **Bootstrap** des Profit-Faktors und **Holm-Korrektur** für die vielen getesteten Strategien.
- **Jüngere Jahre (nur Zusatzinfo, nicht Teil des Urteils):** `pf_letzte5` (Profit-Faktor
  der letzten 5 Kalenderjahre), `jahre_letzte5_pf>1`, `jahre_pf>1_gewichtet_%` (positive
  Jahre, gewichtet: letzte 5 Jahre x3, die 8 davor x2, ältere x1) und `hinweis_letzte5`
  = „zuletzt schwächer“, wenn der PF der letzten 5 Jahre <= 1 oder < 80 % des Gesamt-PF ist.

**„Robust“ (vorab festgelegt):** Zufallstest korrigiert p < 0,05 · Bootstrap-5-%-Quantil > 1 ·
mind. 70 % der Jahre positiv · vor und nach jedem Trennjahr PF > 1.

**Ergebnis (Stand 12.10.2026):** Robust sind nur **kurzfristige Mean-Reversion-Strategien**
(Kauf nach Rückgang, Verkauf bei Stärke): *Connors RSI(2)* (PF 1,77, 82 % der Jahre positiv,
schlechtestes Jahr 2008 mit 0,62, im Bärenmarkt 2,31) und die *Quantified-Strategies-Regeln*
(1,40 auf allen Werten, 1,92 auf SPY). Allerdings besteht auch der schlichte Vergleich
„Kauf nach rotem Tag“ (1,28) – der Effekt ist allgemein, die Signale verstärken ihn nur.
Alle Trendfolge- und Ausbruchs-Strategien schlagen **zufällige Einstiegstage nicht**: Ihr
Gewinn kommt aus dem Anstieg der getesteten Aktien seit 2005, nicht vom Signal.
Wichtig: Die Mean-Reversion-Quellen nennen **keinen Stop-Loss** – das reale Verlustrisiko in
Crashs ist größer, als R und Drawdown zeigen.

**Letzte 5 Jahre (2022–2026):** Die Gewichtung nach Alter ändert kaum etwas – die
Rangfolge bleibt, kein Urteil würde kippen. *Connors RSI(2)* ist zuletzt sogar etwas besser
(1,86), *QS 3 Swing-Regeln* auf allen Werten waren in allen 5 Jahren positiv (1,33).
Einziger Hinweis „zuletzt schwächer“: *QS 3 Swing-Regeln auf SPY* (1,53 statt 1,92, nur
115 Trades). Die Wochen-Strategien legen zuletzt stark zu, ihre Vergleiche ohne Signal aber
genauso – das ist der starke Aktienmarkt seit 2023, kein Verdienst der Signale.

## Momentum-Filter (Aktienauswahl)

```bash
python -m strategy_lab.momentum_filter   # nach run_all; schreibt results/momentum_filter.csv
```

Vor jede reine Long-Strategie (Tages-/Wochenkerzen, ganze SWING-Liste) wird ein
Momentum-Filter geschaltet: Ein Trade bleibt nur, wenn die Aktie am Vortag (Wochen-
strategien: in der Vorwoche) das Kriterium erfüllt. Sieben Kriterien mit Standardwerten
aus der Literatur, nicht optimiert: über SMA200 · 12-1-Monats-Rendite > 0 · 12-1-Rendite in
der oberen Hälfte der Liste · 6-Monats-Rendite in der oberen Hälfte · 6 Monate besser als
SPY · höchstens 10 % unter dem 52-Wochen-Hoch · Dual Momentum (relativ + absolut).
Kontrolle: Zufallstest mit 5.000 Durchläufen, zufällige Einstiege **nur an Tagen, an denen
derselbe Filter erfüllt ist**, Holm-Korrektur über alle 96 Kombinationen.

**Ergebnis (Stand 13.10.2026):**
1. **Der Filter macht aus keiner Strategie eine robuste.** Alle Trendfolge- und
   Wochenstrategien bleiben auch mit Filter nicht besser als zufällige Einstiege in
   dieselben Momentum-Aktien. Robust bleiben nur *Connors RSI(2)*, *QS 3 Swing-Regeln* und
   die „roter Tag“-Vergleiche – mit jedem Filter.
2. **Bei den robusten Mean-Reversion-Strategien hilft relatives Momentum etwas:**
   12-1-Rendite in der oberen Hälfte hebt *Connors RSI(2)* von 1,77 auf 1,95 und
   *QS 3 Swing-Regeln* von 1,40 auf 1,58 (Rücksetzer bei starken Aktien kaufen). Bei QS
   ist der Unterschied zwischen behaltenen und weggefilterten Trades klar (90-%-Intervall
   +0,22 bis +0,46), bei Connors knapp (+0,06 bis +0,86). Aber: rund ein Drittel bis die
   Hälfte der Trades fällt weg, die **Summe der Gewinne sinkt** (Connors 932 % statt
   1.143 %, QS 4.130 % statt 6.104 %). In den letzten 5 Jahren bringt der Filter bei Connors
   nichts (1,86 mit und ohne).
3. **Am meisten im Schnitt bringen 6-Monats-Kriterien** (relativ zur Liste oder besser als
   SPY: Ø +0,14 bis +0,16 PF, bei 92–100 % der Strategien positiv). Der Großteil davon steckt
   aber schon im Zufallstest mit Filter (Ø +0,15 bis +0,19) – es ist der allgemeine
   Momentum-Effekt, kein besseres Timing der Strategien.
4. **Nähe zum 52-Wochen-Hoch schadet** (Ø −0,10). Absolutes Momentum und SMA200 ändern kaum
   etwas (+0,04 / +0,05).
5. Wochenstrategien schwanken mit Filter stark (−0,5 bis +0,8), weil oft nur 200–500 Trades
   übrig bleiben – dort keine Schlüsse ziehen.

Vorsicht: Die Bootstrap-Vergleiche in Punkt 2 wurden nach Sicht der Ergebnisse für die
besten Filter gerechnet und sind daher optimistisch.

## Großer Test: 200 Werte aus S&P 500 und DAX

```bash
python -m strategy_lab.big_test   # ca. 25 Min.; schreibt results/big/
```

Universum (`universe.py`): alle **40 DAX-Werte** + **160 S&P-500-Werte**, zufällig gezogen
je GICS-Sektor (Seed 2026) – also nicht nach Erfolg ausgesucht. Alle Tages-/Wochen-
strategien, gleiche Kosten, gleiche Robustheits-Kriterien. Grenze: heutige Indexmitglieder
(Survivorship-Bias bleibt), Bärenmarkt-Regel weiter über SPY.

| Strategie | PF 26 Werte | PF 200 Werte | PF letzte 5 J. | Gewinnjahre | PF Strategie / Zufall | Urteil |
|---|---|---|---|---|---|---|
| Squeeze + EMA21/34 (1w) | 2,54 | **1,97** | 1,78 | 77 % | 2,11 / 2,30 | nein (3/4) |
| Vergleich: EMA21/34 ohne Squeeze (1w) | 2,47 | **1,94** | 1,65 | 77 % | 2,15 / 2,26 | nein (3/4) |
| Vergleich: 6-Wochen-Hoch-Ausbruch (1w) | 2,68 | **1,67** | 1,44 | 73 % | 1,81 / 2,02 | nein (3/4) |
| Wochen-Ausbruch + MACD-Ausstieg (1w) | 1,88 | **1,49** | 1,36 | 68 % | 1,54 / 1,93 | nein (2/4) |
| Connors RSI(2) (1d) | 1,77 | **1,47** | 1,24 | 82 % | 1,52 / 1,17 | robust |
| Glow Ribbon Flip (1d, nur Long) | 1,46 | **1,37** | 1,18 | 77 % | 1,41 / 1,53 | nein (3/4) |
| Vergleich: EMA21/34 ohne Squeeze (1d) | 1,50 | **1,32** | 1,20 | 73 % | 1,32 / 1,41 | nein (3/4) |
| QS 3 Swing-Regeln (1d) | 1,40 | **1,29** | 1,20 | 95 % | 1,35 / 1,18 | robust |
| EMA200 + RSI + Engulfing (1d) | 1,43 | **1,28** | 1,12 | 68 % | 1,35 / 1,63 | nein (2/4) |
| Squeeze + EMA21/34 (1d) | 1,42 | **1,27** | 1,16 | 77 % | 1,29 / 1,43 | nein (3/4) |
| Vergleich: grüne Kerze > EMA200 (1d) | 1,34 | **1,25** | 1,12 | 77 % | 1,32 / 1,62 | nein (3/4) |
| Vergleich: Kauf nach rotem Tag (1d) | 1,28 | **1,23** | 1,13 | 82 % | 1,26 / 1,18 | robust |
| Vergleich: roter Tag > SMA200 (1d) | 1,26 | **1,20** | 1,10 | 77 % | 1,22 / 1,14 | robust |
| EMA50 Pullback (1d) | 1,14 | **1,01** | 0,91 | 48 % | 0,97 / 1,65 | nein (0/4) |
| Glow Ribbon Flip (1d) | 1,07 | **1,01** | 0,98 | 45 % | 0,98 / 1,51 | nein (0/4) |
| Donchian 50 + MACD (1d) | 1,14 | **0,99** | 0,81 | 59 % | 0,95 / 1,77 | nein (0/4) |
| Vergleich: Donchian 50 ohne MACD (1d) | 1,14 | **0,99** | 0,82 | 59 % | 0,95 / 1,77 | nein (0/4) |
| Vergleich: EMA21-Kreuz, fester Stop (1d) | 1,03 | **0,98** | 1,00 | 59 % | 0,97 / 1,22 | nein (0/4) |

**Ergebnis (Stand 13.10.2026):**
1. **Alle Profit-Faktoren sinken** gegenüber der kleinen Liste (z. B. Squeeze 1w 2,54 → 1,97,
   Connors 1,77 → 1,47, QS 1,40 → 1,29) – die 26 Werte mit vielen Tech-Gewinnern waren zu
   günstig.
2. **Das Urteil bleibt gleich:** robust sind nur *Connors RSI(2)*, *QS 3 Swing-Regeln* und
   die beiden „roter Tag“-Vergleiche. Alle Trend-/Wochenstrategien sind schlechter als
   zufällige Einstiege mit gleicher Haltedauer.
3. **Verlierer werden sichtbar:** *EMA50 Pullback*, *Glow Ribbon (Long+Short)* und
   *Donchian 50 + MACD* liegen bei PF ≈ 1,0, zuletzt darunter.
4. **Die robusten Strategien sind zuletzt schwächer:** Connors 1,24 und QS 1,20 in den
   letzten 5 Jahren (gesamt 1,47 / 1,29).
5. **DAX schwächer als USA:** Connors 1,34 (DAX) vs. 1,50 (USA), QS 1,07 vs. 1,36.
6. **Momentum-Filter** (`results/big/momentum_filter.csv`, 5.000 Zufallsdurchläufe): relatives
   12-1-Momentum hebt Connors auf 1,53 und QS auf 1,37 – deutlich weniger als auf der kleinen
   Liste, bei 20–40 % weniger Gesamtgewinn. Keine Trend-/Wochenstrategie wird mit einem Filter
   besser als zufällige Einstiege in dieselben Momentum-Aktien.

## Connors RSI(2) mit Stop-Loss

```bash
python -m strategy_lab.connors_stops   # schreibt results/connors_stops.csv
```

Das Original hat keinen Stop. Getestet (vorab festgelegt): Stop 5 % / 10 % unter Einstieg,
2 / 3 ATR(14) unter Einstieg, Zeit-Stop nach 10 Handelstagen. Der Ausstieg „Schluss > SMA5“
bleibt immer aktiv; Preis-Stops werden ab dem Folgetag über das Tagestief geprüft, Kurslücken
zur Eröffnung gefüllt.

| 200 Werte | PF | Ø je Trade | Summe | 1-%-Quantil | Stop-Ausstiege | PF letzte 5 J. | Urteil |
|---|---|---|---|---|---|---|---|
| ohne Stop (Original) | **1,47** | +0,49 % | 6.880 % | −12,4 % | – | 1,24 | robust |
| Zeit-Stop 10 Tage | 1,45 | +0,48 % | 6.741 % | −12,3 % | 2,9 % | 1,23 | robust |
| Stop 10 % | 1,38 | +0,42 % | 5.906 % | −10,0 % | 5,2 % | 1,20 | robust |
| Stop 3 ATR | 1,33 | +0,40 % | 5.605 % | −11,1 % | 10,2 % | 1,16 | robust |
| Stop 2 ATR | 1,27 | +0,33 % | 4.864 % | −9,1 % | 20,0 % | 1,11 | robust |
| Stop 5 % | 1,26 | +0,30 % | 4.380 % | −6,5 % | 18,3 % | 1,11 | robust |

**Ergebnis (Stand 13.10.2026):** Jeder Stop **kostet Ertrag** – je enger, desto mehr (Stop 5 %:
PF 1,47 → 1,26, Summe −36 %). Mean-Reversion kauft Schwäche; ein enger Stop verkauft genau
die Trades, die sich danach erholen. Dafür werden die großen Einzelverluste kleiner (1-%-
Quantil −12,4 % → −6,5 %). Der summierte Drawdown sinkt **nicht** (mehr, kleinere Verluste in
Serie). **Kurslücken umgeht kein Stop:** Crashs über Nacht (z. B. OXY 2020 −53 %) werden zur
Eröffnung gefüllt. Alle Varianten bleiben robust. Bester Kompromiss: **Stop 10 %** (PF 1,38,
begrenzt die Verluste, 5 % der Trades gestoppt) oder kein Preis-Stop und stattdessen kleine
Positionen. Auf 26 Werten gleiches Bild (Original 1,77, Stop 10 % 1,55, Stop 5 % 1,41).

## Connors RSI(2) als Portfolio mit Kapitalgrenze (alle S&P-500-Werte)

```bash
python -m strategy_lab.portfolio   # schreibt results/portfolio/ (summary, yearly, equity, trades)
```

Alle 503 aktuellen S&P-500-Werte (499 mit genug Historie), seit 2005. Höchstens N Positionen,
jede 1/N des Depotwerts, Kauf/Verkauf zum Schluss, bei zu vielen Signalen niedrigster
RSI(2) zuerst. Barbestand ohne Zins. Kosten 0,01 % je Seite.

| Variante | Rendite p. a. | Max. Drawdown | Sharpe | 2008 | 2022 | Letzte 5 J. p. a. | Investiert |
|---|---|---|---|---|---|---|---|
| N=5, ohne Stop | 20,4 % | −35,6 % | 1,12 | −10,1 % | +10,7 % | 13,7 % | 80 % |
| N=5, Stop 10 % | 20,0 % | −29,3 % | 1,15 | −13,7 % | +15,2 % | 13,8 % | 80 % |
| N=10, ohne Stop | 15,4 % | −29,7 % | 1,01 | −20,1 % | +2,3 % | 11,2 % | 71 % |
| N=10, Stop 10 % | 14,4 % | −28,3 % | 1,00 | −22,9 % | −3,1 % | 8,5 % | 71 % |
| **N=20, ohne Stop** | **14,0 %** | **−19,6 %** | **1,09** | −5,2 % | −7,3 % | 12,4 % | 58 % |
| N=20, Stop 10 % | 12,0 % | −22,2 % | 0,98 | −14,8 % | −14,1 % | 10,4 % | 58 % |
| N=10, Kosten 0,05 % je Seite | 11,4 % | −31,5 % | 0,79 | −21,6 % | −0,4 % | 7,3 % | 71 % |
| Vergleich: gleichgewichtet halten, gleiche Werte | 14,4 % | −52,1 % | 0,77 | −31,9 % | −11,8 % | 12,2 % | 100 % |
| Vergleich: SPY halten (ohne Dividenden) | 9,0 % | −56,5 % | 0,55 | −38,3 % | −19,5 % | 12,4 % | 100 % |

**Ergebnis (Stand 13.10.2026):**
1. **Gleiche Rendite wie Halten, aber deutlich weniger Risiko.** Fairer Maßstab ist das
   gleichgewichtete Halten derselben Werte (gleicher Survivorship-Bias): Connors mit 10–20
   Positionen bringt 14–15 % p. a. wie das Halten (14,4 %), aber mit halbem Drawdown
   (−20 bis −30 % statt −52 %), nur 58–71 % der Zeit investiert und besserem Sharpe.
2. **Die absolute Rendite ist zu günstig:** heutige Indexmitglieder seit 2005
   (Survivorship-Bias) – darum nur relativ zum gleichgewichteten Halten vergleichen.
3. **Die Auswahl nach niedrigstem RSI(2) bringt nichts:** zufällige Auswahl unter den
   Kandidaten ergibt gleich viel (N=10: 15,0–18,9 % über 8 Zufallsläufe, RSI-Auswahl 15,4 %).
   Die Unterschiede zwischen N=5/10/20 sind daher vor allem Zufall und Konzentration.
4. **Kosten sind entscheidend:** 0,05 % statt 0,01 % je Seite kostet 4 Prozentpunkte p. a.
   Ausführung in der Schlussauktion (Market-on-Close) ohne Spread ist Pflicht.
5. **Stop 10 % lohnt sich im Portfolio nicht** (außer leicht bei N=5).
6. **Zuletzt schwächer:** letzte 5 Jahre 11–14 % p. a. – etwa wie Halten (12,2 %), 2026 bisher
   bei N=10 ±0 %.
7. Empfehlung für einen Live-Test: **N=20, ohne Preis-Stop** – geringster Drawdown, bester
   Sharpe, Rendite wie Halten.

## TOP 200 nach Liquidität (monatlich, ohne Blick in die Zukunft)

```bash
python -m strategy_lab.top200   # ~1 Std.; schreibt results/top200/
```

Pool: alle aktuellen S&P-500- und DAX-Werte (~540). Zu jedem Monatsanfang die 200 Werte mit
dem höchsten Ø Tagesumsatz in USD der 63 Handelstage **vor** dem Monat (447 verschiedene Werte
waren seit 2003 mindestens einmal dabei). Ein Trade zählt nur, wenn die Aktie im Monat des
Einstiegs zur TOP 200 gehört. Gleiche Regeln, Kosten und Robustheits-Kriterien.

| Strategie | PF zufällige 200 | PF TOP 200 | PF ganzer Pool | TOP 200 letzte 5 J. | Urteil zufällig | Urteil TOP 200 |
|---|---|---|---|---|---|---|
| Squeeze + EMA21/34 (1w) | 1,97 | **1,85** | 2,10 | 1,57 | nein (3/4) | nein (3/4) |
| Vergleich: EMA21/34 ohne Squeeze (1w) | 1,94 | **1,73** | 1,96 | 1,75 | nein (3/4) | nein (3/4) |
| Vergleich: 6-Wochen-Hoch-Ausbruch (1w) | 1,67 | **1,54** | 1,67 | 1,40 | nein (3/4) | nein (3/4) |
| Connors RSI(2) (1d) | 1,47 | **1,53** | 1,48 | 1,28 | robust | robust |
| Wochen-Ausbruch + MACD-Ausstieg (1w) | 1,49 | **1,38** | 1,51 | 1,30 | nein (2/4) | nein (3/4) |
| Glow Ribbon Flip (1d, nur Long) | 1,37 | **1,31** | 1,37 | 1,17 | nein (3/4) | nein (3/4) |
| QS 3 Swing-Regeln (1d) | 1,29 | **1,31** | 1,32 | 1,22 | robust | robust |
| Vergleich: EMA21/34 ohne Squeeze (1d) | 1,32 | **1,25** | 1,30 | 1,19 | nein (3/4) | nein (2/4) |
| Squeeze + EMA21/34 (1d) | 1,27 | **1,24** | 1,28 | 1,12 | nein (3/4) | nein (3/4) |
| EMA200 + RSI + Engulfing (1d) | 1,28 | **1,22** | 1,28 | 1,13 | nein (2/4) | nein (3/4) |
| Vergleich: Kauf nach rotem Tag (1d) | 1,23 | **1,22** | 1,25 | 1,13 | robust | robust |
| Vergleich: roter Tag > SMA200 (1d) | 1,20 | **1,21** | 1,22 | 1,11 | robust | robust |
| Vergleich: grüne Kerze > EMA200 (1d) | 1,25 | **1,20** | 1,26 | 1,11 | nein (3/4) | nein (3/4) |
| Vergleich: EMA21-Kreuz, fester Stop (1d) | 0,98 | **0,99** | 0,98 | 0,99 | nein (0/4) | nein (0/4) |
| EMA50 Pullback (1d) | 1,01 | **0,99** | 1,00 | 0,88 | nein (0/4) | nein (0/4) |
| Glow Ribbon Flip (1d) | 1,01 | **0,98** | 1,00 | 0,95 | nein (0/4) | nein (0/4) |
| Vergleich: Donchian 50 ohne MACD (1d) | 0,99 | **0,94** | 0,99 | 0,83 | nein (0/4) | nein (0/4) |
| Donchian 50 + MACD (1d) | 0,99 | **0,93** | 0,99 | 0,83 | nein (0/4) | nein (0/4) |

**Ergebnis (Stand 15.10.2026):**
1. **Das Urteil ändert sich bei keiner Strategie:** robust bleiben nur *Connors RSI(2)*,
   *QS 3 Swing-Regeln* und die beiden „roter Tag“-Vergleiche.
2. **Connors RSI(2) wird mit den liquidesten Werten etwas besser** (1,47 → 1,53, letzte 5
   Jahre 1,24 → 1,28) – Rücksetzer bei großen, viel gehandelten Aktien erholen sich
   zuverlässiger. QS leicht besser (1,29 → 1,31).
3. **Trend- und Wochenstrategien werden schlechter** (Squeeze 1w 1,97 → 1,85, Ausbruch
   1,67 → 1,54): Ihr Gewinn kam zum Teil aus kleineren Werten mit starken Kursläufen.
4. Zufällige 200 und ganzer Pool liegen fast gleich – die bisherige Zufallsauswahl war
   repräsentativ. Die TOP-200-Auswahl ist näher an dem, was live gehandelt wird (große,
   liquide Werte) und vermeidet die nachträgliche Auswahl nach Größe.

## Hedgefonds- und Quant-Strategien (Portfolio-Backtest)

```bash
python -m strategy_lab.quant.run   # ~45 Min.; schreibt results/quant/
```

Neun klassische, regelbasierte Strategien aus Forschung und Fondspraxis (Quellen und Regeln im
Kopf von `quant/strategies.py` und `quant/pairs.py`): Aktien-Momentum (Jegadeesh/Titman, AQR),
Clenow „Stocks on the Move“, niedrige Schwankung (Frazzini/Pedersen), Kurzfrist-Umkehr
(Lehmann), Trendfolge über Anlageklassen (Moskowitz/Ooi/Pedersen – CTAs wie Man AHL), Dual
Momentum (Antonacci), Risk Parity (Bridgewater-Idee), Monatswechsel-Effekt, Paarhandel (Gatev
et al.). Aktien aus der monatlichen TOP 200, Kurse **inkl. Dividenden**, freies Geld verzinst
wie SHY, Kosten 0,05 % (Aktien) bzw. 0,02 % (ETFs) je Umschichtung, seit 2005 bzw. erstem Signal.
Nicht testbar mit freien Daten: Value/Quality (Bilanzdaten), Hochfrequenz/Spezialdaten.

**„Robust“ (vorab festgelegt):** höhere Sharpe-Quote als der Vergleich (Aktien: TOP 200
gleichgewichtet; sonst 60/40 SPY/IEF) · besser in ≥ 3 von 4 Zeitabschnitten · alle
Nachbar-Parameter besser · Aktienauswahl zusätzlich besser als 100 Zufallsportfolios (Holm).

| Strategie | Rendite p. a. | Sharpe | Max. DD | letzte 5 J. p. a. | Sharpe Vergleich | Abschnitte besser | Urteil |
|---|---|---|---|---|---|---|---|
| Aktien-Momentum 12-1 | 20,3 % | 0,72 | -59,9 % | 35,9 % | 0,61 | 4/4 | robust |
| Clenow Stocks on the Move | 10,3 % | 0,57 | -24,8 % | 7,3 % | 0,61 | 1/4 | nein (1/4) |
| Niedrige Schwankung | 9,5 % | 0,58 | -37,9 % | 6,6 % | 0,61 | 2/4 | nein (0/4) |
| Kurzfrist-Umkehr (Wochenverlierer) | 19,2 % | 0,66 | -57,7 % | 19,7 % | 0,61 | 1/4 | nein (2/4) |
| Trendfolge Anlageklassen (TSMOM) | 4,7 % | 0,56 | -11,9 % | 3,6 % | 0,60 | 1/4 | nein (0/3) |
| Dual Momentum GEM | 8,4 % | 0,47 | -35,9 % | 6,8 % | 0,59 | 1/4 | nein (0/3) |
| Risk Parity (All-Weather-Idee) | 5,9 % | 0,64 | -18,9 % | 4,4 % | 0,61 | 2/4 | nein (2/3) |
| Monatswechsel-Effekt SPY | 3,6 % | 0,24 | -14,9 % | 3,0 % | 0,59 | 1/4 | nein (0/3) |
| Paarhandel (Gatev et al.) | 3,2 % | 0,23 | -15,0 % | 3,4 % | 0,59 | 0/4 | nein (0/3) |
| Vergleich: TOP 200 gleichgewichtet | 13,2 % | 0,61 | -57,5 % | 13,6 % | – | – | – |
| Vergleich: 60 % SPY / 40 % IEF | 8,1 % | 0,59 | -32,6 % | 7,2 % | – | – | – |
| Vergleich: SPY | 10,9 % | 0,53 | -55,2 % | 13,1 % | – | – | – |

> **Korrektur (16.10.2026):** Diese Tabelle nutzt heutige Indexmitglieder auch für
> frühere Jahre – spätere Aufsteiger (CVNA, APP, SMCI …) wurden schon vor ihrer Aufnahme
> gekauft. Mit Stichtags-Universum (Abschnitt „Fairer Vergleich“ unten) besteht **keine**
> Strategie mehr, auch Momentum nicht (Sharpe 0,55 statt 0,72).

**Ergebnis (Stand 15.10.2026, vor der Korrektur):**
1. **Nur Aktien-Momentum 12-1 besteht alle Prüfungen** (20,3 % p. a., Sharpe 0,72 vs. 0,61,
   in allen 4 Zeitabschnitten besser, alle Nachbar-Parameter besser, besser als alle 100
   Zufallsportfolios). **Aber:** größter Einbruch −60 % (2008: −47 %), sehr konzentriert auf
   die Gewinner des Moments (2024: +73 %, 2026 bisher +78 %) – Rückschläge wie der
   „Momentum-Crash“ 2009 (+17 % gegenüber +39 % des Markts) gehören dazu.
2. **Kurzfrist-Umkehr** hat eine gute Sharpe (0,66), ist aber nur in 1 von 4 Abschnitten besser.
3. **Risk Parity** hat die beste Sharpe der Mischportfolios (0,64) bei −19 % Einbruch, aber
   nur 5,9 % p. a. – nicht in allen Abschnitten besser als 60/40.
4. **Trendfolge (TSMOM)** schützt am besten (−12 % Einbruch, 2008 positiv), bringt ohne Hebel
   aber nur 4,7 % p. a.; Fonds setzen dafür Hebel ein.
5. Clenow, niedrige Schwankung, Dual Momentum, Monatswechsel und Paarhandel schlagen ihren
   Vergleich nicht. Paarhandel ist seit den 2000ern bekannt und nach Kosten fast ausgereizt.
6. Survivorship-Bias bleibt (Pool = heutige Indexmitglieder) – trifft Momentum vermutlich
   stärker, weil abgestürzte frühere Gewinner fehlen.

## Fairer Vergleich mit Stichtags-Universum (Connors, Momentum, Kombinationen)

```bash
python -m strategy_lab.quant.compare            # Vergleich + 5.000-€-Konto
python -m strategy_lab.quant.run --pit          # 9 Quant-Strategien mit Stichtags-Universum
python -m strategy_lab.quant.momentum_research  # Merkmale der künftigen Momentum-Gewinner
python -m strategy_lab.quant.explore_resid      # explorativ: Residual-Momentum
```

**Stichtags-Universum:** nur US-Werte, jeder erst ab seinem Aufnahmedatum in den S&P 500
(`quant/sp500_aufnahme.csv`, Wikipedia), daraus die monatliche TOP 200 nach Liquidität
(~150–196 Werte). 293 der 503 heutigen Mitglieder kamen erst nach 2005 dazu – ohne diese
Regel kaufte der Test z. B. CVNA, APP oder SMCI Jahre vor ihrem Aufstieg. Später
entfernte Verlierer fehlen weiterhin (Rest-Verzerrung zugunsten aller Long-Strategien).
Alles mit derselben Engine, Kursen inkl. Dividenden, Kosten 0,05 % je Umschichtung.

| Variante | Rendite p. a. | Sharpe | Max. DD | 2008 | letzte 5 J. p. a. | Urteil |
|---|---|---|---|---|---|---|
| Connors RSI(2), 20 Pos. | 9,5 % | 0,74 | -19,6 % | 4,6 % | 7,2 % | nein (2/3) |
| Momentum 12-1, 20 Pos. | 13,9 % | 0,55 | -54,9 % | -42,1 % | 18,9 % | nein (0/3) |
| Momentum + Marktfilter | 11,9 % | 0,55 | -32,6 % | 6,6 % | 1,6 % | nein (1/3) |
| Momentum + Schwankungssteuerung | 11,5 % | 0,54 | -35,2 % | -26,3 % | 13,2 % | nein (0/3) |
| 50 % Momentum + 50 % Connors | 12,2 % | 0,66 | -30,5 % | -21,3 % | 14,0 % | nein (2/3) |
| 50 % Momentum+Filter + 50 % Connors | 11,0 % | 0,67 | -22,0 % | 5,7 % | 5,0 % | nein (2/3) |
| Vergleich: TOP 200 gleichgewichtet | 12,7 % | 0,59 | -55,8 % | -35,9 % | 12,4 % | – |
| Vergleich: SPY | 10,8 % | 0,53 | -55,2 % | -36,8 % | 12,8 % | – |

**9 Quant-Strategien – Sharpe vorher (heutige Mitglieder) und mit Stichtags-Universum:**

| Strategie | Sharpe vorher | Sharpe Stichtag | Rendite p. a. Stichtag | Urteil Stichtag |
|---|---|---|---|---|
| Aktien-Momentum 12-1 | 0,72 | **0,55** | 13,9 % | nein (0/4) |
| Clenow Stocks on the Move | 0,57 | **0,56** | 9,8 % | nein (1/4) |
| Niedrige Schwankung | 0,58 | **0,59** | 9,7 % | nein (1/4) |
| Kurzfrist-Umkehr (Wochenverlierer) | 0,66 | **0,63** | 17,8 % | nein (1/4) |
| Trendfolge Anlageklassen (TSMOM) | 0,56 | **0,55** | 4,7 % | nein (0/3) |
| Dual Momentum GEM | 0,47 | **0,46** | 8,3 % | nein (0/3) |
| Risk Parity (All-Weather-Idee) | 0,64 | **0,63** | 5,9 % | nein (2/3) |
| Monatswechsel-Effekt SPY | 0,24 | **0,23** | 3,5 % | nein (0/3) |
| Paarhandel (Gatev et al.) | 0,23 | **0,24** | 3,3 % | nein (0/3) |

**Merkmale, die künftige Momentum-Gewinner vorhersagen sollen** (Rangkorrelation „IC“ mit
der Folgemonats-Rendite unter den 40 besten 12-1-Werten; 0 = keine Vorhersagekraft):

| Merkmal | Quelle | IC 2005–15 | IC 2016–26 | bestätigt |
|---|---|---|---|---|
| 12-1-Rendite selbst (stärkste Gewinner) | Jegadeesh & Titman 1993 | 0,015 | 0,027 | nein |
| gleichmäßiger Anstieg statt Sprünge (−Informations-Diskretheit) | Da, Gurun & Warachka 2014 'Frog in the Pan' | 0,009 | -0,009 | nein |
| Residual-Momentum: Rendite über dem Markt (Beta-bereinigt) / Restschwankung | Blitz, Huij & Martens 2011 | 0,009 | 0,018 | nein |
| Nähe zum 52-Wochen-Hoch | George & Hwang 2004 | -0,011 | -0,037 | nein |
| 12-1-Rendite / Schwankung (Rendite je Risiko) | Rachev et al. 2007 | 0,006 | 0,008 | nein |
| Trendqualität: R² der Regression über 12 Monate | Clenow 2015 | -0,003 | -0,004 | nein |
| niedrige 12-Monats-Schwankung | Frazzini & Pedersen 2014 | -0,007 | -0,038 | nein |
| kein Umsatzanstieg (−Umsatz 3 M / 12 M) | Lee & Swaminathan 2000 | 0,005 | -0,029 | nein |
| mittelfristiges Momentum 12-7 Monate | Novy-Marx 2012 | 0,022 | 0,000 | nein |
| Momentum des Sektors (Ø 12-1 der Sektor-Werte) | Moskowitz & Grinblatt 1999 | 0,001 | -0,000 | nein |
| kein extremer Tagesgewinn im letzten Monat (−Max-Tagesrendite) | Bali, Cakici & Whitelaw 2011 | 0,005 | -0,026 | nein |
| Rücksetzer im letzten Monat (−1-Monats-Rendite) | Jegadeesh 1990 | -0,002 | 0,001 | nein |

**5.000-€-Konto** (Kosten je Order = 0,02 % + 0,50 $ / Ordergröße):

| Pos. | Variante | Rendite p. a. | Sharpe | Max. DD | letzte 5 J. p. a. |
|---|---|---|---|---|---|
| 3 | Connors RSI(2) | 9,4 % | 0,49 | -31,7 % | -2,1 % |
| 3 | Momentum 12-1 | 20,1 % | 0,61 | -66,3 % | 41,3 % |
| 3 | Momentum + Marktfilter | 17,6 % | 0,60 | -42,4 % | 12,5 % |
| 3 | 50/50 Momentum+Filter / Connors | 14,3 % | 0,64 | -33,2 % | 6,6 % |
| 5 | Connors RSI(2) | 10,0 % | 0,57 | -24,8 % | 1,6 % |
| 5 | Momentum 12-1 | 20,1 % | 0,65 | -59,4 % | 26,7 % |
| 5 | Momentum + Marktfilter | 17,3 % | 0,64 | -38,7 % | 3,8 % |
| 5 | 50/50 Momentum+Filter / Connors | 14,2 % | 0,70 | -29,0 % | 3,9 % |
| 10 | Connors RSI(2) | 7,1 % | 0,45 | -29,6 % | 2,9 % |
| 10 | Momentum 12-1 | 16,2 % | 0,58 | -56,4 % | 22,8 % |
| 10 | Momentum + Marktfilter | 13,8 % | 0,57 | -36,4 % | 2,1 % |
| 10 | 50/50 Momentum+Filter / Connors | 10,8 % | 0,59 | -26,1 % | 3,4 % |

**Ergebnis (Stand 16.10.2026):**
1. **Der Vorsprung von Momentum kam großteils aus der Aktienauswahl mit heutigem Wissen.**
   Mit Stichtags-Universum: 13,9 % statt 20,0 % p. a., Sharpe 0,55 – unter dem
   gleichgewichteten Halten (0,59). Mit Marktfilter halbiert sich der Einbruch (−33 % statt
   −55 %), die Sharpe bleibt 0,55.
2. **Connors RSI(2) ist kaum betroffen** (Sharpe 0,74, Einbruch −20 %, 2008 +4,6 %) und hat
   die beste Rendite je Risiko – aber **sein Vorteil schrumpft**: Sharpe je Abschnitt
   1,05 / 1,08 / 0,46 / 0,47 gegen 0,25 / 0,86 / 0,73 / 0,82 beim Halten. Seit 2016
   schlechter als Halten.
3. **Beste Mischung: 50 % Momentum mit Marktfilter + 50 % Connors** (Sharpe 0,67, Einbruch
   −22 %, 2008 +5,7 %). Die Korrelation der beiden ist nur 0,54 – sie ergänzen sich.
   Nicht „robust“ nach den Regeln (nur 2/4 Abschnitte besser).
4. **Keines der 12 Merkmale sagt die künftigen Gewinner unter den Momentum-Kandidaten
   voraus** (alle IC nahe 0, keines besteht schon die Entdeckungsphase). Am nächsten kommt
   *Residual-Momentum* (Blitz et al.): als eigene Strategie Sharpe 0,66 vs. 0,59, besser
   als 97 % der Zufallsauswahlen, aber nur in 2 von 4 Abschnitten besser – ein Hinweis,
   kein Beweis (`results/quant/explorativ_residual.csv`).
5. **Bei 5.000 €** stehen Momentum-Varianten mit 3–5 Positionen auf dem Papier am besten da,
   sind aber extrem konzentriert (Einbruch −40 bis −66 %) und hängen an einzelnen Werten;
   Connors mit 5 Positionen brachte in den letzten 5 Jahren nur 1,6 % p. a.
6. Nicht testbar mit freien Daten, laut Forschung aber die stärkste Ergänzung zu Momentum:
   **Gewinn-Momentum** (Gewinnüberraschungen, Analysten-Anhebungen; Chan, Jegadeesh &
   Lakonishok 1996) – braucht Gewinn- und Schätzungsdaten.

## Grenzen

- Intraday-Daten von Yahoo: 1 Min nur ~7 Tage, 5/15/30 Min nur ~60 Tage, 1 Std ~2 Jahre.
  Day-Trading-Ergebnisse beruhen deshalb auf kurzen Zeiträumen.
- Video-Regeln sind oft unscharf („nah genug“, „bullische Kursbewegung“). Jede Annahme
  steht im Kopf der jeweiligen Datei unter `strategies/`.
- Treffen Stop und Ziel in derselben Kerze, wird der Stop angenommen (konservativ).
- Yahoo-Schlusskurse sind um Splits, aber nicht um Abspaltungen und Sonderdividenden
  bereinigt; im großen Test gibt es drei solche Fehlsprünge (DB1.DE 2007, MO 2008, WY 2010).
  Sie betreffen 1–3 Trades je Strategie und ändern die Profit-Faktoren um weniger als 0,01.
- **Aufnahme-Verzerrung:** Alle Tests vor dem Abschnitt „Fairer Vergleich mit
  Stichtags-Universum“ nutzen heutige Indexmitglieder auch für frühere Jahre. Das schönt vor
  allem Trend- und Momentum-Strategien (Momentum-Sharpe 0,72 → 0,55); Connors RSI(2) ist
  kaum betroffen (0,74 → 0,74).
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
