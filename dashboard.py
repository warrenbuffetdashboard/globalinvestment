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

warnings.filterwarnings("ignore")
logging.getLogger("streamlit").setLevel(logging.ERROR)

st.set_page_config(page_title="Global Investment Dashboard", layout="wide", page_icon="📊")

# ============================================
# GLOBAL TICKER DATABASE (with region & country)
# Includes North America, South America, Europe, Asia
# ============================================
@st.cache_data(ttl=86400)
def get_global_tickers():
    tickers = {
        # North America - USA
        "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com Inc.", "TSLA": "Tesla Inc.", "META": "Meta Platforms",
        "NVDA": "NVIDIA Corp.", "BRK-B": "Berkshire Hathaway", "JPM": "JPMorgan Chase",
        "V": "Visa Inc.", "JNJ": "Johnson & Johnson", "WMT": "Walmart Inc.",
        "PG": "Procter & Gamble", "UNH": "UnitedHealth", "HD": "Home Depot",
        "DIS": "Walt Disney", "MA": "Mastercard", "BAC": "Bank of America",
        "NFLX": "Netflix", "KO": "Coca-Cola", "PEP": "PepsiCo", "INTC": "Intel",
        "CSCO": "Cisco Systems", "ADBE": "Adobe", "CRM": "Salesforce", "COST": "Costco",
        "CVX": "Chevron", "XOM": "Exxon Mobil", "WFC": "Wells Fargo", "QCOM": "Qualcomm",
        "TXN": "Texas Instruments", "AMGN": "Amgen", "HON": "Honeywell",
        "LMT": "Lockheed Martin", "UPS": "UPS", "IBM": "IBM", "SBUX": "Starbucks",
        "NKE": "Nike", "BA": "Boeing", "GE": "General Electric", "CAT": "Caterpillar",
        "GS": "Goldman Sachs", "MS": "Morgan Stanley", "BLK": "BlackRock",
        "AXP": "American Express", "VZ": "Verizon", "T": "AT&T", "RTX": "Raytheon",
        "LOW": "Lowe's", "PYPL": "PayPal", "INTU": "Intuit", "MDT": "Medtronic",
        "ISRG": "Intuitive Surgical", "NOW": "ServiceNow", "SYK": "Stryker",
        "TGT": "Target", "CI": "Cigna", "ZTS": "Zoetis", "DUK": "Duke Energy",
        "MO": "Altria", "USB": "U.S. Bancorp", "PNC": "PNC Financial",
        "COF": "Capital One", "EMR": "Emerson Electric", "MMM": "3M",
        "APD": "Air Products", "CL": "Colgate-Palmolive", "MAR": "Marriott",
        "FDX": "FedEx", "ADP": "ADP", "NSC": "Norfolk Southern", "ROP": "Roper Tech",
        "PGR": "Progressive", "BKNG": "Booking Holdings", "UBER": "Uber",
        "ABNB": "Airbnb", "DASH": "DoorDash", "SNOW": "Snowflake", "ZS": "Zscaler",
        "CRWD": "CrowdStrike", "PANW": "Palo Alto Networks", "OKTA": "Okta",
        "WDAY": "Workday", "TEAM": "Atlassian", "SHOP": "Shopify", "ROKU": "Roku",
        "TTD": "Trade Desk", "MRNA": "Moderna", "PFE": "Pfizer", "BIIB": "Biogen",
        "GILD": "Gilead Sciences", "REGN": "Regeneron", "VRTX": "Vertex",
        "ILMN": "Illumina", "IDXX": "Idexx", "ALGN": "Align Tech", "DXCM": "Dexcom",
        "BSX": "Boston Scientific",
        # North America - Canada
        "RY.TO": "Royal Bank of Canada", "TD.TO": "Toronto-Dominion Bank",
        "SHOP.TO": "Shopify Inc.", "ENB.TO": "Enbridge Inc.", "CNQ.TO": "Canadian Natural Resources",
        "BNS.TO": "Bank of Nova Scotia", "BMO.TO": "Bank of Montreal", "CM.TO": "Canadian Imperial Bank",
        "SU.TO": "Suncor Energy", "CSU.TO": "Constellation Software",
        # South America - Brazil (B3)
        "PETR4.SA": "Petrobras", "VALE3.SA": "Vale S.A.", "ITUB4.SA": "Itaú Unibanco",
        "BBDC4.SA": "Bradesco", "ABEV3.SA": "Ambev", "BBAS3.SA": "Banco do Brasil",
        "ELET3.SA": "Eletrobras", "SUZB3.SA": "Suzano", "RENT3.SA": "Localiza",
        "WEGE3.SA": "Weg S.A.", "RAIL3.SA": "Rumo Logística", "BRFS3.SA": "BRF S.A.",
        "GGBR4.SA": "Gerdau", "CSAN3.SA": "Cosan", "EGIE3.SA": "Engie Brasil",
        "SBSP3.SA": "Sabesp", "VIVT3.SA": "Vivo", "HYPE3.SA": "Hypermarcas",
        "LREN3.SA": "Lojas Renner", "MGLU3.SA": "Magazine Luiza", "PCAR3.SA": "Pão de Açúcar",
        "NTCO3.SA": "Natura", "USIM5.SA": "Usiminas", "CMIG4.SA": "Cemig",
        # South America - Argentina
        "YPF": "YPF S.A.", "GGAL": "Grupo Galicia", "BMA": "Banco Macro",
        "PAM": "Pampa Energía", "TGS": "Transportadora de Gas del Sur",
        # South America - Chile
        "BSANTANDER.SN": "Banco Santander Chile", "ENELAM.SN": "Enel Americas",
        "SQM.B": "SQM", "CMPC.SN": "CMPC", "CHILE.SN": "Banco de Chile",
        # South America - Colombia
        "EC": "Ecopetrol", "BVC": "Bancolombia", "CEMARGOS.CN": "Cementos Argos",
        # Europe - Portugal (PSI)
        "EDP.LS": "EDP - Energias de Portugal", "GALP.LS": "Galp Energia",
        "BCP.LS": "Banco Comercial Português", "JMT.LS": "Jerónimo Martins",
        "REN.LS": "REN - Redes Energéticas Nacionais", "SON.LS": "Sonae",
        "NOS.LS": "NOS", "SEM.LS": "Semapa", "COR.LS": "Corticeira Amorim",
        "ALTR.LS": "Altri", "MCP.LS": "Motociclo", "IBS.LS": "Ibersol",
        "GVOLT.LS": "Greenvolt", "CTT.LS": "CTT Correios de Portugal",
        # Europe - United Kingdom
        "AZN.L": "AstraZeneca", "SHEL.L": "Shell", "ULVR.L": "Unilever",
        "HSBA.L": "HSBC", "RYAAY": "Ryanair", "GSK.L": "GSK", "BP.L": "BP",
        "DGE.L": "Diageo", "REL.L": "RELX", "LSEG.L": "London Stock Exchange",
        # Europe - Germany
        "SAP.DE": "SAP SE", "DTE.DE": "Deutsche Telekom", "VOW3.DE": "Volkswagen",
        "BAS.DE": "BASF", "BAYN.DE": "Bayer", "ADS.DE": "Adidas", "DBK.DE": "Deutsche Bank",
        "MBG.DE": "Mercedes-Benz", "BMW.DE": "BMW", "ALV.DE": "Allianz",
        # Europe - France
        "BNP.PA": "BNP Paribas", "AIR.PA": "Airbus", "SAN.PA": "Sanofi",
        "OR.PA": "L'Oréal", "MC.PA": "LVMH", "SU.PA": "Schneider Electric",
        "TTE.PA": "TotalEnergies", "CS.PA": "AXA", "RNO.PA": "Renault",
        # Europe - Switzerland
        "NESN.SW": "Nestlé", "NOVO-B.CO": "Novo Nordisk", "ROG.SW": "Roche",
        "NOVN.SW": "Novartis", "UBSG.SW": "UBS", "ZURN.SW": "Zurich Insurance",
        # Europe - Netherlands
        "ASML.AS": "ASML Holding", "INGA.AS": "ING Groep", "PHIA.AS": "Philips",
        "RDSA.AS": "Shell (NL)", "UNA.AS": "Unilever NL",
        # Europe - Italy
        "ENEL.MI": "Enel", "STLA.MI": "Stellantis", "ISP.MI": "Intesa Sanpaolo",
        "G.MI": "Generali", "LDO.MI": "Leonardo", "UCG.MI": "UniCredit",
        # Europe - Spain
        "SAN.MC": "Banco Santander", "TEF.MC": "Telefónica", "IBE.MC": "Iberdrola",
        "REP.MC": "Repsol", "BBVA.MC": "BBVA", "ITX.MC": "Inditex",
        # Europe - Denmark
        "NOVO-B.CO": "Novo Nordisk", "MAERSK-B.CO": "Maersk", "DSV.CO": "DSV",
        # Europe - Sweden
        "ERIC-B.ST": "Ericsson", "VOLV-B.ST": "Volvo", "SEB-A.ST": "SEB",
        # Asia - Japan
        "7203.T": "Toyota Motor", "9984.T": "SoftBank Group", "6758.T": "Sony Group",
        "9432.T": "Nippon Telegraph & Telephone", "8306.T": "Mitsubishi UFJ Financial",
        "8058.T": "Mitsubishi Corporation", "4502.T": "Takeda Pharmaceutical",
        "6861.T": "Keyence", "7974.T": "Nintendo", "8316.T": "Sumitomo Mitsui",
        # Asia - South Korea
        "005930.KS": "Samsung Electronics", "000660.KS": "SK Hynix",
        "035420.KS": "NAVER Corporation", "051910.KS": "LG Chem",
        "005380.KS": "Hyundai Motor", "068270.KS": "Celltrion",
        # Asia - China (Hong Kong listed)
        "0700.HK": "Tencent Holdings", "9988.HK": "Alibaba Group",
        "1299.HK": "AIA Group", "0939.HK": "China Construction Bank",
        "3988.HK": "Bank of China", "2318.HK": "Ping An Insurance",
        # Asia - India
        "HDFCBANK.NS": "HDFC Bank", "RELIANCE.NS": "Reliance Industries",
        "TCS.NS": "Tata Consultancy Services", "INFY.NS": "Infosys",
        "ITC.NS": "ITC Limited", "BHARTIARTL.NS": "Bharti Airtel",
        "ICICIBANK.NS": "ICICI Bank", "SBIN.NS": "State Bank of India",
        # Asia - Taiwan
        "TSM": "Taiwan Semiconductor", "2330.TW": "TSMC (local)", "2454.TW": "MediaTek",
        # Asia - Australia
        "CBA.AX": "Commonwealth Bank", "BHP.AX": "BHP Group", "CSL.AX": "CSL Limited",
        "WBC.AX": "Westpac", "NAB.AX": "National Australia Bank",
        # ETFs
        "SPY": "SPDR S&P 500 ETF", "QQQ": "Invesco QQQ Trust", "IVV": "iShares Core S&P 500",
        "VOO": "Vanguard S&P 500", "VTI": "Vanguard Total Stock Market",
        "BND": "Vanguard Total Bond Market", "GLD": "SPDR Gold Trust",
        "SLV": "iShares Silver Trust", "TLT": "iShares 20+ Year Treasury Bond",
        "EEM": "iShares MSCI Emerging Markets", "EFA": "iShares MSCI EAFE",
        "VGK": "Vanguard FTSE Europe", "EWJ": "iShares MSCI Japan",
        "FXI": "iShares China Large-Cap", "FLI": "iShares MSCI Portugal",
        # Cryptocurrencies
        "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "BNB-USD": "Binance Coin",
        "SOL-USD": "Solana", "XRP-USD": "Ripple", "ADA-USD": "Cardano",
        "DOGE-USD": "Dogecoin", "AVAX-USD": "Avalanche", "SHIB-USD": "Shiba Inu",
        "DOT-USD": "Polkadot", "LINK-USD": "Chainlink", "MATIC-USD": "Polygon",
        "LTC-USD": "Litecoin", "UNI-USD": "Uniswap", "ATOM-USD": "Cosmos",
    }
    # Assign region and country based on suffix and known mappings
    df = pd.DataFrame(list(tickers.items()), columns=["Ticker", "Name"])
    
    def get_region_and_country(ticker):
        # North America
        if ticker.endswith(".TO") or ticker in ["RY.TO","TD.TO","SHOP.TO","ENB.TO","CNQ.TO","BNS.TO","BMO.TO","CM.TO","SU.TO","CSU.TO"]:
            return "North America", "Canada"
        if ticker in ["AAPL","MSFT","GOOGL","AMZN","TSLA","META","NVDA","BRK-B","JPM","V","JNJ",
                      "WMT","PG","UNH","HD","DIS","MA","BAC","NFLX","KO","PEP","INTC","CSCO",
                      "ADBE","CRM","COST","CVX","XOM","WFC","QCOM","TXN","AMGN","HON","LMT",
                      "UPS","IBM","SBUX","NKE","BA","GE","CAT","GS","MS","BLK","AXP","VZ","T",
                      "RTX","LOW","PYPL","INTU","MDT","ISRG","NOW","SYK","TGT","CI","ZTS","DUK",
                      "MO","USB","PNC","COF","EMR","MMM","APD","CL","MAR","FDX","ADP","NSC","ROP",
                      "PGR","BKNG","UBER","ABNB","DASH","SNOW","ZS","CRWD","PANW","OKTA","WDAY",
                      "TEAM","SHOP","ROKU","TTD","MRNA","PFE","BIIB","GILD","REGN","VRTX","ILMN",
                      "IDXX","ALGN","DXCM","BSX"]:
            return "North America", "USA"
        # South America - Brazil
        if ticker.endswith(".SA") or ticker in ["PETR4.SA","VALE3.SA","ITUB4.SA","BBDC4.SA","ABEV3.SA",
                                                "BBAS3.SA","ELET3.SA","SUZB3.SA","RENT3.SA","WEGE3.SA",
                                                "RAIL3.SA","BRFS3.SA","GGBR4.SA","CSAN3.SA","EGIE3.SA",
                                                "SBSP3.SA","VIVT3.SA","HYPE3.SA","LREN3.SA","MGLU3.SA",
                                                "PCAR3.SA","NTCO3.SA","USIM5.SA","CMIG4.SA"]:
            return "South America", "Brazil"
        # South America - Argentina
        if ticker in ["YPF","GGAL","BMA","PAM","TGS"]:
            return "South America", "Argentina"
        # South America - Chile
        if ticker.endswith(".SN") or ticker in ["SQM.B","CMPC.SN","CHILE.SN"]:
            return "South America", "Chile"
        # South America - Colombia
        if ticker in ["EC","BVC","CEMARGOS.CN"]:
            return "South America", "Colombia"
        # Europe - Portugal
        if ticker.endswith(".LS"):
            return "Europe", "Portugal"
        # Europe - UK
        if ticker.endswith(".L") or ticker in ["AZN.L","SHEL.L","ULVR.L","HSBA.L","RYAAY","GSK.L","BP.L","DGE.L","REL.L","LSEG.L"]:
            return "Europe", "United Kingdom"
        # Europe - Germany
        if ticker.endswith(".DE") or ticker in ["SAP.DE","DTE.DE","VOW3.DE","BAS.DE","BAYN.DE","ADS.DE","DBK.DE","MBG.DE","BMW.DE","ALV.DE"]:
            return "Europe", "Germany"
        # Europe - France
        if ticker.endswith(".PA") or ticker in ["BNP.PA","AIR.PA","SAN.PA","OR.PA","MC.PA","SU.PA","TTE.PA","CS.PA","RNO.PA"]:
            return "Europe", "France"
        # Europe - Switzerland
        if ticker.endswith(".SW") or ticker in ["NESN.SW","ROG.SW","NOVN.SW","UBSG.SW","ZURN.SW"]:
            return "Europe", "Switzerland"
        # Europe - Netherlands
        if ticker.endswith(".AS") or ticker in ["ASML.AS","INGA.AS","PHIA.AS","RDSA.AS","UNA.AS"]:
            return "Europe", "Netherlands"
        # Europe - Italy
        if ticker.endswith(".MI") or ticker in ["ENEL.MI","STLA.MI","ISP.MI","G.MI","LDO.MI","UCG.MI"]:
            return "Europe", "Italy"
        # Europe - Spain
        if ticker.endswith(".MC") or ticker in ["SAN.MC","TEF.MC","IBE.MC","REP.MC","BBVA.MC","ITX.MC"]:
            return "Europe", "Spain"
        # Europe - Denmark
        if ticker.endswith(".CO") or ticker in ["NOVO-B.CO","MAERSK-B.CO","DSV.CO"]:
            return "Europe", "Denmark"
        # Europe - Sweden
        if ticker.endswith(".ST"):
            return "Europe", "Sweden"
        # Asia - Japan
        if ticker.endswith(".T"):
            return "Asia", "Japan"
        # Asia - South Korea
        if ticker.endswith(".KS"):
            return "Asia", "South Korea"
        # Asia - Hong Kong
        if ticker.endswith(".HK"):
            return "Asia", "Hong Kong"
        # Asia - India
        if ticker.endswith(".NS") or ticker in ["HDFCBANK.NS","RELIANCE.NS","TCS.NS","INFY.NS","ITC.NS","BHARTIARTL.NS","ICICIBANK.NS","SBIN.NS"]:
            return "Asia", "India"
        # Asia - Taiwan
        if ticker in ["TSM","2330.TW","2454.TW"]:
            return "Asia", "Taiwan"
        # Asia - Australia
        if ticker.endswith(".AX"):
            return "Asia", "Australia"
        # Asia - China (US listed)
        if ticker in ["BABA","BIDU","JD"]:
            return "Asia", "China"
        # ETFs
        if ticker in ["SPY","QQQ","IVV","VOO","VTI","BND","GLD","SLV","TLT","EEM","EFA","VGK","EWJ","FXI","FLI"]:
            return "ETFs", "ETFs"
        # Cryptocurrencies
        if "-USD" in ticker:
            return "Crypto", "Crypto"
        # Fallback
        return "Other", "Unknown"
    
    df[["Region", "Country"]] = df["Ticker"].apply(lambda x: pd.Series(get_region_and_country(x)))
    # Filter out "Other" for clarity
    df = df[df["Region"] != "Other"]
    return df

