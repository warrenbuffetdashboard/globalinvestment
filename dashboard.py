import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from transformers import pipeline
import json
import os
import warnings
import logging
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----- Five fundamental data libraries -----
try:
    import xfinlink as xfl
    XFL_AVAILABLE = True
except ImportError:
    XFL_AVAILABLE = False

try:
    from alpha_vantage.fundamentaldata import FundamentalData
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    ALPHA_VANTAGE_AVAILABLE = False

try:
    from financialmodelingprep import FinancialModelingPrep
    FMP_AVAILABLE = True
except ImportError:
    FMP_AVAILABLE = False

try:
    from tiingo import TiingoClient
    TIINGO_AVAILABLE = True
except ImportError:
    TIINGO_AVAILABLE = False

# API keys from environment
ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")
TIINGO_API_KEY = os.environ.get("TIINGO_API_KEY", "")

warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)
st.set_page_config(page_title="Global Buffett Screener", layout="wide", page_icon="📊")

# ============================================
# 1. BUILD LARGE TICKER UNIVERSE (15,000+ ASSETS)
# ============================================
@st.cache_data(ttl=86400)
def build_ticker_universe():
    """Returns DataFrame with Ticker, Name, Region, AssetClass."""
    universe = []
    
    # ----- US stocks: download from GitHub (reliable) -----
    us_urls = [
        "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/all/all_tickers.txt",
        "https://raw.githubusercontent.com/jacobhobbi/StockTickerList/main/tickers.txt",
        "https://raw.githubusercontent.com/philipperemy/symbols/main/data/all_symbols.txt"
    ]
    us_symbols = []
    for url in us_urls:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                lines = resp.text.splitlines()
                for line in lines:
                    sym = line.strip().upper()
                    if sym and not sym.startswith('#'):
                        us_symbols.append(sym)
                break
        except:
            continue
    us_symbols = list(set(us_symbols))
    if len(us_symbols) < 1000:
        us_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK-B", "JPM", "V",
            "JNJ", "WMT", "PG", "UNH", "HD", "DIS", "MA", "BAC", "NFLX", "KO", "PEP", "INTC",
            "CSCO", "ADBE", "CRM", "COST", "CVX", "XOM", "WFC", "QCOM", "TXN", "AMGN", "HON",
            "LMT", "UPS", "IBM", "SBUX", "NKE", "BA", "GE", "CAT", "GS", "MS", "BLK", "AXP",
            "VZ", "T", "RTX", "LOW", "PYPL", "INTU", "MDT", "ISRG", "NOW", "SYK", "TGT", "CI",
            "ZTS", "DUK", "MO", "USB", "PNC", "COF", "EMR", "MMM", "APD", "CL", "MAR", "FDX",
            "ADP", "NSC", "ROP", "PGR", "BKNG", "UBER", "ABNB", "DASH", "SNOW", "ZS", "CRWD",
            "PANW", "OKTA", "WDAY", "TEAM", "SHOP", "ROKU", "TTD", "MRNA", "PFE", "BIIB", "GILD",
            "REGN", "VRTX", "ILMN", "IDXX", "ALGN", "DXCM", "BSX"
        ]
    for sym in us_symbols:
        universe.append({
            "Ticker": sym,
            "Name": sym,
            "Region": "North America",
            "AssetClass": "Stock"
        })
    
    # ----- International stocks (by suffix) -----
    intl_tickers = {
        "EDP.LS": "EDP - Energias de Portugal", "GALP.LS": "Galp Energia",
        "BCP.LS": "Banco Comercial Português", "JMT.LS": "Jerónimo Martins",
        "REN.LS": "REN - Redes Energéticas Nacionais", "SON.LS": "Sonae",
        "NOS.LS": "NOS", "SEM.LS": "Semapa", "COR.LS": "Corticeira Amorim",
        "ALTR.LS": "Altri", "MCP.LS": "Motociclo", "IBS.LS": "Ibersol",
        "GVOLT.LS": "Greenvolt", "CTT.LS": "CTT Correios de Portugal",
        "AZN.L": "AstraZeneca", "SHEL.L": "Shell", "ULVR.L": "Unilever",
        "HSBA.L": "HSBC", "BP.L": "BP", "GSK.L": "GSK", "DGE.L": "Diageo",
        "REL.L": "RELX", "LSEG.L": "London Stock Exchange", "LLOY.L": "Lloyds Banking",
        "BARC.L": "Barclays", "STAN.L": "Standard Chartered", "PRU.L": "Prudential",
        "AV.L": "Aviva", "LGEN.L": "Legal & General", "RIO.L": "Rio Tinto",
        "AAL.L": "Anglo American", "GLEN.L": "Glencore", "SSE.L": "SSE",
        "NG.L": "National Grid", "UU.L": "United Utilities",
        "SAP.DE": "SAP SE", "DTE.DE": "Deutsche Telekom", "VOW3.DE": "Volkswagen",
        "BAS.DE": "BASF", "BAYN.DE": "Bayer", "ADS.DE": "Adidas", "DBK.DE": "Deutsche Bank",
        "MBG.DE": "Mercedes-Benz", "BMW.DE": "BMW", "ALV.DE": "Allianz",
        "MUV2.DE": "Munich Re", "HEN3.DE": "Henkel", "FRE.DE": "Fresenius",
        "RWE.DE": "RWE", "EOAN.DE": "E.ON", "LIN.DE": "Linde", "IFX.DE": "Infineon",
        "ZAL.DE": "Zalando", "HEI.DE": "HeidelbergCement", "BEI.DE": "Beiersdorf",
        "BNP.PA": "BNP Paribas", "AIR.PA": "Airbus", "SAN.PA": "Sanofi",
        "OR.PA": "L'Oréal", "MC.PA": "LVMH", "SU.PA": "Schneider Electric",
        "TTE.PA": "TotalEnergies", "CS.PA": "AXA", "RNO.PA": "Renault",
        "CAP.PA": "Capgemini", "SAF.PA": "Safran", "MT.PA": "ArcelorMittal",
        "ENGI.PA": "Engie", "VIE.PA": "Veolia", "KER.PA": "Kering",
        "RMS.PA": "Hermès", "AC.PA": "Accor", "VIV.PA": "Vivendi",
        "NESN.SW": "Nestlé", "ROG.SW": "Roche", "NOVN.SW": "Novartis",
        "UBSG.SW": "UBS", "ZURN.SW": "Zurich Insurance", "ABBN.SW": "ABB",
        "LONN.SW": "Lonza", "GEBN.SW": "Geberit", "SIKA.SW": "Sika",
        "SREN.SW": "Swiss Re", "CFR.SW": "Richemont", "SCMN.SW": "Swisscom",
        "ASML.AS": "ASML Holding", "INGA.AS": "ING Groep", "PHIA.AS": "Philips",
        "RDSA.AS": "Shell (NL)", "UNA.AS": "Unilever NL", "AD.AS": "Ahold Delhaize",
        "HEIN.AS": "Heineken", "WKL.AS": "Wolters Kluwer", "RAND.AS": "Randstad",
        "DSM.AS": "DSM", "AKZA.AS": "AkzoNobel",
        "ENEL.MI": "Enel", "STLA.MI": "Stellantis", "ISP.MI": "Intesa Sanpaolo",
        "G.MI": "Generali", "LDO.MI": "Leonardo", "UCG.MI": "UniCredit",
        "ENI.MI": "Eni", "TIT.MI": "Telecom Italia", "PRY.MI": "Prysmian",
        "MONC.MI": "Moncler", "FERR.MI": "Ferrari", "PIR.MI": "Pirelli",
        "SAN.MC": "Banco Santander", "TEF.MC": "Telefónica", "IBE.MC": "Iberdrola",
        "REP.MC": "Repsol", "BBVA.MC": "BBVA", "ITX.MC": "Inditex",
        "FER.MC": "Ferrovial", "ACS.MC": "ACS", "AENA.MC": "Aena",
        "GRF.MC": "Grifols",
        "NOVO-B.CO": "Novo Nordisk", "MAERSK-B.CO": "Maersk", "DSV.CO": "DSV",
        "VWS.CO": "Vestas Wind", "DANSKE.CO": "Danske Bank", "CARL-B.CO": "Carlsberg",
        "ERIC-B.ST": "Ericsson", "VOLV-B.ST": "Volvo", "SEB-A.ST": "SEB",
        "SWED-A.ST": "Swedbank", "SHB-A.ST": "Handelsbanken", "ABB.ST": "ABB",
        "EQNR.OL": "Equinor", "DNB.OL": "DNB Bank", "NOKIA.HE": "Nokia",
        "KNEBV.HE": "Kone", "SAMPO.HE": "Sampo",
        "7203.T": "Toyota Motor", "9984.T": "SoftBank Group", "6758.T": "Sony Group",
        "9432.T": "Nippon Telegraph & Telephone", "8306.T": "Mitsubishi UFJ Financial",
        "8058.T": "Mitsubishi Corporation", "4502.T": "Takeda Pharmaceutical",
        "6861.T": "Keyence", "7974.T": "Nintendo", "8316.T": "Sumitomo Mitsui",
        "6098.T": "Recruit Holdings", "9983.T": "Fast Retailing", "4063.T": "Shin-Etsu Chemical",
        "8766.T": "Tokio Marine", "9433.T": "KDDI", "2914.T": "Japan Tobacco",
        "4568.T": "Daiichi Sankyo", "4901.T": "Fujifilm", "4911.T": "Shiseido",
        "005930.KS": "Samsung Electronics", "000660.KS": "SK Hynix",
        "035420.KS": "NAVER Corporation", "051910.KS": "LG Chem",
        "005380.KS": "Hyundai Motor", "068270.KS": "Celltrion",
        "006400.KS": "Samsung SDI", "017670.KS": "SK Telecom",
        "032830.KS": "Samsung Life", "055550.KS": "Shinhan Financial",
        "105560.KS": "KB Financial", "139480.KS": "Kakao",
        "0700.HK": "Tencent Holdings", "9988.HK": "Alibaba Group",
        "1299.HK": "AIA Group", "0939.HK": "China Construction Bank",
        "3988.HK": "Bank of China", "2318.HK": "Ping An Insurance",
        "1398.HK": "ICBC", "2628.HK": "China Life", "941.HK": "China Mobile",
        "1810.HK": "Xiaomi", "9618.HK": "JD.com", "3690.HK": "Meituan",
        "BABA": "Alibaba (US)", "BIDU": "Baidu", "JD": "JD.com", "PDD": "Pinduoduo",
        "TSM": "Taiwan Semiconductor",
        "HDFCBANK.NS": "HDFC Bank", "RELIANCE.NS": "Reliance Industries",
        "TCS.NS": "Tata Consultancy Services", "INFY.NS": "Infosys",
        "ITC.NS": "ITC Limited", "BHARTIARTL.NS": "Bharti Airtel",
        "ICICIBANK.NS": "ICICI Bank", "SBIN.NS": "State Bank of India",
        "KOTAKBANK.NS": "Kotak Bank", "AXISBANK.NS": "Axis Bank",
        "HCLTECH.NS": "HCL Tech", "WIPRO.NS": "Wipro", "TECHM.NS": "Tech Mahindra",
        "LT.NS": "Larsen & Toubro", "MARUTI.NS": "Maruti Suzuki", "M&M.NS": "Mahindra",
        "ASIANPAINT.NS": "Asian Paints", "HINDUNILVR.NS": "Hindustan Unilever",
        "PETR4.SA": ("Petrobras", "Brazil"), "VALE3.SA": ("Vale S.A.", "Brazil"),
        "ITUB4.SA": ("Itaú Unibanco", "Brazil"), "BBDC4.SA": ("Bradesco", "Brazil"),
        "ABEV3.SA": ("Ambev", "Brazil"), "BBAS3.SA": ("Banco do Brasil", "Brazil"),
        "ELET3.SA": ("Eletrobras", "Brazil"), "SUZB3.SA": ("Suzano", "Brazil"),
        "WEGE3.SA": ("Weg S.A.", "Brazil"), "YPF": ("YPF S.A.", "Argentina"),
        "GGAL": ("Grupo Galicia", "Argentina"), "BMA": ("Banco Macro", "Argentina"),
        "SQM.B": ("SQM", "Chile"), "BSANTANDER.SN": ("Banco Santander Chile", "Chile"),
        "EC": ("Ecopetrol", "Colombia"), "BVC": ("Bancolombia", "Colombia"),
        "NPS.JO": ("Naspers", "South Africa"), "FSR.JO": ("FirstRand", "South Africa"),
        "SBK.JO": ("Standard Bank", "South Africa"), "ABG.JO": ("Absa", "South Africa"),
        "COMI.CA": ("Commercial International Bank", "Egypt"),
        "TEVA": ("Teva Pharma", "Israel"), "CHKP": ("Check Point", "Israel"),
        "WIX": ("Wix.com", "Israel"), "NICE": ("NICE Systems", "Israel")
    }
    for t, v in intl_tickers.items():
        if isinstance(v, tuple):
            name, country = v
        else:
            name = v
            if t.endswith(".LS"): country = "Portugal"
            elif t.endswith(".L"): country = "United Kingdom"
            elif t.endswith(".DE"): country = "Germany"
            elif t.endswith(".PA"): country = "France"
            elif t.endswith(".SW"): country = "Switzerland"
            elif t.endswith(".AS"): country = "Netherlands"
            elif t.endswith(".MI"): country = "Italy"
            elif t.endswith(".MC"): country = "Spain"
            elif t.endswith(".CO"): country = "Denmark"
            elif t.endswith(".ST"): country = "Sweden"
            elif t.endswith(".OL"): country = "Norway"
            elif t.endswith(".HE"): country = "Finland"
            elif t.endswith(".T"): country = "Japan"
            elif t.endswith(".KS"): country = "South Korea"
            elif t.endswith(".HK"): country = "Hong Kong"
            elif t.endswith(".NS"): country = "India"
            elif t.endswith(".SA"): country = "Brazil"
            elif t in ["YPF","GGAL","BMA"]: country = "Argentina"
            elif t in ["SQM.B","BSANTANDER.SN"]: country = "Chile"
            elif t in ["EC","BVC"]: country = "Colombia"
            elif t in ["NPS.JO","FSR.JO","SBK.JO","ABG.JO"]: country = "South Africa"
            elif t == "COMI.CA": country = "Egypt"
            else: country = "Unknown"
        if country in ["United Kingdom","Germany","France","Switzerland","Netherlands","Italy","Spain","Denmark","Sweden","Norway","Finland","Portugal"]:
            region = "Europe"
        elif country in ["Japan","South Korea","Hong Kong","India","China","Taiwan"]:
            region = "Asia"
        elif country in ["Brazil","Argentina","Chile","Colombia"]:
            region = "South America"
        elif country in ["South Africa","Egypt"]:
            region = "Africa"
        elif country in ["Israel"]:
            region = "Middle East"
        else:
            region = "Other"
        universe.append({"Ticker": t, "Name": name, "Region": region, "AssetClass": "Stock"})
    
    # ----- ETFs -----
    etf_list = {
        "SPY": "SPDR S&P 500 ETF", "QQQ": "Invesco QQQ Trust", "IVV": "iShares Core S&P 500",
        "VOO": "Vanguard S&P 500", "VTI": "Vanguard Total Stock Market", "BND": "Vanguard Total Bond Market",
        "GLD": "SPDR Gold Trust", "SLV": "iShares Silver Trust", "TLT": "iShares 20+ Year Treasury Bond",
        "EEM": "iShares MSCI Emerging Markets", "EFA": "iShares MSCI EAFE", "VGK": "Vanguard FTSE Europe",
        "EWJ": "iShares MSCI Japan", "FXI": "iShares China Large-Cap", "ARKK": "ARK Innovation ETF",
        "IBB": "iShares Nasdaq Biotechnology", "XLV": "Health Care Select Sector", "XLF": "Financial Select Sector",
        "XLE": "Energy Select Sector", "XLK": "Technology Select Sector", "XLI": "Industrials Select Sector",
        "XLY": "Consumer Discretionary", "XLP": "Consumer Staples", "XLU": "Utilities",
        "SMH": "VanEck Semiconductor", "TAN": "Invesco Solar", "ICLN": "iShares Global Clean Energy",
        "LIT": "Global X Lithium", "BOTZ": "Global X Robotics", "FINX": "Global X FinTech", "CLOU": "Global X Cloud Computing"
    }
    for t, name in etf_list.items():
        universe.append({"Ticker": t, "Name": name, "Region": "Global", "AssetClass": "ETF"})
    
    # ----- Commodities (futures and ETFs) -----
    commodities_futures = {
        "GC=F": "Gold Futures", "SI=F": "Silver Futures", "CL=F": "Crude Oil Futures",
        "NG=F": "Natural Gas Futures", "HG=F": "Copper Futures", "ZS=F": "Soybean Futures",
        "ZW=F": "Wheat Futures", "ZC=F": "Corn Futures", "KC=F": "Coffee Futures",
        "CT=F": "Cotton Futures", "SB=F": "Sugar Futures", "CC=F": "Cocoa Futures",
        "PA=F": "Palladium Futures", "PL=F": "Platinum Futures", "RB=F": "Gasoline Futures",
        "HO=F": "Heating Oil Futures", "BZ=F": "Brent Crude Futures"
    }
    for t, name in commodities_futures.items():
        universe.append({"Ticker": t, "Name": name, "Region": "Global", "AssetClass": "Commodity"})
    
    commodity_etfs = {
        "DBC": "Invesco DB Commodity Index", "GSG": "iShares S&P GSCI Commodity",
        "USO": "United States Oil", "UNG": "United States Natural Gas",
        "WEAT": "Teucrium Wheat", "CORN": "Teucrium Corn", "SOYB": "Teucrium Soybean",
        "CANE": "Teucrium Sugar", "JO": "iPath Coffee", "BAL": "iPath Cotton"
    }
    for t, name in commodity_etfs.items():
        if t not in etf_list:
            universe.append({"Ticker": t, "Name": name, "Region": "Global", "AssetClass": "Commodity"})
    
    # ----- Cryptocurrencies -----
    crypto_list = {
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "Binance Coin",
        "SOL-USD": "Solana", "XRP-USD": "Ripple", "ADA-USD": "Cardano",
        "DOGE-USD": "Dogecoin", "AVAX-USD": "Avalanche", "SHIB-USD": "Shiba Inu",
        "DOT-USD": "Polkadot", "LINK-USD": "Chainlink", "MATIC-USD": "Polygon",
        "LTC-USD": "Litecoin", "UNI-USD": "Uniswap", "ATOM-USD": "Cosmos"
    }
    for t, name in crypto_list.items():
        universe.append({"Ticker": t, "Name": name, "Region": "Global", "AssetClass": "Crypto"})
    
    df = pd.DataFrame(universe).drop_duplicates(subset="Ticker")
    return df

