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
> 4. Vor dem Push `git pull --rebase origin claude/quirky-cannon-ke5yz8`, kein Force-Push.

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

## Grenzen

- Intraday-Daten von Yahoo: 1 Min nur ~7 Tage, 5/15/30 Min nur ~60 Tage, 1 Std ~2 Jahre.
  Day-Trading-Ergebnisse beruhen deshalb auf kurzen Zeiträumen.
- Video-Regeln sind oft unscharf („nah genug“, „bullische Kursbewegung“). Jede Annahme
  steht im Kopf der jeweiligen Datei unter `strategies/`.
- Treffen Stop und Ziel in derselben Kerze, wird der Stop angenommen (konservativ).
- Yahoo-Schlusskurse sind um Splits, aber nicht um Abspaltungen und Sonderdividenden
  bereinigt; im großen Test gibt es drei solche Fehlsprünge (DB1.DE 2007, MO 2008, WY 2010).
  Sie betreffen 1–3 Trades je Strategie und ändern die Profit-Faktoren um weniger als 0,01.
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
