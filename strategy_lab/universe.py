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


# Alle aktuellen S&P-500-Mitglieder (Wikipedia, Stand 13.10.2026) – für den Portfolio-Test.
SP500_ALL = [
    "A", "AAPL", "ABBV", "ABNB", "ABT", "ACGL", "ACN", "ADBE", "ADI", "ADM",
    "ADP", "ADSK", "AEE", "AEP", "AES", "AFL", "AIG", "AIZ", "AJG", "AKAM",
    "ALB", "ALGN", "ALL", "ALLE", "AMAT", "AMCR", "AMD", "AME", "AMGN", "AMP",
    "AMT", "AMZN", "ANET", "AON", "AOS", "APA", "APD", "APH", "APO", "APP",
    "APTV", "ARE", "ARES", "ATO", "AVGO", "AVY", "AWK", "AXON", "AXP", "AZO",
    "BA", "BAC", "BALL", "BAX", "BBY", "BDX", "BE", "BEN", "BF-B", "BG",
    "BIIB", "BKNG", "BKR", "BLK", "BMY", "BNY", "BR", "BRK-B", "BRO", "BSX",
    "BX", "BXP", "C", "CAH", "CARR", "CASY", "CAT", "CB", "CBOE", "CBRE",
    "CCI", "CCL", "CDNS", "CDW", "CEG", "CF", "CFG", "CHD", "CHRW", "CHTR",
    "CI", "CIEN", "CINF", "CL", "CLX", "CMCSA", "CME", "CMG", "CMI", "CMS",
    "CNC", "CNP", "COF", "COHR", "COIN", "COO", "COP", "COR", "COST", "CPAY",
    "CPRT", "CPT", "CRH", "CRL", "CRM", "CRWD", "CSCO", "CSGP", "CSX", "CTAS",
    "CTSH", "CVNA", "CVS", "CVX", "D", "DAL", "DASH", "DD", "DDOG", "DE",
    "DECK", "DELL", "DG", "DGX", "DHI", "DHR", "DIS", "DLR", "DLTR", "DOC",
    "DOV", "DOW", "DPZ", "DRI", "DTE", "DUK", "DVA", "DVN", "DXCM", "EBAY",
    "ECHO", "ECL", "ED", "EFX", "EG", "EIX", "EL", "ELV", "EME", "EMR",
    "EOG", "EQIX", "EQT", "ERIE", "ES", "ESS", "ETN", "ETR", "EVRG", "EW",
    "EXC", "EXE", "EXPD", "EXPE", "EXR", "F", "FANG", "FAST", "FCX", "FDS",
    "FDX", "FDXF", "FE", "FERG", "FFIV", "FICO", "FIS", "FISV", "FITB", "FIX",
    "FLEX", "FOX", "FOXA", "FRT", "FSLR", "FTNT", "FTV", "GD", "GDDY", "GE",
    "GEHC", "GEN", "GEV", "GILD", "GIS", "GL", "GLW", "GM", "GNRC", "GOOG",
    "GOOGL", "GPC", "GPN", "GRMN", "GS", "GWW", "HAL", "HAS", "HBAN", "HCA",
    "HD", "HIG", "HII", "HLT", "HON", "HONA", "HOOD", "HPE", "HPQ", "HRL",
    "HSIC", "HST", "HSY", "HUBB", "HUM", "HWM", "IBKR", "IBM", "ICE", "IDXX",
    "IEX", "IFF", "ILMN", "INCY", "INTC", "INTU", "INVH", "IP", "IQV", "IR",
    "IRM", "ISRG", "IT", "ITW", "IVZ", "J", "JBHT", "JBL", "JCI", "JKHY",
    "JNJ", "JPM", "KDP", "KEY", "KEYS", "KHC", "KIM", "KKR", "KLAC", "KMB",
    "KMI", "KO", "KR", "KVUE", "L", "LDOS", "LEN", "LH", "LHX", "LII",
    "LIN", "LITE", "LLY", "LMT", "LNT", "LOW", "LRCX", "LULU", "LUV", "LVS",
    "LYB", "LYV", "MA", "MAA", "MAR", "MAS", "MCD", "MCHP", "MCK", "MCO",
    "MDLZ", "MDT", "MET", "META", "MGM", "MKC", "MLM", "MMM", "MNST", "MO",
    "MOS", "MPC", "MPWR", "MRK", "MRNA", "MRSH", "MRVL", "MS", "MSCI", "MSFT",
    "MSI", "MTB", "MTD", "MU", "NCLH", "NDAQ", "NDSN", "NEE", "NEM", "NFLX",
    "NI", "NKE", "NOC", "NOW", "NRG", "NSC", "NTAP", "NTRS", "NUE", "NVDA",
    "NVR", "NWS", "NWSA", "NXPI", "O", "ODFL", "OKE", "OMC", "ON", "ORCL",
    "ORLY", "OTIS", "OXY", "P", "PANW", "PAYX", "PCAR", "PCG", "PEG", "PEP",
    "PFE", "PFG", "PG", "PGR", "PH", "PHM", "PKG", "PLD", "PLTR", "PM",
    "PNC", "PNR", "PNW", "PODD", "PPG", "PPL", "PRU", "PSA", "PSX", "PTC",
    "PWR", "PYPL", "Q", "QCOM", "RCL", "RDDT", "REG", "REGN", "RF", "RJF",
    "RL", "RMD", "ROK", "ROL", "ROP", "ROST", "RSG", "RTX", "RVTY", "SBAC",
    "SBUX", "SCHW", "SHW", "SJM", "SKYD", "SLB", "SMCI", "SNA", "SNDK", "SNPS",
    "SO", "SOLV", "SPG", "SPGI", "SRE", "STE", "STLD", "STT", "STX", "STZ",
    "SW", "SWK", "SWKS", "SYF", "SYK", "SYY", "T", "TDG", "TDY", "TECH",
    "TEL", "TER", "TFC", "TGT", "TJX", "TKO", "TMO", "TMUS", "TPL", "TPR",
    "TRGP", "TRMB", "TROW", "TRV", "TSCO", "TSLA", "TSN", "TT", "TTWO", "TWLO",
    "TXN", "TXT", "TYL", "UAL", "UBER", "UDR", "UHS", "ULTA", "UNH", "UNP",
    "UPS", "URI", "USB", "V", "VEEV", "VICI", "VLO", "VLTO", "VMC", "VMRK",
    "VRSK", "VRSN", "VRT", "VRTX", "VST", "VTR", "VTRS", "VYLR", "VZ", "WAB",
    "WAT", "WDAY", "WDC", "WEC", "WELL", "WFC", "WM", "WMB", "WMT", "WRB",
    "WSM", "WST", "WTW", "WY", "WYNN", "XEL", "XOM", "XYL", "XYZ", "YUM",
    "ZBH", "ZBRA", "ZTS",
]