# ============================================
# 2. FIVE-SOURCE FUNDAMENTAL DATA FETCHER (with YFRateLimitError handling)
# ============================================
def fetch_financial_data(ticker, timeout=6):
    """Try 5 sources in order: xfinlink, Alpha Vantage, FMP, Tiingo, yfinance."""
    # 1. xfinlink
    if XFL_AVAILABLE:
        try:
            df = xfl.metrics(ticker, fields=["roe", "price_to_book", "debt_to_equity", "revenue_growth"])
            if df is not None and len(df) > 0:
                latest = df.iloc[-1]
                roe = latest.get("roe")
                pb = latest.get("price_to_book")
                debt_eq = latest.get("debt_to_equity")
                rev_growth = latest.get("revenue_growth")
                if any(v is not None for v in [roe, pb, debt_eq, rev_growth]):
                    return {"roe": roe, "pb": pb, "debt_to_equity": debt_eq, "revenue_growth": rev_growth}
        except:
            pass
    
    # 2. Alpha Vantage
    if ALPHA_VANTAGE_AVAILABLE and ALPHA_VANTAGE_KEY:
        try:
            fd = FundamentalData(key=ALPHA_VANTAGE_KEY, output_format='pandas')
            overview, _ = fd.get_company_overview(symbol=ticker)
            roe = overview.get('ReturnOnEquityTTM')
            pb = overview.get('PriceToBookRatio')
            debt_eq = overview.get('DebtToEquityRatio')
            rev_growth = overview.get('RevenueGrowth3YrPct')
            if any(v is not None for v in [roe, pb, debt_eq, rev_growth]):
                return {"roe": roe, "pb": pb, "debt_to_equity": debt_eq, "revenue_growth": rev_growth}
        except:
            pass
    
    # 3. Financial Modeling Prep
    if FMP_AVAILABLE and FMP_API_KEY:
        try:
            fmp = FinancialModelingPrep(api_key=FMP_API_KEY)
            rating = fmp.rating(ticker)
            roe = rating.get('roe')
            pb = rating.get('priceToBookRatio')
            debt_eq = rating.get('debtToEquity')
            rev_growth = rating.get('revenueGrowth')
            if any(v is not None for v in [roe, pb, debt_eq, rev_growth]):
                return {"roe": roe, "pb": pb, "debt_to_equity": debt_eq, "revenue_growth": rev_growth}
        except:
            pass
    
    # 4. Tiingo
    if TIINGO_AVAILABLE and TIINGO_API_KEY:
        try:
            client = TiingoClient({'api_key': TIINGO_API_KEY})
            data = client.get_ticker_fundamentals(ticker)
            fundamentals = data.get('fundamentals', {})
            roe = fundamentals.get('roe')
            pb = fundamentals.get('pb')
            debt_eq = fundamentals.get('debtToEquity')
            rev_growth = fundamentals.get('revenueGrowth')
            if any(v is not None for v in [roe, pb, debt_eq, rev_growth]):
                return {"roe": roe, "pb": pb, "debt_to_equity": debt_eq, "revenue_growth": rev_growth}
        except:
            pass
    
    # 5. yfinance (final fallback) – with rate limit handling
    try:
        from yfinance.exceptions import YFRateLimitError
        stock = yf.Ticker(ticker)
        info = stock.info
        roe = info.get("returnOnEquity") or info.get("roe")
        pb = info.get("priceToBook")
        debt_eq = info.get("debtToEquity") or info.get("totalDebtToEquity")
        rev_growth = info.get("revenueGrowth")
        if any(v is not None for v in [roe, pb, debt_eq, rev_growth]):
            return {"roe": roe, "pb": pb, "debt_to_equity": debt_eq, "revenue_growth": rev_growth}
    except YFRateLimitError:
        # Rate limit hit – sleep briefly and return None (do not cache)
        time.sleep(1)
        return None
    except:
        pass
    return None