@st.cache_data(ttl=3600)
def get_financials(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "roe": info.get("returnOnEquity", None) or info.get("roe", None),
            "pb": info.get("priceToBook", None),
            "debt_to_equity": info.get("debtToEquity", None) or info.get("totalDebtToEquity", None),
            "revenue_growth": info.get("revenueGrowth", None),
        }
    except Exception:
        return None

def buffett_score(ticker):
    data = get_financials(ticker)
    if not data:
        return {"total": 0, "profitability": 0, "valuation": 0, "debt": 0, "consistency": 0}
    total = 0
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

@st.cache_data(ttl=3600)
def get_stock_data(symbol, period="2d", interval="1d"):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=period, interval=interval)
    return hist

@st.cache_data(ttl=3600, show_spinner=False)
def get_current_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.history(period="1d")["Close"].iloc[-1]
    except Exception:
        return 0.0

@st.cache_data(ttl=7200, show_spinner=False)
def get_all_news(symbol, max_news=20):
    try:
        from gnews import GNews
        google_news = GNews(period="1d", max_results=max_news)
        articles = google_news.get_news(symbol)
        if not articles:
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

# ============================================
# SESSION STATE AND GLOBAL TOP 50 (with region/country)
# ============================================
if "portfolio" not in st.session_state:
    if os.path.exists("portfolio_user.json"):
        with open("portfolio_user.json", "r") as f:
            st.session_state.portfolio = json.load(f)
    else:
        st.session_state.portfolio = ["AAPL", "MSFT", "GOOGL", "NVDA", "EDP.LS", "7203.T", "PETR4.SA"]

