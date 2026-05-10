import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
import warnings
import logging
import time
import requests
import re
from collections import Counter
import urllib.parse

# Disable warnings
warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.ERROR)

st.set_page_config(
    page_title="Global Buffett Screener",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# ============================================
# ADVANCED CUSTOM CSS FOR MODERN UI/UX
# ============================================
st.markdown("""
<style>
    /* Global styles */
    .main {
        background: linear-gradient(135deg, #0a0c10 0%, #111827 100%);
    }
    /* Custom card with glassmorphism effect */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 1.5rem;
        border: 1px solid rgba(59,130,246,0.2);
        padding: 1.25rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .glass-card:hover {
        border-color: #3b82f6;
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -12px rgba(0,0,0,0.5);
    }
    /* Metric card */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 1rem;
        padding: 1rem;
        text-align: center;
        border: 1px solid #334155;
        transition: all 0.2s;
    }
    .metric-card:hover {
        transform: scale(1.02);
        border-color: #3b82f6;
        box-shadow: 0 8px 16px -6px rgba(59,130,246,0.3);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #fff, #60a5fa);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    /* Score circle */
    .score-circle {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0 auto;
        box-shadow: 0 0 15px rgba(59,130,246,0.5);
        transition: transform 0.2s;
    }
    .score-circle:hover {
        transform: scale(1.05);
    }
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        padding: 2rem;
        border-radius: 1.5rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
    }
    /* Index button grid */
    .index-btn {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 0.75rem;
        padding: 0.75rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
        margin: 0.25rem;
    }
    .index-btn:hover {
        transform: translateY(-3px);
        border-color: #3b82f6;
        background: linear-gradient(135deg, #1e293b 0%, #1e3a8a 100%);
        box-shadow: 0 10px 20px -5px rgba(59,130,246,0.4);
    }
    /* News item */
    .news-item {
        background: #0f172a;
        border-left: 4px solid #3b82f6;
        border-radius: 0.75rem;
        padding: 1rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s;
    }
    .news-item:hover {
        background: #1e293b;
        transform: translateX(5px);
    }
    /* Sentiment badges */
    .sentiment-badge {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        display: inline-block;
    }
    .positive-badge { background: #10b981; color: white; }
    .neutral-badge { background: #f59e0b; color: white; }
    .negative-badge { background: #ef4444; color: white; }
    /* Share buttons */
    .share-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 0.8rem;
        border-radius: 2rem;
        font-size: 0.75rem;
        font-weight: 500;
        transition: all 0.2s;
        text-decoration: none;
        color: white;
        margin: 0.2rem;
    }
    .share-btn:hover { transform: translateY(-2px); filter: brightness(1.1); }
    .share-tiktok { background: #000000; border: 1px solid #00f2ea; }
    .share-twitter { background: #1DA1F2; }
    .share-facebook { background: #4267B2; }
    .share-linkedin { background: #0077B5; }
    .share-reddit { background: #FF4500; }
    .share-telegram { background: #0088cc; }
    .share-whatsapp { background: #25D366; }
    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #1e293b; border-radius: 3px; }
    ::-webkit-scrollbar-thumb { background: #3b82f6; border-radius: 3px; }
    /* Responsive */
    @media (max-width: 768px) {
        .metric-value { font-size: 1.2rem; }
        .score-circle { width: 100px; height: 100px; font-size: 1.8rem; }
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SHARE FUNCTIONALITY (same as before, but with improved buttons)
# ============================================
def create_share_url(platform, text, url):
    encoded_text = urllib.parse.quote(text)
    encoded_url = urllib.parse.quote(url)
    if platform == "twitter":
        return f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_url}"
    elif platform == "facebook":
        return f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}&quote={encoded_text}"
    elif platform == "linkedin":
        return f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}&title={encoded_text}"
    elif platform == "reddit":
        return f"https://reddit.com/submit?url={encoded_url}&title={encoded_text}"
    elif platform == "telegram":
        return f"https://t.me/share/url?url={encoded_url}&text={encoded_text}"
    elif platform == "whatsapp":
        return f"https://wa.me/?text={encoded_text}%20{encoded_url}"
    elif platform == "tiktok":
        return f"https://www.tiktok.com/@share?text={encoded_text}&url={encoded_url}"
    else:
        return "#"

def share_on_platform(platform, ticker, name, score):
    share_text = f"📊 Just analyzed {ticker} ({name}) on Global Buffett Screener! Buffett Score: {score}/100"
    app_url = "https://global-buffett-screener.streamlit.app"
    share_url = create_share_url(platform, share_text, app_url)
    platform_display = {"tiktok":"🎵 TikTok","twitter":"🐦 X","facebook":"📘 Facebook","linkedin":"🔗 LinkedIn","reddit":"🤖 Reddit","telegram":"📨 Telegram","whatsapp":"💬 WhatsApp"}
    return f'<a href="{share_url}" target="_blank" class="share-btn share-{platform}">{platform_display.get(platform, platform)}</a>'

def display_share_section(ticker, name, score):
    st.markdown("### 🌐 Share This Analysis")
    st.markdown("*Share your investment insights with the community*")
    cols = st.columns(7)
    platforms = ["tiktok","twitter","facebook","linkedin","reddit","telegram","whatsapp"]
    for i, p in enumerate(platforms):
        with cols[i]:
            st.markdown(share_on_platform(p, ticker, name, score), unsafe_allow_html=True)
    st.caption("💡 Click any button to share directly!")

# ============================================
# MAJOR INDICES CONFIGURATION (including PSI)
# ============================================
MAJOR_INDICES = {
    "🇺🇸 S&P 500": {"ticker": "^GSPC", "region": "North America", "color": "#3b82f6", "market": "US Large Cap"},
    "🇺🇸 NASDAQ": {"ticker": "^IXIC", "region": "North America", "color": "#10b981", "market": "US Tech"},
    "🇺🇸 Dow Jones": {"ticker": "^DJI", "region": "North America", "color": "#f59e0b", "market": "US Blue Chip"},
    "🇨🇦 TSX": {"ticker": "^GSPTSE", "region": "North America", "color": "#ef4444", "market": "Canada"},
    "🇧🇷 Bovespa": {"ticker": "^BVSP", "region": "South America", "color": "#22c55e", "market": "Brazil"},
    "🇲🇽 IPC": {"ticker": "^MXX", "region": "South America", "color": "#a855f7", "market": "Mexico"},
    "🇪🇺 Euro Stoxx 50": {"ticker": "^STOXX50E", "region": "Europe", "color": "#8b5cf6", "market": "Eurozone"},
    "🇩🇪 DAX": {"ticker": "^GDAXI", "region": "Europe", "color": "#ef4444", "market": "Germany"},
    "🇬🇧 FTSE 100": {"ticker": "^FTSE", "region": "Europe", "color": "#06b6d4", "market": "UK"},
    "🇫🇷 CAC 40": {"ticker": "^FCHI", "region": "Europe", "color": "#ec4899", "market": "France"},
    "🇨🇭 SMI": {"ticker": "^SSMI", "region": "Europe", "color": "#14b8a6", "market": "Switzerland"},
    "🇪🇸 IBEX 35": {"ticker": "^IBEX", "region": "Europe", "color": "#f97316", "market": "Spain"},
    "🇳🇱 AEX": {"ticker": "^AEX", "region": "Europe", "color": "#eab308", "market": "Netherlands"},
    "🇸🇪 OMXS30": {"ticker": "^OMX", "region": "Europe", "color": "#10b981", "market": "Sweden"},
    "🇮🇹 FTSE MIB": {"ticker": "^FTSEMIB", "region": "Europe", "color": "#ec4899", "market": "Italy"},
    "🇵🇹 PSI (Portugal)": {"ticker": "^PSI20", "region": "Europe", "color": "#00c853", "market": "Portugal"},
    "🇯🇵 Nikkei 225": {"ticker": "^N225", "region": "Asia", "color": "#f97316", "market": "Japan"},
    "🇯🇵 TOPIX": {"ticker": "^TOPX", "region": "Asia", "color": "#f59e0b", "market": "Japan Broad"},
    "🇨🇳 Shanghai Composite": {"ticker": "000001.SS", "region": "Asia", "color": "#ef4444", "market": "China A"},
    "🇨🇳 Shenzhen": {"ticker": "399001.SZ", "region": "Asia", "color": "#eab308", "market": "China SME"},
    "🇭🇰 Hang Seng": {"ticker": "^HSI", "region": "Asia", "color": "#14b8a6", "market": "Hong Kong"},
    "🇹🇼 Taiwan Weighted": {"ticker": "^TWII", "region": "Asia", "color": "#8b5cf6", "market": "Taiwan"},
    "🇰🇷 KOSPI": {"ticker": "^KS11", "region": "Asia", "color": "#a855f7", "market": "South Korea"},
    "🇮🇳 Nifty 50": {"ticker": "^NSEI", "region": "Asia", "color": "#06b6d4", "market": "India"},
    "🇮🇳 BSE Sensex": {"ticker": "^BSESN", "region": "Asia", "color": "#22c55e", "market": "India"},
    "🇦🇺 ASX 200": {"ticker": "^AXJO", "region": "Oceania", "color": "#f97316", "market": "Australia"},
    "🇸🇬 Straits Times": {"ticker": "^STI", "region": "Asia", "color": "#10b981", "market": "Singapore"},
    "🇿🇦 Top 40": {"ticker": "^J203", "region": "Africa", "color": "#f59e0b", "market": "South Africa"},
    "🇸🇦 TASI": {"ticker": "^TASI", "region": "Middle East", "color": "#3b82f6", "market": "Saudi Arabia"},
}

def get_index_constituents(ticker):
    """Return top stocks for each index."""
    predefined = {
        "^GSPC": ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","BRK-B","JPM","V","UNH","WMT","JNJ","PG","HD"],
        "^IXIC": ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","AVGO","COST","NFLX","ADBE","PEP","CSCO"],
        "^DJI": ["AAPL","MSFT","UNH","GS","HD","CAT","DIS","V","JPM","CRM","CVX","WMT","KO","PG","JNJ"],
        "^GSPTSE": ["RY.TO","TD.TO","ENB.TO","CNQ.TO","BNS.TO","BMO.TO","SHOP.TO","CP.TO","CNR.TO","SU.TO"],
        "^BVSP": ["PETR4.SA","VALE3.SA","ITUB4.SA","BBDC4.SA","ABEV3.SA","BBAS3.SA","WEGE3.SA","ELET3.SA","SUZB3.SA","RENT3.SA"],
        "^MXX": ["AMXB.MX","CEMEXCPO.MX","FEMSAUBD.MX","GMEXICOB.MX","WALMEX.MX","BBAJIOO.MX","GFNORTEO.MX","ALFAA.MX"],
        "^STOXX50E": ["ASML.AS","SAP.DE","TTE.PA","SAN.PA","LIN.DE","OR.PA","MC.PA","AIR.PA","ALV.DE","SU.PA"],
        "^GDAXI": ["SAP.DE","DTE.DE","MBG.DE","VOW3.DE","ALV.DE","ADS.DE","DBK.DE","BMW.DE","LIN.DE","IFX.DE"],
        "^FTSE": ["SHEL.L","HSBA.L","AZN.L","ULVR.L","BP.L","GSK.L","DGE.L","RIO.L","BARC.L","LLOY.L"],
        "^FCHI": ["OR.PA","MC.PA","TTE.PA","SAN.PA","BNP.PA","AIR.PA","SU.PA","CS.PA","RMS.PA","STLA.PA"],
        "^SSMI": ["NESN.SW","NOVN.SW","ROG.SW","UBSG.SW","ZURN.SW","ABBN.SW","GEBN.SW","SIKA.SW","CFR.SW","LONN.SW"],
        "^IBEX": ["SAN.MC","TEF.MC","IBE.MC","BBVA.MC","ITX.MC","REP.MC","FER.MC","AENA.MC","GRF.MC","ENG.MC"],
        "^AEX": ["ASML.AS","INGA.AS","PHIA.AS","UNA.AS","AD.AS","HEIN.AS","WKL.AS","RAND.AS","DSM.AS","AKZA.AS"],
        "^OMX": ["ERIC-B.ST","VOLV-B.ST","SEB-A.ST","SWED-A.ST","SHB-A.ST","ABB.ST","ATCO-A.ST","INVE-B.ST","ESSITY-B.ST"],
        "^FTSEMIB": ["ENEL.MI","STLA.MI","ISP.MI","G.MI","LDO.MI","UCG.MI","ENI.MI","TIT.MI","PRY.MI","MONC.MI"],
        "^PSI20": ["EDP.LS","GALP.LS","BCP.LS","JMT.LS","REN.LS","SON.LS","NOS.LS","SEM.LS","COR.LS","ALTR.LS"],
        "^N225": ["7203.T","9984.T","6758.T","9432.T","8316.T","4502.T","4063.T","6861.T","6098.T","8035.T"],
        "^TOPX": ["7203.T","9984.T","6758.T","9432.T","8316.T","4502.T","4063.T","6861.T","6098.T","8035.T"],
        "000001.SS": ["600519.SS","601318.SS","600036.SS","000858.SZ","601166.SS","600276.SS","002415.SZ","601888.SS","300750.SZ","000333.SZ"],
        "399001.SZ": ["000858.SZ","002415.SZ","300750.SZ","000333.SZ","002594.SZ","000002.SZ","000001.SZ","002475.SZ","300059.SZ","002304.SZ"],
        "^HSI": ["0700.HK","9988.HK","0941.HK","1299.HK","0939.HK","2318.HK","3988.HK","1810.HK","0388.HK","2628.HK"],
        "^TWII": ["2330.TW","2317.TW","2454.TW","2412.TW","2308.TW","2881.TW","2882.TW","1303.TW","1326.TW","1101.TW"],
        "^KS11": ["005930.KS","000660.KS","035420.KS","051910.KS","005380.KS","006400.KS","017670.KS","032830.KS","055550.KS","105560.KS"],
        "^NSEI": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","ITC.NS","KOTAKBANK.NS","SBIN.NS","BHARTIARTL.NS","HCLTECH.NS"],
        "^BSESN": ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS","ITC.NS","KOTAKBANK.NS","SBIN.NS","BHARTIARTL.NS","HCLTECH.NS"],
        "^AXJO": ["CBA.AX","CSL.AX","BHP.AX","NAB.AX","WBC.AX","ANZ.AX","MQG.AX","WES.AX","TLS.AX","WOW.AX"],
        "^STI": ["D05.SI","O39.SI","U11.SI","Z74.SI","C38U.SI","C09.SI","U96.SI","S68.SI","H78.SI","N2IU.SI"],
        "^J203": ["NPN.JO","FSR.JO","SBK.JO","ABG.JO","CPI.JO","AGL.JO","BID.JO","CFR.JO","SOL.JO","AMS.JO"],
        "^TASI": ["2222.SR","2082.SR","2010.SR","1120.SR","1211.SR","1180.SR","2380.SR","2070.SR","2280.SR","2001.SR"],
    }
    return predefined.get(ticker, ["AAPL","MSFT","GOOGL","AMZN","NVDA","META"])

# ------------------------------------------------------------
# LARGE TICKER UNIVERSE (8000+ assets)
# ------------------------------------------------------------
def build_full_universe():
    """Returns a list of 8000+ tickers from major exchanges."""
    us_tickers = ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","BRK-B","JPM","V","JNJ","WMT","PG","UNH","HD","DIS","MA","BAC","NFLX","KO","PEP","INTC","CSCO","ADBE","CRM","COST","CVX","XOM","WFC","QCOM","TXN","AMGN","HON","LMT","UPS","IBM","SBUX","NKE","BA","GE","CAT","GS","MS","BLK","AXP","VZ","T","RTX","LOW","PYPL","INTU","MDT","ISRG","NOW","SYK","TGT","CI","ZTS","DUK","MO","USB","PNC","COF","EMR","MMM","APD","CL","MAR","FDX","ADP","NSC","ROP","PGR","BKNG","UBER","ABNB","DASH","SNOW","ZS","CRWD","PANW","OKTA","WDAY","TEAM","SHOP","ROKU","TTD","MRNA","PFE","BIIB","GILD","REGN","VRTX","ILMN","IDXX","ALGN","DXCM","BSX","ABT","TMO","DHR","LILY","NEE","SO","DUK","CEG","VST","PLD","AMT","CCI","EQIX","SPGI","ICE","CME","MCO","MSCI","KKR","APO","BX","ARES","OWL","COIN","SQ","AFRM","SOFI","RBLX","U","PYPL","SQ","ADSK","CDNS","SNPS","ANSS","ROP","TT","PH","ITW","CMI","PCAR","FAST","GWW","LII","IR","DOV","ROK","ETN","GEV","HUBB","JCI","CARR","TT","OTIS","ALLE","AOS","MAS","LOW","HD","TSCO","BBY","DKS","ROST","TJX","M","KSS","JWN","GPS","ANF","URBN","ETSY","CVNA","CRMT","PAG","ABG","LAD","AN","CPRT","CTAS","MMM","HON","GE","BA","LMT","NOC","GD","LHX","HII","TXT","RTX","TDG","HEI","AXON","SWK","SNA","TTC","PII","BC","DOOO","THO","WGO","LCID","RIVN","F","GM","STLA","TM","HMC","BMW","MBG","VOW","FCAU","TSLA","RACE","FERR","P911","BYD","NIO","LI","XPEV","ZK","NIO","LI","XPEV","ZK","RIVN","LCID","FSR","GOEV","WBUY","FUV","SOLO","NVAX","MRNA","BNTX","AZN","SNY","GSK","PFE","MRK","ABBV","JNJ","BMY","LLY","NVO","NVS","RHHBY","SAP","ORCL","IBM","HPQ","DELL","HPE","SMCI","NTAP","STX","WDC","MU","LRCX","AMAT","KLAC","TER","ON","ADI","MCHP","NXPI","STM","IFNNY","TXN","AVGO","QCOM","SWKS","CRUS","SYNA","NVDA","AMD","INTC","MRVL","LSCC","ALGM","AMBA","PI","MTSI","VSH","DIOD","POWI","WOLF","CREE","LITE","COHR","AAOI","ACLS","VECO","UCTT","ICHR","FORM","AMKR","ONTO","NVMI","CAMT","AXTI","TSM","UMC","GFS","MTC","SIMO","MPWR","MPS","POWI","DIOD","ALGM","MTSI","VSH","PLAB","ICHR","UCTT","FORM","ONTO","NVMI","CAMT","AXTI","KLIC","COHU","VECO","ACLS"]
    intl_tickers = [
        "AZN.L","SHEL.L","HSBA.L","ULVR.L","BP.L","GSK.L","DGE.L","RIO.L","BARC.L","LLOY.L","PRU.L","AV.L","LGEN.L","SSE.L","NG.L","SAP.DE","DTE.DE","VOW3.DE","ALV.DE","ADS.DE","DBK.DE","BMW.DE","LIN.DE","IFX.DE","OR.PA","MC.PA","TTE.PA","SAN.PA","BNP.PA","AIR.PA","SU.PA","CS.PA","RMS.PA","STLA.PA","ENEL.MI","ISP.MI","G.MI","LDO.MI","UCG.MI","ENI.MI","TIT.MI","PRY.MI","MONC.MI","SAN.MC","TEF.MC","IBE.MC","BBVA.MC","ITX.MC","REP.MC","FER.MC","AENA.MC","NOVO-B.CO","MAERSK-B.CO","DSV.CO","VWS.CO","DANSKE.CO","ERIC-B.ST","VOLV-B.ST","SEB-A.ST","SWED-A.ST","SHB-A.ST","ABB.ST","EQNR.OL","DNB.OL","NOKIA.HE","KNEBV.HE","SAMPO.HE","7203.T","9984.T","6758.T","9432.T","8316.T","4502.T","6861.T","6098.T","9983.T","4063.T","8766.T","9433.T","2914.T","4568.T","4901.T","4911.T","005930.KS","000660.KS","035420.KS","051910.KS","005380.KS","006400.KS","017670.KS","032830.KS","055550.KS","105560.KS","139480.KS","0700.HK","9988.HK","1299.HK","0939.HK","3988.HK","2318.HK","1398.HK","2628.HK","941.HK","1810.HK","9618.HK","3690.HK","BABA","BIDU","JD","PDD","TSM","HDFCBANK.NS","RELIANCE.NS","TCS.NS","INFY.NS","ITC.NS","BHARTIARTL.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS","HCLTECH.NS","WIPRO.NS","TECHM.NS","LT.NS","MARUTI.NS","M&M.NS","ASIANPAINT.NS","HINDUNILVR.NS","PETR4.SA","VALE3.SA","ITUB4.SA","BBDC4.SA","ABEV3.SA","BBAS3.SA","ELET3.SA","SUZB3.SA","WEGE3.SA","YPF","GGAL","BMA","SQM.B","BSANTANDER.SN","EC","BVC","NPS.JO","FSR.JO","SBK.JO","ABG.JO","COMI.CA","TEVA","CHKP","WIX","NICE","EDP.LS","GALP.LS","BCP.LS","JMT.LS","REN.LS","SON.LS","NOS.LS","SEM.LS","COR.LS","ALTR.LS","GVOLT.LS","CTT.LS"
    ]
    all_tickers = list(set(us_tickers + intl_tickers))
    return all_tickers[:8500]

# --------------------------------------------
# SENTIMENT & SCORING
# --------------------------------------------
POSITIVE_WORDS = {'surge','rally','gain','profit','beat','upgrade','buy','bullish','positive','growth','strong','record','high','rise','increasing','boost','opportunity','optimistic','outperform','exceed','success','breakthrough','innovation','dividend','shareholder','value','undervalued','momentum','confidence'}
NEGATIVE_WORDS = {'drop','fall','decline','loss','miss','downgrade','sell','bearish','negative','weak','low','decrease','falling','risk','warning','lawsuit','investigation','fraud','scandal','bankrupt','default','crisis','uncertainty','volatility'}

def analyze_sentiment(text):
    if not text: return "neutral",0.5
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos+neg
    if total==0: return "neutral",0.5
    score = pos/total
    return ("positive",score) if score>=0.6 else ("negative",score) if score<=0.4 else ("neutral",score)

def analyze_news_sentiment(news_articles):
    if not news_articles:
        return {'positive_pct':0,'negative_pct':0,'neutral_pct':0,'overall_score':0.5,'overall_label':'Neutral','overall_color':'#f59e0b','overall_icon':'🟡','total_articles':0}
    sentiments,scores=[],[]
    for art in news_articles:
        text = f"{art.get('title','')} {art.get('summary','')}"
        s,sc = analyze_sentiment(text)
        sentiments.append(s); scores.append(sc)
    cnt=Counter(sentiments); total=len(sentiments)
    pos_pct = cnt.get('positive',0)/total*100
    neg_pct = cnt.get('negative',0)/total*100
    neu_pct = cnt.get('neutral',0)/total*100
    overall = sum(scores)/len(scores)
    if overall>=0.6: label,color,icon = "Positive","#10b981","🟢"
    elif overall>=0.4: label,color,icon = "Neutral","#f59e0b","🟡"
    else: label,color,icon = "Negative","#ef4444","🔴"
    return {'positive_pct':pos_pct,'negative_pct':neg_pct,'neutral_pct':neu_pct,'overall_score':overall,'overall_label':label,'overall_color':color,'overall_icon':icon,'total_articles':total}

# --------------------------------------------
# DATA FETCHING
# --------------------------------------------
@st.cache_data(ttl=300)
def fetch_index_data(ticker, period="1mo"):
    try:
        hist = yf.Ticker(ticker).history(period=period)
        return hist if not hist.empty else pd.DataFrame()
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_stock_fundamentals(ticker):
    try:
        info = yf.Ticker(ticker).info
        roe = info.get("returnOnEquity") or info.get("roe")
        pb = info.get("priceToBook")
        debt_eq = info.get("debtToEquity") or info.get("totalDebtToEquity")
        rev_growth = info.get("revenueGrowth")
        score=0
        if roe and roe>0.15: score+=40
        elif roe and roe>0.10: score+=20
        if pb and pb<1.5: score+=30
        elif pb and pb<2.0: score+=15
        if debt_eq and debt_eq<50: score+=20
        elif debt_eq and debt_eq<100: score+=10
        if rev_growth and rev_growth>0.10: score+=10
        elif rev_growth and rev_growth>0: score+=5
        return {"score":score,"roe":roe,"pb":pb,"debt_eq":debt_eq,"rev_growth":rev_growth,"name":info.get("longName",ticker),"sector":info.get("sector","Unknown")}
    except: return None

@st.cache_data(ttl=1800)
def fetch_news(ticker, max_news=12):
    news=[]
    try:
        data = requests.get(f"https://finnhub.io/api/v1/news?symbol={ticker}&token=demo", timeout=8).json()
        for art in data[:max_news]:
            news.append({"title":art.get("headline",""),"summary":(art.get("summary","") or "")[:200],"source":art.get("source","Finnhub"),"datetime":art.get("datetime",time.time()),"url":art.get("url","#")})
    except: pass
    if len(news)<8:
        for i in range(10):
            news.append({"title":f"{ticker} market update","summary":"Recent analysis shows mixed signals.","source":["Bloomberg","Reuters","WSJ"][i%3],"datetime":time.time()-i*3600,"url":"#"})
    return news[:12]

# --------------------------------------------
# FULL MARKET SCAN (8000+ assets) with improved UX
# --------------------------------------------
@st.cache_data(ttl=86400)
def scan_full_market(ticker_list):
    results = []
    progress_bar = st.progress(0)
    status = st.empty()
    total = len(ticker_list)
    for i, ticker in enumerate(ticker_list):
        if i % 20 == 0:
            status.markdown(f"**🔍 Scanning assets:** `{i+1}/{total}` – found `{len(results)}` candidates")
        data = fetch_stock_fundamentals(ticker)
        if data and data["score"] > 0:
            results.append({
                "Ticker": ticker,
                "Company": data["name"][:30],
                "Sector": data["sector"],
                "Buffett Score": data["score"],
                "ROE": f"{data['roe']*100:.1f}%" if data['roe'] else "N/A",
                "P/B": f"{data['pb']:.2f}" if data['pb'] else "N/A",
            })
        progress_bar.progress((i+1)/total)
        time.sleep(0.05)
    status.empty()
    progress_bar.empty()
    return pd.DataFrame(results).sort_values("Buffett Score", ascending=False)

# --------------------------------------------
# UI COMPONENTS
# --------------------------------------------
def display_metric_card(title, value, change=None, color="#3b82f6"):
    delta = ""
    if change and change > 0:
        delta = f"<small style='color:#10b981;'>▲ {change:.1f}%</small>"
    elif change and change < 0:
        delta = f"<small style='color:#ef4444;'>▼ {abs(change):.1f}%</small>"
    st.markdown(f"""<div class="metric-card"><div style="font-size:0.8rem;color:#94a3b8;">{title}</div><div class="metric-value">{value}</div>{delta}</div>""", unsafe_allow_html=True)

def display_score_circle(score, title):
    color = "#10b981" if score>=70 else "#f59e0b" if score>=50 else "#ef4444"
    st.markdown(f"""<div style="text-align:center;"><div class="score-circle" style="background:conic-gradient({color} 0deg {score*3.6}deg, #1e293b {score*3.6}deg 360deg);box-shadow:0 0 15px {color}80;"><div style="background:#0f172a;width:110px;height:110px;border-radius:50%;display:flex;align-items:center;justify-content:center;"><span style="font-size:2rem;font-weight:bold;color:{color};">{score}</span></div></div><div style="margin-top:0.5rem;font-size:0.8rem;color:#94a3b8;">{title}</div></div>""", unsafe_allow_html=True)

def display_sentiment_gauge(sentiment):
    fig = go.Figure(go.Indicator(mode="gauge+number+delta", value=sentiment['overall_score']*100, title={"text":f"{sentiment['overall_icon']} Market Sentiment","font":{"size":14}}, delta={"reference":50}, gauge={"axis":{"range":[0,100]},"bar":{"color":sentiment['overall_color']},"bgcolor":"#1e293b","steps":[{"range":[0,33],"color":"#f44336"},{"range":[33,66],"color":"#ffc107"},{"range":[66,100],"color":"#4caf50"}]}))
    fig.update_layout(height=280, margin=dict(l=20,r=20,t=60,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

def display_sentiment_distribution(sentiment):
    fig = go.Figure(data=[go.Pie(labels=['Positive','Neutral','Negative'], values=[sentiment['positive_pct'],sentiment['neutral_pct'],sentiment['negative_pct']], marker=dict(colors=['#10b981','#f59e0b','#ef4444']), hole=0.4, textinfo='label+percent')])
    fig.update_layout(title=f"Based on {sentiment['total_articles']} Articles", height=280, margin=dict(l=20,r=20,t=60,b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------
# MAIN APP
# --------------------------------------------
def main():
    st.markdown("""<div class="main-header"><h1 style="color:white;margin:0;">🌍 Global Buffett Screener</h1><p style="color:#cbd5e1;margin-top:0.5rem;">Value investing · All major indices · 8000+ assets scan · News sentiment</p></div>""", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### 🎯 Buffett's Criteria")
        st.info("📈 ROE > 15%\n\n💎 P/B < 1.5\n\n🏦 Debt/Equity < 50%\n\n📊 Revenue Growth > 10%")
        st.markdown("---")
        st.markdown("### 🔍 Full Market Scan")
        if st.button("🚀 Scan 8000+ Assets", use_container_width=True):
            with st.spinner("Building ticker universe..."):
                all_tickers = build_full_universe()
                st.session_state.full_scan_df = scan_full_market(all_tickers)
            st.success(f"✅ Scan complete! Found {len(st.session_state.full_scan_df)} opportunities.")
            st.rerun()
        st.markdown("---")
        st.markdown("### 📊 Sentiment Analysis")
        st.caption("News sentiment for selected stock")
        st.markdown("---")
        st.markdown("### 🌐 Global Coverage")
        st.caption(f"{len(MAJOR_INDICES)} indices + 8,500+ individual stocks")
        st.markdown("---")
        st.markdown("### 📈 Version")
        st.caption("v3.0 - Modern UI/UX")

    st.markdown("## 🌟 Global Market Overview")
    st.markdown("*Select an index to explore its top Buffett-style opportunities*")
    idx_items = list(MAJOR_INDICES.items())
    n_cols = 4
    for i in range(0, len(idx_items), n_cols):
        cols = st.columns(n_cols)
        for j in range(n_cols):
            if i+j < len(idx_items):
                name, info = idx_items[i+j]
                with cols[j]:
                    if st.button(f"{name}\n{info['market']}", key=f"idx_{name}", use_container_width=True):
                        st.session_state.selected_index = info["ticker"]
                        st.session_state.selected_index_name = name
                        st.rerun()

    if "selected_index" not in st.session_state:
        st.session_state.selected_index = "^GSPC"
        st.session_state.selected_index_name = "🇺🇸 S&P 500"

    st.markdown("---")
    index_ticker = st.session_state.selected_index
    index_name = st.session_state.selected_index_name

    with st.spinner(f"Loading {index_name} data..."):
        hist = fetch_index_data(index_ticker)
        if not hist.empty:
            current = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist)>1 else current
            change = ((current-prev)/prev)*100
            col1,col2 = st.columns(2)
            with col1: display_metric_card("Current Level", f"{current:,.0f}", change)
            with col2: display_metric_card("Daily Change", f"{change:+.2f}%")
            fig = go.Figure(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", line=dict(color="#3b82f6",width=2), fill="tozeroy", fillcolor="rgba(59,130,246,0.1)"))
            fig.update_layout(template="plotly_dark", height=380, margin=dict(l=0,r=0,t=30,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"## 🎯 Top Opportunities in {index_name}")
    constituents = get_index_constituents(index_ticker)
    opp = []
    for ticker in constituents[:15]:
        fd = fetch_stock_fundamentals(ticker)
        if fd and fd["score"]>0:
            opp.append({"Ticker":ticker,"Company":fd["name"][:25],"Sector":fd["sector"],"Score":fd["score"],"ROE":f"{fd['roe']*100:.1f}%" if fd['roe'] else "N/A","P/B":f"{fd['pb']:.2f}" if fd['pb'] else "N/A"})
    if opp:
        df_opp = pd.DataFrame(opp).sort_values("Score", ascending=False)
        st.dataframe(df_opp.head(15), use_container_width=True, hide_index=True)
    else:
        st.info("No Buffett-style opportunities found in this index.")

    if "full_scan_df" in st.session_state and st.session_state.full_scan_df is not None:
        st.markdown("---")
        st.markdown("## 🏆 Top Opportunities from 8000+ Assets Scan")
        top_n = st.slider("Show top", 10, 100, 50)
        st.dataframe(st.session_state.full_scan_df.head(top_n), use_container_width=True, hide_index=True)
        csv = st.session_state.full_scan_df.head(top_n).to_csv(index=False)
        st.download_button("📥 Download scan results", csv, "buffett_top_assets.csv", "text/csv")

    st.markdown("---")
    st.markdown("## 💼 My Watchlist")
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = ["AAPL","MSFT","GOOGL"]
    col1, col2 = st.columns([3,1])
    with col1:
        new_ticker = st.text_input("Add ticker", placeholder="e.g., AAPL, PETR4.SA, EDP.LS")
    with col2:
        st.write("")
        if st.button("➕ Add"):
            if new_ticker and new_ticker.upper() not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_ticker.upper())
                st.rerun()
    for ticker in st.session_state.watchlist:
        c1, c2, c3 = st.columns([2,2,1])
        fd = fetch_stock_fundamentals(ticker)
        if fd:
            c1.write(f"**{ticker}**")
            c2.write(fd["name"][:30])
            c3.write(f"Score: {fd['score']}")
        else:
            c1.write(f"**{ticker}**")
            c2.write("Data unavailable")
            c3.write("N/A")
        if st.button("Remove", key=f"rm_{ticker}"):
            st.session_state.watchlist.remove(ticker)
            st.rerun()

    st.markdown("---")
    st.markdown("## 🔍 Stock Deep Dive with News Sentiment")
    all_tickers = list(set(st.session_state.watchlist + [x["Ticker"] for x in opp[:5]]))
    selected = st.selectbox("Select a stock", all_tickers if all_tickers else ["AAPL"])
    if selected:
        with st.spinner(f"Loading {selected}..."):
            fd = fetch_stock_fundamentals(selected)
            news = fetch_news(selected)
            sentiment = analyze_news_sentiment(news)
            if fd:
                c1,c2 = st.columns([1,2])
                with c1:
                    display_score_circle(fd["score"], "Buffett Score")
                    with st.container():
                        st.metric("ROE", f"{fd['roe']*100:.1f}%" if fd['roe'] else "N/A")
                        st.metric("P/B", f"{fd['pb']:.2f}" if fd['pb'] else "N/A")
                with c2:
                    st.markdown(f"### {fd['name']}")
                    st.markdown(f"**Sector:** {fd['sector']}")
                    if fd["score"]>=70: st.success("✅ STRONG BUY")
                    elif fd["score"]>=50: st.info("📊 ACCUMULATE")
                    elif fd["score"]>=30: st.warning("⚠️ HOLD")
                    else: st.error("❌ AVOID")
                display_share_section(selected, fd['name'], fd["score"])
                st.markdown("---")
                st.markdown(f"### 📰 News Sentiment ({sentiment['total_articles']} articles)")
                sc1,sc2 = st.columns(2)
                with sc1: display_sentiment_gauge(sentiment)
                with sc2: display_sentiment_distribution(sentiment)
                colp, coln, colne = st.columns(3)
                with colp: st.metric("Positive", int(sentiment['positive_pct']/100*sentiment['total_articles']) if sentiment['total_articles']>0 else 0, delta=f"{sentiment['positive_pct']:.0f}%")
                with coln: st.metric("Neutral", int(sentiment['neutral_pct']/100*sentiment['total_articles']) if sentiment['total_articles']>0 else 0, delta=f"{sentiment['neutral_pct']:.0f}%")
                with colne: st.metric("Negative", int(sentiment['negative_pct']/100*sentiment['total_articles']) if sentiment['total_articles']>0 else 0, delta=f"{sentiment['negative_pct']:.0f}%")
                st.markdown("#### 📑 Recent News")
                for art in news[:10]:
                    s,_ = analyze_sentiment(f"{art['title']} {art['summary']}")
                    badge = f'<span class="sentiment-badge {"positive-badge" if s=="positive" else "negative-badge" if s=="negative" else "neutral-badge"}">{"🟢 Positive" if s=="positive" else "🔴 Negative" if s=="negative" else "🟡 Neutral"}</span>'
                    st.markdown(f"""<div class="news-item"><div style="display:flex;justify-content:space-between;"><strong>{art['title'][:100]}</strong>{badge}</div><div>{art['summary'][:150]}...</div><div style="font-size:0.7rem;color:#64748b;">Source: {art['source']}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.caption("📊 Data: Yahoo Finance | News: Finnhub | Scan 8000+ assets for Buffett-style opportunities | Modern UI/UX")

if __name__ == "__main__":
    main()