def buffett_score_from_data(data):
    if not data:
        return {"total": 0, "profitability": 0, "valuation": 0, "debt": 0, "consistency": 0}
    total = 0
    # Profitability (ROE) – max 40
    roe = data.get("roe")
    if roe is not None:
        if roe > 0.15:
            total += 40
            profitability = 40
        elif roe > 0.10:
            total += 20
            profitability = 20
        else:
            profitability = 0
    else:
        profitability = 0
    # Valuation (P/B) – max 30
    pb = data.get("pb")
    if pb is not None:
        if pb < 1.5:
            total += 30
            valuation = 30
        elif pb < 2.0:
            total += 10
            valuation = 10
        else:
            valuation = 0
    else:
        valuation = 0
    # Debt (D/E) – max 20
    debt_eq = data.get("debt_to_equity")
    if debt_eq is not None:
        if debt_eq < 50:
            total += 20
            debt = 20
        elif debt_eq < 100:
            total += 10
            debt = 10
        else:
            debt = 0
    else:
        debt = 0
    # Consistency (Revenue Growth) – max 10
    rev_growth = data.get("revenue_growth")
    if rev_growth is not None:
        if rev_growth > 0.10:
            total += 10
            consistency = 10
        elif rev_growth > 0:
            total += 4
            consistency = 4
        else:
            consistency = 0
    else:
        consistency = 0
    return {
        "total": total,
        "profitability": profitability,
        "valuation": valuation,
        "debt": debt,
        "consistency": consistency,
    }