ticker_df = get_global_tickers()

if "global_top50_df" not in st.session_state:
    with st.spinner("Analyzing global markets (may take ~40 seconds)..."):
        tickers_to_score = ticker_df.head(600)['Ticker'].tolist()
        results = []
        for ticker in tickers_to_score:
            score_data = buffett_score(ticker)
            if score_data["total"] > 0:
                name_row = ticker_df[ticker_df['Ticker'] == ticker]['Name']
                name = name_row.values[0] if not name_row.empty else ticker
                region = ticker_df[ticker_df['Ticker'] == ticker]['Region'].values[0]
                country = ticker_df[ticker_df['Ticker'] == ticker]['Country'].values[0]
                results.append({
                    "Ticker": ticker,
                    "Company": name,
                    "Region": region,
                    "Country": country,
                    "Buffett Score (0-100)": score_data["total"],
                    "Profitability (ROE)": score_data["profitability"],
                    "Valuation (P/B)": score_data["valuation"],
                    "Debt (D/E)": score_data["debt"],
                    "Consistency": score_data["consistency"]
                })
        df_scores = pd.DataFrame(results)
        if not df_scores.empty:
            df_scores = df_scores.sort_values("Buffett Score (0-100)", ascending=False)
            st.session_state.global_top50_df = df_scores.head(50)
        else:
            st.session_state.global_top50_df = pd.DataFrame()

