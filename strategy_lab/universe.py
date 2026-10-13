"""Großes Test-Universum: 200 Werte aus S&P 500 und DAX (Stand 13.10.2026).

DAX: alle 40 aktuellen Mitglieder (Xetra-Kürzel, Airbus als AIR.DE).
S&P 500: 160 Werte, Zufallsauswahl aus den 503 aktuellen Mitgliedern, proportional
nach GICS-Sektor, fester Seed 2026 – also NICHT nach Erfolg ausgesucht.
Grenze: heutige Indexmitglieder -> Survivorship-Bias (Pleiten und Absteiger seit 2005
fehlen). Werte mit kürzerer Historie (Börsengang nach 2005) werden ab Börsengang getestet.
Liste fest eingetragen, damit jeder wöchentliche Lauf dieselben Werte testet.
"""

DAX40 = [
    "ADS.DE", "AIR.DE", "ALV.DE", "BAS.DE", "BAYN.DE", "BEI.DE", "BMW.DE", "BNR.DE", "CBK.DE", "CON.DE", "DTG.DE", "DBK.DE", "DB1.DE", "DHL.DE", "DTE.DE", "EOAN.DE", "FRE.DE", "FME.DE", "G1A.DE", "HNR1.DE", "HEI.DE", "HEN3.DE", "IFX.DE", "MBG.DE", "MRK.DE", "MTX.DE", "MUV2.DE", "PAH3.DE", "QIA.DE", "RHM.DE", "RWE.DE", "SAP.DE", "G24.DE", "SIE.DE", "ENR.DE", "SHL.DE", "SY1.DE", "VOW3.DE", "VNA.DE", "ZAL.DE",
]

SP500_160 = [
    # Communication Services
    "FOXA", "GOOG", "GOOGL", "LYV", "NWS", "NWSA", "T",
    # Consumer Discretionary
    "AZO", "CCL", "DASH", "DPZ", "LEN", "MAR", "MCD", "MGM", "NKE", "RL", "ROST", "TJX", "TPR", "TSCO", "TSLA",
    # Consumer Staples
    "BF-B", "CHD", "COST", "DLTR", "EL", "KO", "KVUE", "MDLZ", "MO", "TGT", "TSN",
    # Energy
    "DVN", "EQT", "KMI", "OXY", "PSX", "SLB", "XOM",
    # Financials
    "AFL", "AMP", "APO", "BAC", "BLK", "BNY", "BRO", "C", "CFG", "CINF", "COF", "CPAY", "FISV", "FITB", "GL", "IBKR", "ICE", "JPM", "MSCI", "MTB", "TFC", "TRV", "V", "XYZ",
    # Health Care
    "ALGN", "AMGN", "BIIB", "CNC", "CVS", "DGX", "DHR", "DVA", "ELV", "EW", "JNJ", "MDT", "MTD", "PFE", "PODD", "REGN", "STE", "SYK", "UHS",
    # Industrials
    "AME", "AXON", "BE", "CMI", "CSX", "DD", "EMR", "FIX", "FTV", "GD", "IEX", "IR", "ITW", "JBHT", "MMM", "PCAR", "PH", "ROL", "SNA", "TXT", "UAL", "UBER", "UNP", "URI", "VRSK", "VRT",
    # Information Technology
    "AAPL", "ADBE", "AKAM", "AMD", "ANET", "CTSH", "DDOG", "DELL", "FICO", "HPE", "IBM", "KEYS", "KLAC", "MPWR", "MRVL", "NVDA", "P", "Q", "QCOM", "TEL", "TER", "TRMB", "TWLO", "ZBRA",
    # Materials
    "AVY", "CF", "IFF", "LIN", "MOS", "NUE", "PPG", "SHW",
    # Real Estate
    "EQIX", "IRM", "MAA", "O", "PLD", "PSA", "REG", "SBAC", "WY",
    # Utilities
    "AEE", "ATO", "AWK", "CEG", "ED", "EXC", "LNT", "PCG", "SO", "VST",]

BIG = DAX40 + SP500_160