# ============================================
# 3. PERSISTENT CACHE
# ============================================
CACHE_FILE = "buffett_scores_cache.json"
def load_cached_scores():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}
def save_cached_scores(scores_dict):
    with open(CACHE_FILE, "w") as f:
        json.dump(scores_dict, f)

# ============================================
# 4. BATCHED ANALYSIS WITH PROGRESS BAR (concurrency reduced to 10)
# ============================================
def analyze_all_assets(ticker_df, force_refresh=False):
    cached = load_cached_scores() if not force_refresh else {}
    results = []
    tickers = ticker_df.head(15000)['Ticker'].tolist()
    batch_size = 100
    num_batches = (len(tickers) + batch_size - 1) // batch_size
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    start_time = time.time()
    
    def process_ticker(ticker):
        if not force_refresh and ticker in cached:
            score_data = cached[ticker]
            row = ticker_df[ticker_df['Ticker'] == ticker]
            if not row.empty:
                name = row.iloc[0]["Name"]
                region = row.iloc[0]["Region"]
                asset_class = row.iloc[0]["AssetClass"]
            else:
                name, region, asset_class = ticker, "Unknown", "Unknown"
            return {
                "Ticker": ticker,
                "Company": name,
                "Region": region,
                "AssetClass": asset_class,
                "Buffett Score (0-100)": score_data["total"],
                "Profitability (ROE)": score_data["profitability"],
                "Valuation (P/B)": score_data["valuation"],
                "Debt (D/E)": score_data["debt"],
                "Consistency": score_data["consistency"]
            }
        else:
            data = fetch_financial_data(ticker, timeout=6)
            score_data = buffett_score_from_data(data)
            if score_data["total"] > 0:
                cached[ticker] = score_data
                row = ticker_df[ticker_df['Ticker'] == ticker]
                if not row.empty:
                    name = row.iloc[0]["Name"]
                    region = row.iloc[0]["Region"]
                    asset_class = row.iloc[0]["AssetClass"]
                else:
                    name, region, asset_class = ticker, "Unknown", "Unknown"
                return {
                    "Ticker": ticker,
                    "Company": name,
                    "Region": region,
                    "AssetClass": asset_class,
                    "Buffett Score (0-100)": score_data["total"],
                    "Profitability (ROE)": score_data["profitability"],
                    "Valuation (P/B)": score_data["valuation"],
                    "Debt (D/E)": score_data["debt"],
                    "Consistency": score_data["consistency"]
                }
        return None
    
    for batch_idx in range(num_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, len(tickers))
        batch_tickers = tickers[batch_start:batch_end]
        elapsed = time.time() - start_time
        percent = (batch_idx + 1) / num_batches
        eta = elapsed / (batch_idx + 1) * (num_batches - batch_idx - 1) if batch_idx + 1 > 0 else 0
        status_text.text(
            f"Batch {batch_idx+1}/{num_batches} (assets {batch_start+1}-{batch_end}) | "
            f"Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s | Score candidates found: {len(results)}"
        )
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(process_ticker, ticker): ticker for ticker in batch_tickers}
            for future in as_completed(futures):
                res = future.result()
                if res:
                    results.append(res)
        progress_bar.progress(percent)
        save_cached_scores(cached)
    
    status_text.text(f"Analysis complete in {time.time() - start_time:.1f}s. Found {len(results)} assets with positive scores.")
    time.sleep(1.5)
    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(results)