# ============================================
# MODERN DARK CSS
# ============================================
st.markdown("""
<style>
    .stApp { background: #0b0f1c; }
    .css-1d391kg { background: #0a0f1a; border-right: 1px solid #2a2e3d; }
    .stMetric { background: #1a1f2e; border-radius: 20px; padding: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    h1, h2, h3 { color: #eef2ff; font-weight: 600; }
    .rec-box {
        background: linear-gradient(145deg, #1a1f2e, #131725);
        border-radius: 32px;
        padding: 1.8rem;
        text-align: center;
        margin: 1.2rem 0;
        border: 1px solid #2d3348;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
    }
    .stButton>button { background: #2c3e66; border-radius: 40px; width: 100%; }
    .dataframe { background-color: #1a1f2e; border-radius: 16px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR – SEARCH AND PORTFOLIO
# ============================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/warren-buffett--v2.png", width=80)
    st.title("Buffett Hub")
    st.markdown("---")
    st.subheader("🔍 Add Asset")
    search_term = st.text_input("Company name or ticker:")
    if search_term:
        filtered = ticker_df[ticker_df["Name"].str.contains(search_term, case=False) | 
                             ticker_df["Ticker"].str.contains(search_term.upper(), case=False)]
        filtered = filtered.head(20)
        if not filtered.empty:
            selected_ticker = st.selectbox("Select:", filtered["Ticker"].tolist(),
                                           format_func=lambda x: f"{x} – {filtered[filtered['Ticker']==x]['Name'].values[0]}")
            if st.button("➕ Add to Portfolio"):
                if selected_ticker not in st.session_state.portfolio:
                    st.session_state.portfolio.append(selected_ticker)
                    with open("portfolio_user.json", "w") as f:
                        json.dump(st.session_state.portfolio, f)
                    st.success(f"Added {selected_ticker}")
                    st.rerun()
                else:
                    st.warning("Already in portfolio")
    st.markdown("---")
    st.subheader("📋 My Portfolio")
    with st.container(height=300):
        for asset in st.session_state.portfolio.copy():
            col1, col2 = st.columns([4, 1])
            col1.write(f"🔹 {asset}")
            if col2.button("✖", key=f"del_{asset}"):
                st.session_state.portfolio.remove(asset)
                with open("portfolio_user.json", "w") as f:
                    json.dump(st.session_state.portfolio, f)
                st.rerun()
    st.markdown("---")
    st.caption("Data: Yahoo Finance | News: Google RSS | AI: FinBERT")

# ============================================
# MAIN CONTENT – GLOBAL TOP 50 + BY REGION / COUNTRY
# ============================================
st.title("🌍 Global Investment Dashboard")
st.caption(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

top50 = st.session_state.global_top50_df
if top50.empty:
    st.warning("Could not compute global top scores. Please try again later.")
else:
    st.subheader("🏆 Top 50 Companies – Buffett Score (0-100)")
    # Vertical bar chart for global top 50
    fig = go.Figure(data=[
        go.Bar(
            x=top50["Ticker"],
            y=top50["Buffett Score (0-100)"],
            marker=dict(color=top50["Buffett Score (0-100)"], colorscale="Viridis", showscale=True),
            text=top50["Buffett Score (0-100)"],
            textposition="outside",
            hovertemplate="Ticker: %{x}<br>Score: %{y}<br>Company: %{customdata}<extra></extra>",
            customdata=top50["Company"]
        )
    ])
    fig.update_layout(
        title="Global Top 50 Ranking",
        xaxis_title="Ticker",
        yaxis_title="Buffett Score",
        template="plotly_dark",
        height=800,
        xaxis=dict(tickangle=90, tickfont=dict(size=8)),
        plot_bgcolor="#131826",
        paper_bgcolor="#0b0f1c",
        font=dict(color="#eef2ff"),
        margin=dict(b=150)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Filter options: by Region or by Country
    st.subheader("📊 Filter by Region / Country")
    filter_type = st.radio("View by:", ["Region", "Country"], horizontal=True)
    
    if filter_type == "Region":
        # Define region order for readability
        region_order = ["North America", "South America", "Europe", "Asia", "ETFs", "Crypto"]
        available_regions = sorted([r for r in top50["Region"].unique() if r in region_order] + [r for r in top50["Region"].unique() if r not in region_order])
        regions = ["All"] + available_regions
        selected_region = st.selectbox("Select Region:", regions)
        if selected_region == "All":
            display_df = top50
        else:
            display_df = top50[top50["Region"] == selected_region]
        st.subheader(f"📋 {selected_region} Companies (Sorted by Buffett Score)")
        st.dataframe(display_df, use_container_width=True, height=600)
    else:  # Country
        countries = ["All"] + sorted(top50["Country"].unique())
        selected_country = st.selectbox("Select Country:", countries)
        if selected_country == "All":
            display_df = top50
        else:
            display_df = top50[top50["Country"] == selected_country]
        st.subheader(f"📋 {selected_country} Companies (Sorted by Buffett Score)")
        st.dataframe(display_df, use_container_width=True, height=600)

# ============================================
# USER PORTFOLIO SCORES
# ============================================
st.markdown("---")
with st.spinner("Analyzing your portfolio..."):
    portfolio_scores = []
    for sym in st.session_state.portfolio:
        score_data = buffett_score(sym)
        price = get_current_price(sym)
        region_row = ticker_df[ticker_df['Ticker'] == sym]['Region']
        country_row = ticker_df[ticker_df['Ticker'] == sym]['Country']
        region = region_row.values[0] if not region_row.empty else "Unknown"
        country = country_row.values[0] if not country_row.empty else "Unknown"
        portfolio_scores.append({
            "Ticker": sym,
            "Region": region,
            "Country": country,
            "Buffett Score (0-100)": score_data["total"],
            "Profitability (ROE)": score_data["profitability"],
            "Valuation (P/B)": score_data["valuation"],
            "Debt (D/E)": score_data["debt"],
            "Consistency": score_data["consistency"],
            "Current Price": f"${price:.2f}" if price > 0 else "N/A",
        })
    df_portfolio = pd.DataFrame(portfolio_scores)
    df_portfolio = df_portfolio.sort_values("Buffett Score (0-100)", ascending=False)
    st.subheader("📊 Your Portfolio Buffett Scores (Ranked)")
    def color_scores(val):
        if val >= 70: return "background-color: #2e7d32; color: white"
        elif val >= 40: return "background-color: #f9a825; color: black"
        elif val >= 10: return "background-color: #f57c00; color: white"
        else: return "background-color: #c62828; color: white"
    styled_portfolio = df_portfolio.style.map(color_scores, subset=["Profitability (ROE)", "Valuation (P/B)", "Debt (D/E)", "Consistency"])
    st.dataframe(styled_portfolio, use_container_width=True, height=400)

# ============================================
# DETAILED ANALYSIS (WITHOUT NEWS LIST)
# ============================================
st.markdown("---")
st.subheader("📈 Detailed Asset Analysis")
selected_asset = st.selectbox("Select an asset from your portfolio:", st.session_state.portfolio)

with st.spinner(f"Loading data for {selected_asset}..."):
    try:
        current_price = get_current_price(selected_asset)
        hist = get_stock_data(selected_asset, period="2d", interval="1d")
        if not hist.empty and len(hist) >= 2:
            prev_close = hist["Close"].iloc[-2]
            daily_change = (current_price - prev_close) / prev_close * 100
        else:
            daily_change = 0.0
        
        news_list = get_all_news(selected_asset, max_news=20)
        sentiment_score, news_count, sentiment_counts = aggregate_sentiment(news_list)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"${current_price:.2f}", delta=f"{daily_change:+.2f}%")
        
        asset_score_row = top50[top50["Ticker"] == selected_asset] if not top50.empty else None
        if asset_score_row is not None and not asset_score_row.empty:
            buffett = asset_score_row.iloc[0]["Buffett Score (0-100)"]
            col2.metric("Buffett Score", f"{buffett}/100")
        else:
            score_data = buffett_score(selected_asset)
            col2.metric("Buffett Score", f"{score_data['total']}/100")
        
        col3.metric("Total News (last day)", news_count)
        
        st.markdown("---")
        st.subheader("📰 News Sentiment Analysis")
        
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
        
        st.caption("ℹ️ Detailed news list has been removed. Only aggregated sentiment is shown.")
        
    except Exception as e:
        st.error(f"Error: {str(e)}")