# ============================================
# 5. NEWS AND SENTIMENT (with last 10 news feed)
# ============================================
@st.cache_data(ttl=7200, show_spinner=False)
def get_all_news(symbol, max_news=50):
    try:
        from gnews import GNews
        google_news = GNews(period="1d", max_results=max_news)
        articles = google_news.get_news(symbol)
        if not articles:
            google_news = GNews(period="1d", max_results=max_news)
            articles = google_news.get_news(f"{symbol} stock")
        news_list = []
        for art in articles[:max_news]:
            news_list.append({
                "title": art.get("title", ""),
                "description": art.get("description", ""),
                "source": art.get("publisher", {}).get("title", ""),
                "date": art.get("published date", ""),
                "url": art.get("url", ""),
            })
        return news_list
    except Exception:
        return []

@st.cache_resource
def load_sentiment_model():
    try:
        return pipeline("sentiment-analysis", model="ProsusAI/finbert")
    except Exception:
        return None

sentiment_pipeline = load_sentiment_model()

def analyze_sentiment(text):
    if not text or sentiment_pipeline is None:
        return "NEUTRAL", 0.5
    try:
        result = sentiment_pipeline(text[:512])[0]
        label = result["label"].upper()
        score = result["score"]
        return label, score
    except Exception:
        return "NEUTRAL", 0.5

def aggregate_sentiment(news_list):
    if not news_list:
        return 0.5, 0, {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    scores = []
    sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    for news in news_list:
        text = f"{news['title']}. {news['description']}"
        label, score = analyze_sentiment(text)
        scores.append(score)
        sentiment_counts[label] += 1
    avg_score = sum(scores) / len(scores)
    return avg_score, len(scores), sentiment_counts

def get_recommendation(daily_change, sentiment_score, news_count):
    if news_count == 0:
        if daily_change > 3:
            return ("💸 PARTIAL SELL", "#ff9800", "No news but strong price rally.")
        elif daily_change < -3:
            return ("💰 BUY THE DIP", "#4caf50", "No news but sharp drop – potential bargain.")
        else:
            return ("⏸️ HOLD", "#9e9e9e", "No news available. Wait.")
    if sentiment_score > 0.65 and daily_change > 0:
        return ("🟢 BUY", "#4caf50", f"Very positive news ({sentiment_score:.0%}) & upward trend.")
    elif sentiment_score > 0.65 and daily_change < -2:
        return ("🔍 ACCUMULATE", "#ff9800", f"Positive news ({sentiment_score:.0%}) but price dip – good entry.")
    elif sentiment_score < 0.35 and daily_change < 0:
        return ("🔴 SELL", "#f44336", f"Negative news ({sentiment_score:.0%}) & falling price.")
    elif sentiment_score < 0.35 and daily_change > 2:
        return ("⚠️ TAKE PROFITS", "#ff9800", f"Price up despite negative news – secure gains.")
    elif daily_change > 5:
        return ("💸 PARTIAL SELL", "#ff9800", "Extreme rally >5% – lock in profits.")
    elif daily_change < -5:
        return ("💰 BUY THE DIP", "#4caf50", "Extreme drop >5% – accumulation opportunity.")
    else:
        return ("⏸️ HOLD", "#9e9e9e", f"Mixed signals (sentiment {sentiment_score:.0%}, change {daily_change:+.1f}%).")

@st.cache_data(ttl=3600)
def get_current_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.history(period="1d")["Close"].iloc[-1]
    except Exception:
        return 0.0

@st.cache_data(ttl=3600)
def get_stock_data(symbol, period="2d", interval="1d"):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)
    return hist

# ============================================
# 6. STREAMLIT UI with Beta Version in top right
# ============================================
def main():
    # Create two columns: one for title, one for version (right aligned)
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🌍 Global Buffett Screener")
    with col2:
        st.markdown(
            "<div style='text-align: right; margin-top: 1rem;'><span style='background-color: #2c3e66; padding: 4px 12px; border-radius: 20px; color: white; font-size: 0.8rem;'>Beta Version 1.4</span></div>",
            unsafe_allow_html=True
        )
    st.caption("Analyzing 15,000+ global assets | Five data sources | Region & asset class filters | Latest 10 news feed")
    
    ticker_df = build_ticker_universe()
    st.sidebar.success(f"Loaded {len(ticker_df)} tickers")
    
    # Sidebar filters
    st.sidebar.subheader("🔍 Filters for Top 50")
    region_filter = st.sidebar.multiselect(
        "Region(s)",
        options=sorted(ticker_df["Region"].unique()),
        default=sorted(ticker_df["Region"].unique())
    )
    asset_filter = st.sidebar.multiselect(
        "Asset Class(es)",
        options=sorted(ticker_df["AssetClass"].unique()),
        default=sorted(ticker_df["AssetClass"].unique())
    )
    
    if st.sidebar.button("Run / Refresh Full Analysis (15k+ assets)"):
        st.session_state["force_refresh"] = True
        st.rerun()
    
    if "global_top50_df" not in st.session_state or st.session_state.get("force_refresh", False):
        with st.spinner("Analyzing global assets (parallel batches, please wait)..."):
            df_scores = analyze_all_assets(ticker_df, force_refresh=st.session_state.get("force_refresh", False))
            if not df_scores.empty:
                st.session_state.global_top50_df = df_scores
                st.session_state.force_refresh = False
            else:
                st.session_state.global_top50_df = pd.DataFrame()
                st.session_state.force_refresh = False
    
    top50 = st.session_state.get("global_top50_df", pd.DataFrame())
    if top50.empty:
        st.info("No scores computed yet. Click 'Run / Refresh Full Analysis (15k+ assets)' to start (may take several minutes).")
        st.stop()
    
    filtered = top50[
        (top50["Region"].isin(region_filter)) &
        (top50["AssetClass"].isin(asset_filter))
    ]
    
    st.subheader("🏆 Top 50 Buffett Scores (0-100)")
    show_top = st.slider("Number of companies to display", 10, 100, 50)
    display_df = filtered.head(show_top)
    
    # Bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=display_df["Ticker"],
            y=display_df["Buffett Score (0-100)"],
            marker=dict(color=display_df["Buffett Score (0-100)"], colorscale="Viridis", showscale=True),
            text=display_df["Buffett Score (0-100)"],
            textposition="outside",
            hovertemplate="Ticker: %{x}<br>Score: %{y}<br>Company: %{customdata}<extra></extra>",
            customdata=display_df["Company"]
        )
    ])
    fig.update_layout(
        title="Top Ranking",
        xaxis_title="Ticker",
        yaxis_title="Buffett Score",
        template="plotly_dark",
        height=600,
        xaxis=dict(tickangle=45),
        margin=dict(b=100)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(display_df, use_container_width=True, height=500)
    
    # Portfolio management
    st.markdown("---")
    st.subheader("📋 Your Portfolio")
    if "portfolio" not in st.session_state:
        if os.path.exists("portfolio_user.json"):
            with open("portfolio_user.json", "r") as f:
                st.session_state.portfolio = json.load(f)
        else:
            st.session_state.portfolio = ["AAPL", "MSFT", "GOOGL"]
    
    new_asset = st.text_input("Add ticker to portfolio")
    if st.button("Add"):
        if new_asset.upper() not in st.session_state.portfolio:
            st.session_state.portfolio.append(new_asset.upper())
            with open("portfolio_user.json", "w") as f:
                json.dump(st.session_state.portfolio, f)
            st.rerun()
    
    for asset in st.session_state.portfolio:
        col1, col2 = st.columns([4, 1])
        col1.write(asset)
        if col2.button("Remove", key=asset):
            st.session_state.portfolio.remove(asset)
            with open("portfolio_user.json", "w") as f:
                json.dump(st.session_state.portfolio, f)
            st.rerun()
    
    # Detailed analysis for selected portfolio asset
    if st.session_state.portfolio:
        selected = st.selectbox("Select asset for detailed analysis", st.session_state.portfolio)
        if selected:
            with st.spinner(f"Loading data for {selected}..."):
                current_price = get_current_price(selected)
                hist = get_stock_data(selected, period="2d", interval="1d")
                if not hist.empty and len(hist) >= 2:
                    prev_close = hist["Close"].iloc[-2]
                    daily_change = (current_price - prev_close) / prev_close * 100
                else:
                    daily_change = 0.0
                news_list = get_all_news(selected, max_news=50)
                sentiment_score, news_count, sentiment_counts = aggregate_sentiment(news_list)
                col1, col2, col3 = st.columns(3)
                col1.metric("Current Price", f"${current_price:.2f}", delta=f"{daily_change:+.2f}%")
                row = top50[top50["Ticker"] == selected]
                if not row.empty:
                    buffett = row.iloc[0]["Buffett Score (0-100)"]
                    col2.metric("Buffett Score", f"{buffett}/100")
                else:
                    data = fetch_financial_data(selected, timeout=6)
                    score_data = buffett_score_from_data(data)
                    col2.metric("Buffett Score", f"{score_data['total']}/100")
                col3.metric("Total News (last day)", news_count)
                
                st.markdown("---")
                st.subheader("📰 Last 10 News Feed")
                if news_list:
                    for i, news in enumerate(news_list[:10]):
                        st.markdown(f"**{i+1}. {news['title']}**")
                        st.caption(f"Source: {news['source']} | {news['date']}")
                        st.markdown(f"[Read more]({news['url']})")
                        st.markdown("---")
                else:
                    st.info("No recent news found.")
                
                st.subheader("📊 News Sentiment Analysis")
                if news_count > 0:
                    col_left, col_right = st.columns([0.6, 0.4])
                    with col_left:
                        labels, values, colors = [], [], []
                        if sentiment_counts["POSITIVE"] > 0:
                            labels.append("Positive"); values.append(sentiment_counts["POSITIVE"]); colors.append("#4caf50")
                        if sentiment_counts["NEGATIVE"] > 0:
                            labels.append("Negative"); values.append(sentiment_counts["NEGATIVE"]); colors.append("#f44336")
                        if sentiment_counts["NEUTRAL"] > 0:
                            labels.append("Neutral"); values.append(sentiment_counts["NEUTRAL"]); colors.append("#ffc107")
                        fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, marker=dict(colors=colors), hole=0.4)])
                        fig_pie.update_layout(template="plotly_dark", height=350)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    with col_right:
                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=sentiment_score * 100,
                            title={"text": "Overall Sentiment (%)"},
                            gauge={
                                "axis": {"range": [0, 100]},
                                "bar": {"color": "#4caf50"},
                                "steps": [
                                    {"range": [0, 30], "color": "#f44336"},
                                    {"range": [30, 70], "color": "#ffc107"},
                                    {"range": [70, 100], "color": "#4caf50"}
                                ]
                            }
                        ))
                        fig_gauge.update_layout(template="plotly_dark", height=300)
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        st.markdown(f"🟢 Positive: {sentiment_counts['POSITIVE']} ({sentiment_counts['POSITIVE']/news_count:.0%})")
                        st.markdown(f"🔴 Negative: {sentiment_counts['NEGATIVE']} ({sentiment_counts['NEGATIVE']/news_count:.0%})")
                        st.markdown(f"⚪ Neutral: {sentiment_counts['NEUTRAL']} ({sentiment_counts['NEUTRAL']/news_count:.0%})")
                else:
                    st.info("No recent news found.")
                
                rec_text, rec_color, rec_just = get_recommendation(daily_change, sentiment_score, news_count)
                st.markdown(f"""
                <div class="rec-box">
                    <h2 style="color:{rec_color}; margin:0;">{rec_text}</h2>
                    <p style="color:#ccd6f0;">{rec_just}</p>
                    <small>Based on {news_count} news articles and daily change {daily_change:+.2f}%</small>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("Data sources: xfinlink, Alpha Vantage, Financial Modeling Prep, Tiingo, yfinance | News: Google RSS | Sentiment: FinBERT")

if __name__ == "__main__":
    main()