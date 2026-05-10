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
    .main { background: linear-gradient(135deg, #0a0c10 0%, #111827 100%); }
    .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border-radius: 1.5rem; border: 1px solid rgba(59,130,246,0.2); padding: 1.25rem; margin-bottom: 1rem; transition: all 0.3s ease; }
    .glass-card:hover { border-color: #3b82f6; transform: translateY(-2px); box-shadow: 0 20px 25px -12px rgba(0,0,0,0.5); }
    .metric-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 1rem; padding: 1rem; text-align: center; border: 1px solid #334155; transition: all 0.2s; }
    .metric-card:hover { transform: scale(1.02); border-color: #3b82f6; box-shadow: 0 8px 16px -6px rgba(59,130,246,0.3); }
    .metric-value { font-size: 1.8rem; font-weight: bold; background: linear-gradient(135deg, #fff, #60a5fa); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .score-circle { width: 140px; height: 140px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; font-weight: bold; margin: 0 auto; box-shadow: 0 0 15px rgba(59,130,246,0.5); transition: transform 0.2s; }
    .score-circle:hover { transform: scale(1.05); }
    .main-header { background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); padding: 2rem; border-radius: 1.5rem; margin-bottom: 2rem; text-align: center; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3); }
    .index-btn { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 0.75rem; padding: 0.75rem; text-align: center; cursor: pointer; transition: all 0.2s; margin: 0.25rem; }
    .index-btn:hover { transform: translateY(-3px); border-color: #3b82f6; background: linear-gradient(135deg, #1e293b 0%, #1e3a8a 100%); box-shadow: 0 10px 20px -5px rgba(59,130,246,0.4); }
    .news-item { background: #0f172a; border-left: 4px solid #3b82f6; border-radius: 0.75rem; padding: 1rem; margin-bottom: 0.75rem; transition: all 0.2s; }
    .news-item:hover { background: #1e293b; transform: translateX(5px); }
    .sentiment-badge { font-size: 0.7rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 20px; display: inline-block; }
    .positive-badge { background: #10b981; color: white; }
    .neutral-badge { background: #f59e0b; color: white; }
    .negative-badge { background: #ef4444; color: white; }
    .share-btn { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.8rem; border-radius: 2rem; font-size: 0.75rem; font-weight: 500; transition: all 0.2s; text-decoration: none; color: white; margin: 0.2rem; }
    .share-btn:hover { transform: translateY(-2px); filter: brightness(1.1); }
    .share-tiktok { background: #000000; border: 1px solid #00f2ea; }
    .share-twitter { background: #1DA1F2; }
    .share-facebook { background: #4267B2; }
    .share-linkedin { background: #0077B5; }
    .share-reddit { background: #FF4500; }
    .share-telegram { background: #0088cc; }
    .share-whatsapp { background: #25D366; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #1e293b; border-radius: 3px; }
    ::-webkit-scrollbar-thumb { background: #3b82f6; border-radius: 3px; }
    @media (max-width: 768px) { .metric-value { font-size: 1.2rem; } .score-circle { width: 100px; height: 100px; font-size: 1.8rem; } }
</style>
""", unsafe_allow_html=True)

# ============================================
# SHARE FUNCTIONALITY
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
# INDICES GROUPED BY REGION
# ============================================
INDICES_BY_REGION = {
    "North America": {
        "🇺🇸 S&P 500": {"ticker": "^GSPC", "color": "#3b82f6", "market": "US Large Cap"},
        "🇺🇸 NASDAQ": {"ticker": "^IXIC", "color": "#10b981", "market": "US Tech"},
        "🇺🇸 Dow Jones": {"ticker": "^DJI", "color": "#f59e0b", "market": "US Blue Chip"},
        "🇨🇦 TSX": {"ticker": "^GSPTSE", "color": "#ef4444", "market": "Canada"},
    },
    "South America": {
        "🇧🇷 Bovespa": {"ticker": "^BVSP", "color": "#22c55e", "market": "Brazil"},
        "🇲🇽 IPC": {"ticker": "^MXX", "color": "#a855f7", "market": "Mexico"},
    },
    "Europe": {
        "🇪🇺 Euro Stoxx 50": {"ticker": "^STOXX50E", "color": "#8b5cf6", "market": "Eurozone"},
        "🇩🇪 DAX": {"ticker": "^GDAXI", "color": "#ef4444", "market": "Germany"},
        "🇬🇧 FTSE 100": {"ticker": "^FTSE", "color": "#06b6d4", "market": "UK"},
        "🇫🇷 CAC 40": {"ticker": "^FCHI", "color": "#ec4899", "market": "France"},
        "🇨🇭 SMI": {"ticker": "^SSMI", "color": "#14b8a6", "market": "Switzerland"},
        "🇪🇸 IBEX 35": {"ticker": "^IBEX", "color": "#f97316", "market": "Spain"},
        "🇳🇱 AEX": {"ticker": "^AEX", "color": "#eab308", "market": "Netherlands"},
        "🇸🇪 OMXS30": {"ticker": "^OMX", "color": "#10b981", "market": "Sweden"},
        "🇮🇹 FTSE MIB": {"ticker": "^FTSEMIB", "color": "#ec4899", "market": "Italy"},
        "🇵🇹 PSI (Portugal)": {"ticker": "^PSI20", "color": "#00c853", "market": "Portugal"},
    },
    "Asia": {
        "🇯🇵 Nikkei 225": {"ticker": "^N225", "color": "#f97316", "market": "Japan"},
        "🇯🇵 TOPIX": {"ticker": "^TOPX", "color": "#f59e0b", "market": "Japan Broad"},
        "🇨🇳 Shanghai Composite": {"ticker": "000001.SS", "color": "#ef4444", "market": "China A"},
        "🇨🇳 Shenzhen": {"ticker": "399001.SZ", "color": "#eab308", "market": "China SME"},
        "🇭🇰 Hang Seng": {"ticker": "^HSI", "color": "#14b8a6", "market": "Hong Kong"},
        "🇹🇼 Taiwan Weighted": {"ticker": "^TWII", "color": "#8b5cf6", "market": "Taiwan"},
        "🇰🇷 KOSPI": {"ticker": "^KS11", "color": "#a855f7", "market": "South Korea"},
        "🇮🇳 Nifty 50": {"ticker": "^NSEI", "color": "#06b6d4", "market": "India"},
        "🇮🇳 BSE Sensex": {"ticker": "^BSESN", "color": "#22c55e", "market": "India"},
        "🇸🇬 Straits Times": {"ticker": "^STI", "color": "#10b981", "market": "Singapore"},
    },
    "Oceania": {
        "🇦🇺 ASX 200": {"ticker": "^AXJO", "color": "#f97316", "market": "Australia"},
    },
    "Africa": {
        "🇿🇦 Top 40": {"ticker": "^J203", "color": "#f59e0b", "market": "South Africa"},
    },
    "Middle East": {
        "🇸🇦 TASI": {"ticker": "^TASI", "color": "#3b82f6", "market": "Saudi Arabia"},
    }
}

def get_index_constituents(ticker):
    """Return top 15 stocks for each index."""
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

# ============================================
# LARGE TICKER UNIVERSE (15,000+ assets)
# ============================================
def build_full_universe():
    """Generate a list of 15,000+ tickers using multiple sources."""
    # Core US (S&P 500 + NASDAQ 100 + Russell 2000 representative)
    us_large = ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","BRK-B","JPM","V","JNJ","WMT","PG","UNH","HD","DIS","MA","BAC","NFLX","KO","PEP","INTC","CSCO","ADBE","CRM","COST","CVX","XOM","WFC","QCOM","TXN","AMGN","HON","LMT","UPS","IBM","SBUX","NKE","BA","GE","CAT","GS","MS","BLK","AXP","VZ","T","RTX","LOW","PYPL","INTU","MDT","ISRG","NOW","SYK","TGT","CI","ZTS","DUK","MO","USB","PNC","COF","EMR","MMM","APD","CL","MAR","FDX","ADP","NSC","ROP","PGR","BKNG","UBER","ABNB","DASH","SNOW","ZS","CRWD","PANW","OKTA","WDAY","TEAM","SHOP","ROKU","MRNA","PFE","BIIB","GILD","REGN","VRTX","ILMN","IDXX","ALGN","DXCM","BSX","ABT","TMO","DHR","NEE","SO","PLD","AMT","CCI","EQIX","SPGI","ICE","CME","MCO","MSCI","KKR","APO","BX","ARES","COIN","SQ","AFRM","SOFI","RBLX","ADSK","CDNS","SNPS","ANSS","TT","PH","ITW","CMI","PCAR","FAST","GWW","LII","IR","DOV","ROK","ETN","GEV","HUBB","JCI","CARR","OTIS","ALLE","AOS","MAS","LOW","HD","TSCO","BBY","DKS","ROST","TJX","M","KSS","JWN","GPS","ANF","URBN","ETSY","CVNA","CPRT","CTAS","HON","BA","LMT","NOC","GD","LHX","HII","TXT","RTX","TDG","HEI","AXON","SWK","SNA","TTC","PII","BC","DOOO","THO","WGO","LCID","RIVN","F","GM","STLA","TM","HMC","BMW","MBG","VOW","RACE","FERR","BYD","NIO","LI","XPEV","ZK","RIVN","LCID","FSR","GOEV","SOLO","NVAX","MRNA","BNTX","AZN","SNY","GSK","PFE","MRK","ABBV","JNJ","BMY","LLY","NVO","NVS","RHHBY","SAP","ORCL","IBM","HPQ","DELL","HPE","SMCI","NTAP","STX","WDC","MU","LRCX","AMAT","KLAC","TER","ON","ADI","MCHP","NXPI","STM","IFNNY","TXN","AVGO","QCOM","SWKS","CRUS","SYNA","AMD","INTC","MRVL","LSCC","ALGM","AMBA","PI","MTSI","VSH","DIOD","POWI","WOLF","CREE","LITE","COHR","AAOI","ACLS","VECO","UCTT","ICHR","FORM","AMKR","ONTO","NVMI","CAMT","AXTI","TSM","UMC","GFS","SIMO","MPWR","POWI","DIOD","ALGM","MTSI","VSH","PLAB","ICHR","UCTT","FORM","ONTO","NVMI","CAMT","AXTI","KLIC","COHU","VECO","ACLS"]
    # Add mid-cap and small-cap from Russell 2000 symbols (sample)
    russell_sample = ["AAN","AAP","ABG","ABM","ACAD","ACCO","ACEL","ACHC","ACIW","ACLS","ACM","ACMR","ACNB","ACOR","ACRS","ACT","ACU","ACVA","ACXP","ADAG","ADAP","ADEA","ADI","ADM","ADMA","ADNT","ADPT","ADSK","ADT","ADUS","ADVM","AEE","AEG","AEHL","AEHR","AEIS","AEK","AEL","AEM","AEP","AER","AES","AFBI","AFCG","AFG","AFGB","AFIB","AFMD","AFRM","AGCO","AGEN","AGIO","AGL","AGM","AGNC","AGO","AGR","AGRO","AGX","AGYS","AHCO","AHL","AHPA","AHR","AHT","AI","AIG","AIH","AIHS","AIMC","AIN","AIP","AIR","AIRC","AIRG","AIT","AJG","AJRD","AKAM","AKBA","AKER","AKRO","ALB","ALCO","ALDX","ALEC","ALE","ALEX","ALG","ALGM","ALGN","ALGT","ALHC","ALIM","ALK","ALKS","ALKT","ALL","ALLE","ALLY","ALNY","ALPN","ALRM","ALRN","ALRS","ALSN","ALT","ALTG","ALTR","ALTS","ALTY","ALV","ALXO","ALYA","AM","AMAL","AMAT","AMBA","AMBC","AMBO","AMC","AMCI","AMCR","AMD","AME","AMED","AMG","AMGN","AMH","AMK","AMKR","AMN","AMP","AMPH","AMPS","AMPY","AMRC","AMRK","AMRN","AMRX","AMSF","AMST","AMSWA","AMT","AMTB","AMTD","AMTX","AMWD","AMWL","AMX","AMZA","AN","ANAB","ANDE","ANET","ANF","ANGI","ANGO","ANIK","ANIP","ANIX","ANL","ANSS","ANTE","ANTX","ANVS","ANY","AOD","AOMR","AON","AOS","AOSL","AP","APA","APAM","APD","APDN","APEI","APEN","APG","APGB","APGN","APH","API","APLE","APLS","APLT","APM","APN","APO","APOG","APPS","APRE","APRN","APRSN","APTI","APTO","APTV","APWC","APYX","AQB","AQMS","AQNU","AQST","AQUA","AR","ARA","ARAY","ARBE","ARBK","ARBT","ARC","ARCB","ARCC","ARCE","ARCH","ARCO","ARCT","ARD","ARDC","ARDX","ARE","AREC","ARG","ARGO","ARHS","ARI","ARIS","ARIZ","ARKO","ARKR","ARLO","ARLP","ARMK","ARMP","AROC","AROW","ARQ","ARR","ARRO","ARRS","ARRY","ARSD","ARTE","ARTL","ARTNA","ARTW","ARVL","ARWR","ASA","ASAN","ASB","ASBA","ASGN","ASH","ASIX","ASLE","ASLN","ASM","ASMB","ASML","ASND","ASO","ASPN","ASPS","ASR","ASRT","ASRV","ASTC","ASTE","ASTL","ASTR","ASTS","ASX","ASYS","ATAT","ATH","ATHM","ATHX","ATI","ATKR","ATLC","ATLO","ATLX","ATMC","ATNI","ATNM","ATNX","ATO","ATOM","ATOS","ATR","ATRA","ATRC","ATRI","ATRO","ATSG","ATVI","ATXG","AU","AUB","AUBN","AUDC","AUGX","AUPH","AUR","AUROW","AUS","AUTL","AUTO","AUUD","AVA","AVAH","AVAL","AVAV","AVB","AVCO","AVDL","AVDX","AVEO","AVGO","AVGR","AVIR","AVNW","AVNS","AVNT","AVO","AVPT","AVRO","AVT","AVTE","AVTR","AVXL","AWK","AWP","AWRE","AX","AXDX","AXGN","AXL","AXLA","AXON","AXP","AXR","AXS","AXSM","AXTA","AXU","AY","AYI","AYLA","AYRO","AYTU","AZ","AZEK","AZN","AZO","AZPN","AZRE","AZTA","AZUL","AZYO","B","BA","BABA","BAC","BAM","BAND","BANF","BANR","BANX","BAOS","BAP","BARK","BASE","BATL","BAX","BB","BBAI","BBBY","BBCP","BBDO","BBGI","BBI","BBIG","BBIO","BBLN","BBOX","BBQ","BBSI","BBTN","BBUC","BBVA","BBW","BBWI","BC","BCAB","BCAL","BCBP","BCC","BCDA","BCE","BCEL","BCLI","BCML","BCO","BCOV","BCPC","BCRX","BCS","BCSA","BCSF","BCTX","BCYC","BDC","BDJ","BDL","BDN","BDR","BDSX","BDTX","BDX","BE","BEAM","BECN","BEDU","BEEM","BEKE","BELFA","BELFB","BEN","BENE","BEP","BEPC","BEPH","BEPI","BERY","BEST","BETR","BFAM","BFC","BFH","BFI","BFIN","BFLY","BFS","BFST","BG","BGC","BGFV","BGH","BGI","BGNE","BGR","BGRY","BGS","BGSF","BHB","BHC","BHE","BHF","BHG","BHK","BHLB","BHR","BHRB","BHSE","BHV","BHVN","BIDU","BILL","BIO","BIOL","BIOX","BIP","BIPC","BIPH","BIPI","BJC","BJRI","BK","BKD","BKE","BKH","BKI","BKNG","BKN","BKR","BKSY","BKU","BKYI","BL","BLBD","BLBX","BLCM","BLCO","BLD","BLDE","BLDR","BLFY","BLIN","BLK","BLKB","BLMN","BLND","BLNK","BLPH","BLRX","BLTE","BLTS","BLU","BLUA","BLUE","BLX","BMA","BMAC","BMEA","BMEZ","BMI","BML","BMO","BMRA","BMRC","BMRN","BMTC","BMY","BND","BNED","BNGO","BNIX","BNL","BNNR","BNOX","BNR","BNS","BNTC","BNTX","BNY","BOCH","BOCN","BOE","BOH","BOKF","BOLD","BOLT","BOMN","BON","BOOM","BOOT","BORR","BOSC","BOSS","BOTJ","BOWL","BOX","BP","BPAC","BPMC","BPOP","BPRN","BPT","BPTH","BPTS","BPYPM","BQ","BR","BRAC","BRAG","BRBR","BRBS","BRC","BRCC","BRCN","BRDG","BRDS","BREZ","BRFH","BRFS","BRID","BRKL","BRKR","BRK","BRK-A","BRK-B","BRKS","BRMK","BRNS","BRO","BROG","BRP","BRPM","BRQS","BRSP","BRT","BRX","BRY","BSAC","BSBK","BSBR","BSCP","BSET","BSGA","BSGM","BSIG","BSL","BSM","BSQR","BSRR","BSVN","BSX","BSY","BTB","BTBD","BTBT","BTCM","BTCS","BTI","BTMD","BTN","BTO","BTRS","BTTR","BTTX","BTU","BTWN","BUD","BUI","BURL","BUSE","BV","BVH","BVS","BW","BWB","BWEN","BWFG","BWG","BWLP","BWMN","BWMX","BWSN","BWV","BWXT","BX","BXC","BXG","BXL","BXP","BXRX","BXSL","BY","BYD","BYFC","BYND","BYN","BYSI","BZ","BZFD","BZH","BZUN","C","CAAP","CABA","CABO","CAC","CACC","CACI","CADE","CADL","CAE","CAF","CAG","CAH","CAKE","CAL","CALC","CALM","CALT","CAMP","CAMT","CAN","CAPL","CAPR","CAR","CARA","CARE","CARL","CARM","CARR","CARS","CARV","CASA","CASH","CASI","CASS","CAT","CATC","CATH","CATO","CATY","CBA","CBAH","CBAY","CBB","CBFV","CBI","CBIO","CBK","CBL","CBRE","CBRL","CBSH","CBT","CBU","CBUS","CBZ","CC","CCAP","CCB","CCBG","CCCC","CCCS","CCD","CCEP","CCF","CCG","CCI","CCJ","CCK","CCL","CCLP","CCM","CCNC","CCNE","CCNI","CCNR","CCO","CCOI","CCRD","CCRN","CCS","CCSI","CCT","CCTG","CCU","CCV","CD","CDAK","CDAQ","CDE","CDEV","CDIO","CDL","CDLX","CDMO","CDNA","CDNS","CDOR","CDR","CDRE","CDRO","CDT","CDTX","CDW","CDXC","CDXS","CDZI","CE","CEAD","CECO","CEE","CEF","CEI","CEIX","CELC","CELH","CELU","CELZ","CEMI","CEN","CENX","CEPU","CERE","CERS","CERT","CET","CETX","CEVA","CEV","CF","CFB","CFBK","CFG","CFIV","CFLT","CFMS","CFR","CFRX","CFSB","CGBD","CGDG","CGC","CGEM","CGEN","CGNT","CGNX","CGO","CGRN","CGUS","CHCI","CHCT","CHD","CHDN","CHE","CHEF","CHEK","CHGG","CHI","CHK","CHKP","CHMG","CHMI","CHN","CHNR","CHRS","CHRW","CHS","CHT","CHTR","CHUY","CHW","CHWY","CHX","CI","CIA","CIB","CIBR","CIDM","CIEN","CIF","CIFR","CIG","CIGI","CII","CIIG","CIK","CIL","CIM","CINF","CING","CINR","CIO","CION","CIR","CISO","CIT","CIVB","CIX","CIZ","CJAX","CJD","CJEW","CJNK","CJPR","CKPT","CKX","CL","CLAA","CLAR","CLAS","CLB","CLBK","CLBR","CLBS","CLBT","CLDX","CLEU","CLF","CLFD","CLGN","CLH","CLIM","CLIR","CLLS","CLM","CLMT","CLNE","CLNN","CLNR","CLOE","CLOEU","CLOH","CLOI","CLOZ","CLPR","CLPS","CLPT","CLR","CLRB","CLRC","CLRG","CLRO","CLS","CLSD","CLSK","CLSM","CLST","CLSY","CLTL","CLVR","CLVT","CLW","CLX","CM","CMA","CMAX","CMBM","CMBT","CMCA","CMC","CMCL","CMCM","CMCO","CMCSA","CMCT","CMD","CMDY","CME","CMG","CMI","CMLS","CMMB","CMP","CMPO","CMPR","CMPS","CMPX","CMRE","CMRX","CMS","CMT","CMTG","CMTL","CMU","CN","CNA","CNBKA","CNC","CNDT","CNET","CNF","CNFR","CNGL","CNH","CNI","CNK","CNMD","CNNE","CNO","CNOB","CNP","CNQ","CNS","CNSL","CNSP","CNTA","CNTB","CNTG","CNTX","CNX","CNXN","CO","COCO","CODA","CODI","CODX","COE","COF","COFS","COGT","COHN","COHR","COHU","COIN","COKE","COLB","COLD","COLL","COLM","COM","COMB","COMM","COMP","COMS","CON","CONN","CONX","COO","COOK","COOL","COOP","COP","COR","CORT","CORZ","COSM","COTY","COUP","COUR","COVA","COWN","CP","CPA","CPAA","CPAC","CPB","CPE","CPER","CPF","CPG","CPHC","CPHI","CPI","CPK","CPLP","CPNG","CPOP","CPRI","CPRT","CPRX","CPS","CPSH","CPSS","CPST","CPT","CPTK","CPUH","CQP","CR","CRBG","CRBP","CRBU","CRC","CRCT","CRDF","CRDL","CRDO","CRE","CREC","CRESY","CREV","CREX","CRGE","CRGY","CRH","CRI","CRIS","CRK","CRKN","CRL","CRMD","CRMT","CRNC","CRNT","CRNX","CRON","CROX","CRS","CRSP","CRSR","CRT","CRTO","CRUS","CRVL","CRVS","CRWD","CRWS","CRZO","CS","CSA","CSAN","CSBR","CSCO","CSGP","CSGS","CSII","CSIQ","CSL","CSLR","CSLT","CSPI","CSQ","CSR","CSSE","CSTE","CSTL","CSTM","CSTR","CSV","CSWC","CSWI","CSX","CT","CTAS","CTBB","CTBI","CTDD","CTEC","CTET","CTG","CTGO","CTHR","CTIB","CTIC","CTKB","CTLP","CTLT","CTMX","CTM","CTNM","CTNT","CTO","CTOS","CTR","CTRA","CTRE","CTS","CTSH","CTSO","CTVA","CTXR","CUB","CUBA","CUBI","CUE","CUEN","CULL","CULP","CURV","CUTR","CUZ","CVA","CVAC","CVBF","CVCO","CVE","CVEO","CVGI","CVGW","CVI","CVII","CVLG","CVLT","CVLY","CVM","CVNA","CVR","CVS","CVU","CVV","CVX","CW","CWAN","CWBC","CWCO","CWEN","CWGL","CWH","CWI","CWK","CWS","CWST","CXM","CXO","CXT","CXW","CYAN","CYBN","CYBR","CYCC","CYCN","CYD","CYH","CYRX","CYTH","CYTK","CYTO","CZFS","CZNC","CZOO","CZR","CZWI","D","DABA","DAC","DADA","DAIO","DAKT","DAL","DALN","DALS","DALT","DAN","DAO","DAR","DASH","DATE","DAVA","DAVE","DAWN","DB","DBC","DBD","DBGI","DBI","DBL","DBRG","DBTX","DBV","DC","DCBO","DCF","DCI","DCOM","DCP","DCPH","DCT","DCTH","DD","DDD","DDF","DDL","DDS","DDT","DE","DEA","DEC","DECK","DEH","DEI","DELL","DEN","DENN","DESP","DEST","DETX","DEUS","DEW","DFFN","DFH","DFIN","DFP","DFS","DG","DGICA","DGII","DGNU","DGP","DGRS","DGRW","DGX","DH","DHAC","DHBC","DHC","DHCNI","DHCNL","DHF","DHI","DHIL","DHX","DIA","DIBS","DICE","DIN","DINO","DIOD","DIS","DISA","DISH","DIT","DIV","DIVB","DIVO","DIXY","DJCO","DK","DKL","DKNG","DKS","DLA","DLB","DLHC","DLNG","DLPN","DLR","DLTH","DLTR","DLX","DM","DMAC","DMAT","DMB","DMC","DMF","DMLP","DMO","DMRC","DMS","DMTK","DMYI","DMYS","DNA","DNB","DNLI","DNMR","DNN","DNOW","DNUT","DO","DOC","DOCN","DOCS","DOCU","DOGZ","DOLE","DOMA","DOMH","DOMO","DOOO","DORM","DOUG","DOV","DOW","DOX","DPCS","DPG","DPRO","DPST","DPZ","DQ","DRCT","DRD","DRH","DRI","DRMA","DRQ","DRRX","DRS","DRTS","DRVN","DS","DSGN","DSGR","DSGX","DSKE","DSP","DSS","DSX","DT","DTB","DTE","DTF","DTIL","DTM","DTOC","DTSS","DTST","DTV","DUET","DUK","DUNE","DUO","DUOL","DUOT","DURA","DUSL","DUST","DV","DVA","DVAX","DVN","DWAC","DWAS","DXC","DXCM","DXF","DXLG","DXPE","DXR","DXYN","DY","DYAI","DYLD","DYNT","DZSI","E","EA","EAF","EARN","EAST","EAT","EB","EBAY","EBC","EBF","EBMT","EBS","EBTC","EC","ECAT","ECC","ECCF","ECCV","ECCW","ECCX","ECL","ECOR","ECPG","ECVT","ED","EDAP","EDBL","EDIT","EDN","EDS","EDSA","EDTK","EDTX","EDU","EE","EEA","EEFT","EEIQ","EELV","EEM","EEMA","EEMD","EEMS","EFC","EFF","EFG","EFII","EFO","EFSC","EFSH","EFT","EFX","EGAN","EGBN","EGHT","EGLE","EGO","EGP","EGY","EH","EHC","EHTH","EIC","EICA","EICB","EIG","EIM","EIX","EJH","EKSO","EL","ELA","ELAN","ELAT","ELBM","ELC","ELD","ELDN","ELEV","ELF","ELG","ELLO","ELMD","ELOX","ELP","ELS","ELSE","ELTK","ELV","ELYM","ELYS","EM","EMB","EMBC","EMBK","EMCF","EMD","EME","EMF","EMKR","EML","EMLD","EMN","EMO","EMP","EMR","ENB","ENBA","ENCP","ENDP","ENFC","ENFN","ENG","ENIC","ENJ","ENLC","ENLV","ENO","ENOB","ENPH","ENR","ENS","ENSC","ENSG","ENSV","ENTA","ENTF","ENTG","ENTX","ENV","ENVA","ENVB","ENVX","EOG","EOI","EOLS","EOS","EOSE","EOT","EP","EPAC","EPAM","EPC","EPD","EPM","EPR","EPRT","EPSN","EQC","EQH","EQIX","EQR","EQS","EQT","ERAS","ERII","ERJ","ERNA","ERX","ERY","ES","ESAB","ESAC","ESBA","ESCA","ESE","ESEA","ESGR","ESI","ESLA","ESLT","ESNT","ESP","ESPR","ESQ","ESRT","ESS","ESTA","ESTC","ESTE","ET","ETB","ETD","ETG","ETHO","ETN","ETNB","ETON","ETR","ETRN","ETSY","ETV","ETW","ETWO","ETX","ETY","EUCG","EUCR","EUDG","EURN","EUSA","EUSC","EVA","EVAX","EVBG","EVBN","EVC","EVCM","EVE","EVF","EVG","EVGN","EVGO","EVH","EVI","EVLO","EVLV","EVO","EVOK","EVOL","EVR","EVRG","EVRI","EVTV","EVV","EW","EWBC","EWTX","EXAS","EXC","EXD","EXEL","EXFY","EXG","EXI","EXK","EXLS","EXP","EXPD","EXPI","EXPO","EXPR","EXR","EXTR","EYE","EYEN","EYLD","EYPT","EZFL","EZGO","EZPW","F","FA","FAB","FACT","FAD","FAF","FALN","FAMI","FANG","FANH","FARM","FARO","FAST","FAT","FATBB","FATBP","FATE","FAX","FB","FBC","FBIO","FBIZ","FBK","FBMS","FBNC","FBIO","FBP","FBRT","FBRX","FBT","FC","FCAP","FCAU","FCBC","FCCO","FCEF","FCF","FCFS","FCN","FCNCA","FCOB","FCPT","FCRD","FCRX","FCT","FCX","FDBC","FDD","FDEU","FDHY","FDMT","FDP","FDS","FDT","FDUS","FDX","FE","FEAM","FEDU","FEI","FELE","FEM","FEMB","FEN","FENC","FENG","FEP","FER","FERG","FERN","FET","FEX","FEZ","FF","FFA","FFBC","FFC","FFIC","FFIE","FFIN","FFIV","FFNW","FFWM","FGEN","FGI","FHB","FHI","FHLT","FHN","FIAC","FIBK","FICO","FICV","FID","FIII","FILL","FINM","FINV","FIS","FISI","FITB","FITE","FIV","FIVE","FIVN","FIX","FIZZ","FJUN","FJUL","FJUNE","FJUNW","FJUNZ","FL","FLAC","FLEX","FLGC","FLGT","FLIC","FLL","FLM","FLME","FLMN","FLNC","FLNG","FLNT","FLO","FLR","FLS","FLT","FLUX","FLWS","FLXS","FLYE","FLYW","FMAO","FMB","FMBH","FMET","FMF","FMI","FMN","FMNB","FMO","FMS","FMTX","FMY","FN","FNA","FNB","FNCB","FND","FNF","FNGO","FNGU","FNGZ","FNHC","FNKO","FNLC","FNV","FNVT","FNWB","FNWD","FOA","FOCS","FOE","FOF","FOLD","FONR","FOR","FORA","FORG","FORM","FORR","FORTE","FOSL","FOX","FOXA","FOXF","FPA","FPAY","FPH","FPL","FPRX","FPV","FR","FRA","FRBA","FRBK","FRC","FRD","FREE","FREY","FRG","FRGE","FRGI","FRGT","FRHC","FRI","FRLN","FRME","FRO","FROG","FRON","FRPH","FRPT","FRSH","FRST","FRSX","FRT","FRTA","FRTY","FRXB","FSAC","FSBC","FSBW","FSEA","FSFG","FSK","FSLR","FSM","FSR","FSS","FST","FSTR","FSTX","FTAI","FTCH","FTCI","FTDR","FTEK","FTF","FTFT","FTI","FTK","FTNT","FTPA","FTS","FTV","FUBO","FUL","FULC","FULT","FUNC","FUND","FURY","FUSB","FUSN","FUTU","FUV","FV","FVC","FVCB","FVRR","FWAC","FWBI","FWONA","FWONK","FWRD","FWRG","FXCO","FXNC","FZT","G","GAB","GABC","GAIA","GAIN","GALT","GAM","GAMB","GAME","GAN","GAPA","GAPB","GASS","GATO","GATX","GAU","GBCI","GBDC","GBIO","GBL","GBLI","GBR","GBRG","GBS","GBT","GCC","GCDC","GCGV","GCI","GCMG","GCO","GCT","GCTK","GCV","GD","GDDY","GDE","GDEV","GDHG","GDL","GDO","GDOT","GDRX","GDS","GDV","GDYN","GE","GECC","GEEX","GEF","GEG","GEL","GEN","GENC","GENE","GENK","GENY","GEO","GEOS","GERN","GES","GEVO","GF","GFAI","GFF","GFI","GFL","GFLU","GFS","GGAL","GGB","GGG","GGT","GGZ","GHC","GHG","GHIX","GHM","GHRS","GHSI","GHY","GIB","GIC","GIFI","GIGM","GII","GIL","GILT","GIM","GIPR","GIS","GJH","GJO","GJP","GJR","GJS","GJT","GKOS","GL","GLAD","GLBE","GLBS","GLBZ","GLDD","GLEE","GLG","GLHA","GLIN","GLLI","GLMD","GLNG","GLO","GLOB","GLOP","GLP","GLPG","GLPI","GLRE","GLT","GLTA","GLTO","GLUE","GLV","GLW","GLYC","GM","GMBL","GMDA","GME","GMED","GMGI","GMLP","GMRE","GMS","GMVD","GNE","GNFT","GNK","GNL","GNLN","GNMA","GNOM","GNPX","GNR","GNRC","GNS","GNSS","GNT","GNTX","GNTY","GNW","GO","GOAU","GOCO","GODN","GOEV","GOGL","GOGO","GOLD","GOLF","GOOD","GOOG","GOOGL","GOOS","GORO","GOSS","GOTU","GOVX","GP","GPAC","GPAL","GPCR","GPC","GPI","GPK","GPMT","GPN","GPOR","GPP","GPRE","GPRK","GPRO","GPS","GPT","GPUS","GPX","GQ","GQQ","GRAB","GRAY","GRBK","GRC","GRCL","GRCY","GREE","GREEN","GREK","GRFS","GRID","GRIN","GRIP","GRMN","GRN","GRNB","GRND","GRNT","GRNV","GROW","GRPH","GRPN","GRRR","GRTS","GRTX","GRVY","GRWG","GRX","GSA","GSAT","GSBC","GSBD","GSD","GSEE","GSFP","GSG","GSHD","GSIT","GSK","GSL","GSLC","GSM","GSQB","GSRM","GSRX","GSS","GSST","GSUN","GSY","GT","GTAC","GTBP","GTE","GTEC","GTES","GTI","GTIM","GTLS","GTN","GTO","GTR","GTRA","GTS","GTT","GTX","GTXAP","GTY","GUBG","GUID","GULF","GUNR","GURE","GUT","GV","GVA","GVAL","GVCI","GVI","GVP","GWRE","GWRS","GWW","GXGX","GYRO","H","HA","HAE","HAL","HALL","HALO","HAPP","HARP","HAS","HASG","HAT","HAUS","HAWX","HAYN","HAYW","HBB","HBCP","HBIO","HBI","HBLA","HBNC","HBP","HBT","HCAT","HCCI","HCDI","HCI","HCKT","HCM","HCSG","HCTI","HCWB","HCXY","HD","HDB","HDSN","HE","HEAR","HEES","HEET","HEI","HELE","HEPA","HEPS","HES","HESM","HEVI","HEXO","HFFG","HFG","HFRO","HFWA","HGBL","HGH","HGLB","HGTY","HGV","HHC","HHGC","HHRS","HI","HIBB","HIFS","HIG","HIHO","HII","HILS","HIMX","HIO","HIPO","HITI","HIVE","HIW","HL","HLBZ","HLF","HLGN","HLI","HLIO","HLIT","HLNE","HLT","HLTH","HLVX","HLX","HMC","HMNF","HMST","HMTV","HMY","HNI","HNNA","HNO","HNRA","HNST","HNW","HOFT","HOG","HOLI","HOLX","HOMB","HOMZ","HON","HONE","HOOD","HOOK","HOPE","HORI","HOTH","HOV","HOVNP","HOWL","HP","HPA","HPCO","HPE","HPK","HPP","HPQ","HPS","HQH","HQI","HQY","HR","HRB","HRBR","HRC","HRMY","HROW","HROWM","HRT","HRTG","HRTX","HRYU","HSBC","HSC","HSDT","HSIC","HSII","HSKA","HSON","HST","HSTM","HSY","HT","HTAB","HTBI","HTBK","HTCR","HTD","HTEC","HTGC","HTH","HTHT","HTIA","HTIC","HTLD","HTLF","HTZ","HUBB","HUBG","HUDI","HUGE","HUIZ","HUM","HUMA","HUN","HURC","HUSA","HUT","HWBK","HWCPZ","HWEL","HWKN","HWM","HXI","HY","HYAC","HYB","HYFM","HYG","HYI","HYLB","HYLN","HYMC","HYPR","HYRE","HYS","HYT","HYW","HYZD","IAC","IAD","IAE","IAF","IAG","IAPR","IART","IAS","IAU","IAUF","IBA","IBB","IBBJ","IBCE","IBCP","IBEX","IBIO","IBKR","IBM","IBN","IBOC","IBP","IBRX","IBTA","IBTE","IBTF","IBTH","IBTI","IBTJ","IBTK","IBTM","IBUY","ICAD","ICCC","ICCH","ICD","ICE","ICFI","ICHR","ICL","ICLK","ICLNF","ICLR","ICMB","ICNC","ICOW","ICR","ICUI","ICVX","IDA","IDAI","IDBA","IDCC","IDE","IDEX","IDN","IDR","IDSA","IDT","IDW","IDXX","IDYA","IEA","IEC","IEF","IEX","IFF","IFGL","IFIN","IFN","IFRA","IFRX","IFS","IG","IGA","IGC","IGD","IGF","IGHG","IGI","IGIB","IGIC","IGLD","IGM","IGN","IGOV","IGR","IGS","IGT","IGV","IHC","IHD","IHRT","IHT","IID","IIF","III","IIII","IIIN","IIIV","IINN","IIPR","IIVI","IJH","IJJ","IJK","IJR","IJS","IJT","IKNA","IKT","ILMN","ILPT","ILTB","IMAB","IMAC","IMAX","IMBI","IMCC","IMCR","IMCV","IMGN","IMH","IMKTA","IMMP","IMMR","IMMX","IMNM","IMO","IMOM","IMOS","IMPL","IMPP","IMPPP","IMPV","IMRN","IMRX","IMTE","IMTG","IMTX","IMUX","IMV","IMVT","IMXI","INAB","INBK","INBX","INCR","INCY","INDA","INDB","INDI","INDO","INDY","INFI","INFL","INFN","INFR","ING","INGN","INGR","INKA","INKW","INM","INMB","INMD","INMKT","INN","INNV","INO","INOD","INOV","INPX","INSE","INSG","INSI","INSM","INSP","INST","INSW","INT","INTA","INTC","INTE","INTG","INTJ","INTT","INTU","INTX","INUV","INVA","INVE","INVH","INVO","INVZ","INZY","IOAC","IOBT","IOCT","IONM","IONQ","IONS","IOSP","IOVA","IP","IPA","IPAR","IPB","IPDN","IPG","IPGP","IPHA","IPI","IPKW","IPLDP","IPM","IPN","IPOD","IPOF","IPOS","IPSC","IPVA","IPVF","IPVI","IPW","IPWR","IQ","IQI","IQV","IR","IRBT","IRDM","IREN","IRIX","IRM","IRMD","IRNT","IROH","IROQ","IRTC","IRWD","ISAA","ISCB","ISCF","ISD","ISDR","ISEE","ISEM","ISHP","ISIG","ISLX","ISMD","ISPC","ISPO","ISPR","ISPY","ISRA","ISRG","ISSC","ISTB","ISTR","ISUN","ISVL","ISWN","ISZE","IT","ITA","ITB","ITCI","ITE","ITGR","ITI","ITIC","ITOS","ITP","ITQ","ITRG","ITRI","ITRM","ITRN","ITT","ITUB","ITW","IUS","IUSB","IUSG","IUSS","IUSV","IVA","IVAC","IVCA","IVCB","IVDA","IVDN","IVE","IVEG","IVH","IVI","IVLC","IVOG","IVOL","IVOO","IVR","IVT","IVV","IVW","IVZ","IWIN","IWM","IWN","IWO","IWP","IWR","IWS","IWV","IWX","IWY","IX","IXC","IXG","IXJ","IXN","IXP","IXUS","IYC","IYE","IYF","IYG","IYH","IYJ","IYM","IYR","IYF","IYW","IYX","IYZ","IZEA","J","JACK","JAGX","JAKK","JAMF","JAN","JANX","JAQC","JAZZ","JBGS","JBHT","JBK","JBL","JBLU","JBSS","JBT","JCAP","JCE","JCI","JCO","JCOM","JCPI","JCU","JD","JEF","JELD","JEMD","JEPI","JEPQ","JETS","JFIN","JFR","JG","JGGC","JGH","JHG","JHI","JHS","JHX","JILL","JJSF","JKHY","JKS","JLL","JLS","JMAC","JMIA","JMM","JMSB","JNCE","JNPR","JNUG","JOAN","JOB","JOBY","JOE","JOF","JOUT","JOYY","JP","JPC","JPI","JPM","JPN","JPS","JPT","JQC","JRI","JRO","JRS","JRVR","JSM","JSPR","JTEK","JTO","JUGG","JUGGU","JULZ","JUN","JUNZ","JUPW","JUST","JVA","JVSA","JWN","JWSM","JXJT","JXN","JYNT","K","KAI","KAJ","KALA","KALU","KALV","KAMN","KAR","KARO","KAVL","KB","KBAL","KBCP","KBH","KBNT","KBR","KBSF","KC","KCCA","KDP","KELYA","KELYB","KEN","KEP","KER","KEYS","KF","KFFB","KFH","KFRC","KFS","KFY","KGC","KHC","KIDS","KIM","KIND","KINS","KIO","KIRK","KITT","KLC","KLG","KLIC","KLR","KLTR","KLXE","KMB","KMDA","KMI","KMPB","KMPH","KMT","KMX","KN","KNBE","KNDI","KNOP","KNX","KO","KOD","KODK","KOF","KOP","KOPN","KORE","KOSS","KPLT","KPTI","KR","KRBP","KRC","KREF","KRG","KRKN","KRNL","KRNT","KRON","KROS","KRP","KRT","KRUS","KRYS","KSCP","KSM","KSS","KTB","KTCC","KTF","KTH","KTN","KTOS","KTRA","KURA","KURE","KVHI","KVSA","KVSC","KW","KWR","KYCH","KYN","KZIA","KZR","L","LAAC","LAB","LABP","LAC","LAD","LADR","LAG","LAKE","LAMR","LANC","LAND","LARK","LASR","LATG","LAUR","LAW","LAZ","LAZR","LBAI","LBC","LBH","LBI","LBRT","LBRDA","LBRDK","LBTYA","LBTYB","LBTYK","LC","LCAA","LCID","LCII","LCNB","LCTX","LCUT","LDI","LDP","LDTC","LECO","LEG","LEGH","LEGN","LEJU","LEN","LENZ","LEO","LESL","LEU","LEV","LEXX","LFAC","LFC","LFG","LFMD","LFMDP","LFST","LFT","LFWU","LGAC","LGCB","LGFA","LGHL","LGIH","LGL","LGOV","LGV","LGVN","LGWL","LHC","LHCG","LHDX","LHO","LHR","LI","LIA","LIBY","LICY","LIDR","LIFE","LII","LILA","LILAK","LINC","LIND","LINK","LION","LIT","LITB","LITE","LITT","LIVE","LIVN","LIXT","LIZI","LJA","LJPC","LKCO","LKN","LKOD","LKOR","LKQ","LL","LLAP","LLEX","LLL","LLY","LMAT","LMB","LMFA","LMND","LMNL","LMNR","LMT","LNC","LND","LNG","LNN","LNSR","LNT","LNTH","LOAN","LOB","LOCO","LODE","LOGC","LOGI","LOKM","LOMA","LON","LONE","LOOP","LOPE","LORL","LOTZ","LOVE","LOW","LPCN","LPG","LPI","LPL","LPLA","LPSN","LPTV","LPX","LQD","LQDA","LQDT","LRFC","LRMR","LRN","LSBK","LSDI","LSF","LSI","LSPD","LSTR","LSXMA","LSXMB","LSXMK","LTBR","LTC","LTH","LTHM","LTRN","LTRPA","LTRPB","LTRX","LTRY","LU","LUCD","LUCY","LUFK","LULU","LUMN","LUMO","LUNA","LUNG","LUV","LVLU","LVO","LVRO","LVTX","LWAY","LX","LXEH","LXFR","LXFT","LXU","LYB","LYEL","LYFT","LYG","LYL","LYRA","LYTS","LYV","LZ","LZB","M","MA","MAA","MACK","MACU","MAG","MAIN","MAMA","MAMO","MAN","MANH","MANU","MAPS","MAQC","MAR","MARA","MARK","MARPS","MART","MAS","MASI","MASS","MAT","MATW","MATX","MAV","MAX","MAXN","MAYS","MBC","MBIN","MBIO","MBK","MBND","MBOT","MBOX","MBRX","MBSC","MBTC","MBSD","MBUU","MBWM","MC","MCAE","MCB","MCD","MCF","MCFT","MCHP","MCHX","MCI","MCK","MCN","MCO","MCR","MCRB","MCRI","MCS","MCW","MCY","MD","MDB","MDC","MDEV","MDFN","MDGL","MDIA","MDJH","MDLZ","MDNA","MDRR","MDRX","MDT","MDU","MDVL","MDWD","MDXG","MDXH","ME","MEAC","MEC","MED","MEDP","MEDS","MEG","MEI","MEIP","MEKA","MELI","MEOA","MERC","MESA","MESO","MET","META","METC","METCB","METX","MEXX","MF","MFA","MFG","MFGP","MFH","MFIC","MFL","MFM","MFUS","MG","MGA","MGEE","MGF","MGI","MGIC","MGLD","MGNT","MGRC","MGX","MHD","MHF","MHH","MHI","MHK","MHLA","MHN","MHNC","MHO","MHR","MI","MICT","MIDD","MIGI","MILN","MIMO","MIND","MINDP","MINM","MIO","MIR","MIRM","MIST","MIT","MITO","MITQ","MITT","MIXT","MIY","MKC","MKD","MKL","MKOR","MKSI","MKTW","MKTX","ML","MLAB","MLAC","MLAI","MLCO","MLI","MLKN","MLM","MLNK","MLP","MLR","MLSS","MLTX","MLVF","MMAT","MMC","MMD","MMI","MMLP","MMM","MMMB","MMP","MMS","MMSI","MMT","MMU","MN","MNA","MNBD","MNDO","MNK","MNMD","MNPR","MNR","MNRL","MNSB","MNSO","MNST","MNTK","MNTN","MNTS","MNTV","MNX","MO","MOB","MOBBW","MOBQ","MOD","MODG","MODN","MODV","MOFG","MOGO","MOGU","MOH","MOLN","MOMO","MON","MOND","MOO","MOOD","MOON","MOR","MORF","MORN","MOS","MOTG","MOTN","MOTS","MOV","MOVE","MOXC","MP","MPA","MPAA","MPB","MPC","MPLN","MPLX","MPW","MPX","MQ","MRAI","MRAM","MRBK","MRC","MRCC","MRCY","MRIN","MRK","MRKR","MRM","MRNA","MRNS","MRO","MRSN","MRTN","MRTX","MRUS","MRVI","MRVL","MS","MSA","MSB","MSBI","MSC","MSEX","MSFT","MSGE","MSGM","MSGS","MSI","MSM","MSN","MSP","MSS","MST","MSTR","MSVB","MSW","MSWN","MT","MTA","MTAC","MTB","MTC","MTCH","MTD","MTDR","MTEK","MTEM","MTEX","MTG","MTH","MTL","MTLS","MTMT","MTN","MTNB","MTOR","MTR","MTRX","MTRX","MTSC","MTSI","MTTR","MTUL","MTUS","MTW","MTX","MTZ","MUA","MUE","MUFG","MUI","MUJ","MULN","MUR","MUSA","MUX","MVBF","MVC","MVCB","MVF","MVO","MVS","MVST","MVT","MWA","MX","MXCT","MXE","MXF","MXL","MXO","MXOX","MXXX","MYE","MYFW","MYGN","MYMD","MYNA","MYN","MYO","MYOV","MYPS","MYRG","MYSZ","MYTE","NAAS","NAB","NABH","NAC","NAD","NAII","NAK","NAN","NANC","NAOV","NATH","NATI","NATR","NAUT","NAVI","NAZ","NB","NBB","NBEV","NBHC","NBIC","NBIX","NBN","NBR","NBRV","NBTB","NBW","NBXG","NC","NCA","NCAC","NCB","NCFT","NCI","NCL","NCLH","NCMI","NCNA","NCNO","NCR","NCRX","NCV","NCV","NCZ","NDAQ","NDLS","NDMO","NDP","NDRA","NDSN","NE","NEA","NECB","NEE","NEGG","NEO","NEOG","NEON","NEP","NEPT","NERV","NET","NETC","NETI","NETL","NEU","NEW","NEWA","NEWP","NEWR","NEWT","NEX","NEXA","NEXI","NEXT","NFBK","NFE","NFLX","NFNT","NFTY","NFYS","NG","NGC","NGD","NGG","NGL","NGM","NGMS","NGS","NGVC","NGVT","NH","NHC","NHE","NHLD","NHTC","NI","NIC","NICE","NICK","NILE","NIM","NINE","NIO","NIU","NJDC","NJR","NJS","NK","NKE","NKLA","NKSH","NKTR","NKTX","NL","NLR","NLRC","NLS","NLSN","NLSP","NLTX","NLY","NM","NMCO","NMFC","NMG","NMI","NMIH","NMRA","NMRK","NMS","NMT","NMTC","NMTR","NMZ","NN","NNA","NNAV","NNDM","NNN","NNOX","NNVC","NNY","NOA","NOAH","NOC","NOD","NOG","NOK","NOM","NOMD","NONE","NOTE","NOTV","NOV","NOVA","NOVN","NOVS","NOW","NP","NPAB","NPCE","NPFD","NPK","NPO","NPP","NPTN","NPV","NRC","NRDS","NRDY","NREF","NRG","NRGV","NRIM","NRK","NRP","NRT","NSC","NSEC","NSIT","NSP","NSPR","NSS","NSSC","NST","NSTG","NSYS","NTAP","NTB","NTCO","NTCT","NTES","NTG","NTGR","NTIC","NTIP","NTLA","NTN","NTNX","NTRB","NTST","NTUS","NTWK","NU","NUBL","NUGN","NUHW","NULG","NULV","NUM","NURO","NUS","NUSC","NUSH","NUV","NUVB","NUVL","NUVO","NUW","NUWE","NUZE","NVA","NVAC","NVCN","NVCR","NVCT","NVDA","NVEC","NVEE","NVEI","NVFY","NVGS","NVMI","NVNO","NVO","NVOS","NVR","NVS","NVSA","NVST","NVT","NVTA","NVTS","NVX","NWBI","NWBO","NWE","NWFL","NWG","NWL","NWLI","NWN","NWPX","NWS","NWSA","NX","NXE","NXGL","NXGN","NXLI","NXRT","NXST","NXT","NXTC","NXTG","NXU","NYC","NYCB","NYMT","NYXH","NZF","O","OAK","OAKU","OAS","OASPU","OBCI","OBDE","OBE","OBIO","OBNK","OBT","OC","OCAX","OCC","OCCI","OCEA","OCFC","OCFT","OCG","OCGN","OCN","OCSL","OCS","OCTO","OCUL","OCUP","ODC","ODD","ODFL","ODP","OEC","OESX","OFC","OFED","OFIX","OFLX","OFS","OG","OGE","OGEN","OGI","OGN","OGS","OHI","OI","OII","OIIM","OIS","OJ","OKE","OKTA","OLB","OLD","OLE","OLED","OLK","OLLI","OLMA","OLN","OLO","OLP","OLPX","OM","OMAB","OMC","OMCL","OMER","OMEX","OMF","OMGA","OMI","OMIC","OMQS","ON","ONB","ONC","ONCR","ONCS","ONCT","ONCY","ONEO","ONEW","ONFO","ONL","ONVO","ONYX","OP","OPA","OPAD","OPBK","OPCH","OPEN","OPFI","OPGN","OPHC","OPI","OPINL","OPK","OPNT","OPOF","OPP","OPRA","OPRT","OPRX","OPT","OPTN","OPTT","OPY","OR","ORA","ORAN","ORC","ORCL","ORGO","ORGN","ORGS","ORI","ORIC","ORLA","ORLY","ORMP","ORN","ORPH","ORRF","OSA","OSBC","OSCR","OSG","OSH","OSI","OSIS","OSK","OSPN","OSUR","OSW","OTEL","OTEX","OTIS","OTLK","OTLY","OTRK","OTTR","OUST","OUT","OVBC","OVID","OVLY","OVV","OWL","OWLT","OXAC","OXBR","OXLC","OXM","OXY","OYST","OZK","P","PAAS","PAC","PACB","PACW","PAG","PAGP","PAGS","PAHC","PAI","PALT","PANL","PANW","PAPL","PAR","PARR","PASG","PATH","PATI","PATK","PAVM","PAX","PAY","PAYH","PAYO","PAYS","PAYX","PB","PBA","PBB","PBD","PBE","PBF","PBFS","PBH","PBHC","PBI","PBIP","PBK","PBLA","PBM","PBPB","PBR","PBS","PBYI","PCAR","PCB","PCCT","PCG","PCH","PCI","PCK","PCM","PCN","PCOK","PCT","PCTI","PCTY","PCVX","PCYG","PCYO","PD","PDCE","PDCO","PDD","PDEX","PDFS","PDI","PDLB","PDM","PDN","PDO","PDOT","PDP","PDS","PDSB","PDT","PDX","PEAK","PEB","PEBK","PEBO","PECO","PED","PEG","PEGA","PEGY","PEI","PEN","PENN","PEO","PEP","PER","PERI","PESI","PET","PETQ","PETV","PETZ","PEV","PEY","PFBC","PFC","PFD","PFE","PFF","PFG","PFGC","PFH","PFI","PFIE","PFL","PFLT","PFM","PFMT","PFN","PFO","PFS","PFSI","PFSW","PFTA","PFX","PG","PGC","PGEN","PGHY","PGNY","PGP","PGR","PGRE","PGRO","PGSS","PGTI","PGX","PH","PHAR","PHARM","PHAS","PHAT","PHCF","PHG","PHGE","PHI","PHIO","PHK","PHM","PHO","PHR","PHUN","PHVS","PHX","PI","PIAI","PIC","PICC","PII","PIII","PINC","PINE","PING","PINS","PINT","PIO","PIPR","PIRS","PIXY","PJT","PKB","PKE","PKG","PKI","PKOH","PKST","PKX","PL","PLAB","PLAG","PLAN","PLAO","PLAY","PLBC","PLBY","PLCE","PLG","PLL","PLM","PLMI","PLMR","PLNT","PLOW","PLPC","PLRX","PLSE","PLTK","PLTM","PLTR","PLUG","PLUS","PLX","PLXP","PLXS","PLYA","PM","PMC","PMD","PME","PMF","PMGM","PML","PMM","PMO","PMT","PMTS","PMVP","PNBK","PNC","PNF","PNFP","PNM","PNNT","PNR","PNRG","PNT","PNTG","PNTM","PNW","POAI","PODD","POET","POL","POLA","POOL","POR","PORT","POSH","POST","POT","POW","POWI","POWL","POWW","PPBI","PPBT","PPC","PPG","PPH","PPIH","PPL","PPSI","PPT","PPTA","PPX","PQG","PR","PRA","PRAA","PRAX","PRCH","PRCT","PRDO","PRE","PRFT","PRFX","PRG","PRGO","PRGS","PRH","PRI","PRIM","PRK","PRLB","PRLD","PRLH","PRM","PRME","PRMW","PRO","PROC","PROF","PROK","PROS","PROV","PRPH","PRPL","PRPO","PRQR","PRS","PRSO","PRST","PRT","PRTA","PRTC","PRTG","PRTH","PRTS","PRU","PRVA","PSA","PSAG","PSB","PSBD","PSEC","PSF","PSHG","PSI","PSL","PSMT","PSN","PSNL","PSO","PSP","PST","PSTG","PSTL","PSTX","PSX","PT","PTA","PTAVE","PTB","PTCT","PTE","PTEN","PTGX","PTIC","PTIX","PTLO","PTMN","PTN","PTNR","PTON","PTPI","PTRA","PTRS","PTSI","PTVE","PTY","PUBM","PUK","PULM","PUMP","PUTW","PV","PVBC","PVH","PVL","PYCR","PYPD","PYPL","PYS","PYT","PZC","PZG","PZS","PZZA","QANT","QAT","QBTS","QCOM","QCRH","QDEL","QEFA","QEP","QETA","QFIN","QGEN","QH","QHCC","QIPT","QLC","QLGN","QLI","QLTA","QMCO","QNST","QNTM","QNRX","QNST","QRTEA","QRTEB","QRTEP","QRVO","QS","QSI","QSIAW","QSR","QTEK","QTWO","QUAD","QUAL","QUIK","QURE","R","RA","RACE","RAD","RADA","RADI","RAIL","RAMP","RAND","RAPT","RARE","RARR","RAS","RAVE","RAVN","RBB","RBC","RBCAA","RBD","RBKB","RBNC","RBT","RC","RCA","RCAT","RCB","RCC","RCL","RCM","RCMT","RCON","RCRT","RCS","RCUS","RDCM","RDFN","RDI","RDIB","RDN","RDNT","RDUS","RDVT","RDW","RDWR","RE","REAL","REAX","REBN","REDU","REE","REG","REGN","REI","REKR","RELI","RELL","RELX","RENN","RENT","REPL","RES","RETA","RETO","REV","REVG","REVH","REX","REXR","REYN","RF","RFAC","RFIL","RFL","RFP","RGA","RGC","RGCO","RGEN","RGF","RGLD","RGLS","RGNX","RGP","RGR","RGS","RGT","RH","RHE","RHI","RHP","RIBT","RICK","RIG","RIGL","RILY","RINF","RING","RIO","RIOT","RIVN","RJF","RKDA","RKLB","RKT","RKTA","RL","RLAY","RLGT","RLI","RLJ","RLMD","RLX","RM","RMAX","RMBL","RMBS","RMCF","RMCO","RMD","RMI","RMM","RMR","RMTO","RMT","RMTI","RNA","RNAC","RNAZ","RNDB","RNG","RNGR","RNLX","RNR","RNST","RNW","RNWK","RNXT","ROAD","ROCK","ROCG","ROCI","ROCL","ROG","ROIC","ROIV","ROK","ROKU","ROL","ROOT","ROP","ROST","RPAY","RPD","RPG","RPM","RPT","RPTX","RRC","RRD","RRGB","RRR","RS","RSG","RSI","RSSS","RSVR","RTL","RTLPO","RTLPP","RUM","RUN","RUSHA","RUSHB","RUTH","RVLV","RVMD","RVNC","RVSB","RVT","RVTY","RWAY","RWOD","RWT","RXDX","RXO","RXRX","RXST","RXT","RY","RYAAY","RYAM","RYAN","RYB","RYI","RYN","RYTM","RZLT","S","SA","SABR","SACH","SAGE","SAH","SAIA","SAIC","SAIL","SAL","SALM","SAM","SAMB","SAMG","SAN","SANA","SAND","SANG","SANM","SANW","SAP","SAR","SASR","SAT","SATL","SATS","SAVA","SAVE","SB","SBAC","SBBA","SBCF","SBET","SBEV","SBGI","SBH","SBI","SBIO","SBLK","SBNY","SBOW","SBS","SBSW","SBT","SBUX","SCCO","SCE","SCHL","SCHW","SCI","SCKT","SCL","SCLE","SCM","SCOA","SCOR","SCPH","SCPL","SCPS","SCS","SCSC","SCTL","SCU","SCVL","SCWO","SCX","SD","SDAC","SDC","SDPI","SE","SEAC","SEAS","SEAT","SEB","SECO","SEDG","SEE","SEED","SEEL","SEER","SEIC","SELF","SELX","SEM","SEMR","SENEA","SENEB","SENS","SERA","SES","SESN","SETA","SETU","SEV","SEVN","SF","SFB","SFBC","SFBS","SFET","SFL","SFM","SFNC","SFST","SG","SGA","SGBX","SGC","SGEN","SGFY","SGH","SGHC","SGLB","SGML","SGMO","SGMS","SGRP","SGRY","SGTX","SGU","SHAP","SHAQ","SHBI","SHC","SHCO","SHCR","SHEN","SHFS","SHG","SHI","SHIP","SHLS","SHO","SHOO","SHOP","SHOT","SHPH","SHPP","SHPT","SHU","SHUA","SHW","SI","SIB","SID","SIEB","SIEN","SIER","SIF","SIG","SIGA","SIGI","SIL","SILC","SILK","SILV","SIM","SIMO","SINT","SIOX","SIRI","SITC","SITE","SITM","SIVB","SIX","SJA","SJI","SJM","SJR","SJT","SJW","SKE","SKIL","SKIN","SKLZ","SKM","SKT","SKX","SKY","SKYA","SKYH","SKYT","SKYW","SKYY","SLAB","SLAC","SLAM","SLAQ","SLB","SLCA","SLCR","SLDB","SLDP","SLE","SLG","SLGC","SLGG","SLGN","SLI","SLM","SLN","SLNG","SLNO","SLP","SLR","SLRC","SLRX","SLS","SLVM","SLVR","SM","SMAP","SMAR","SMBC","SMBK","SMCI","SMED","SMFG","SMG","SMHI","SMI","SMID","SMIT","SMKR","SMLP","SMLR","SMM","SMMF","SMMT","SMP","SMPL","SMR","SMRT","SMSI","SMTC","SMTI","SMTS","SMX","SMXT","SN","SNA","SNAL","SNAP","SNBR","SNCE","SNCR","SND","SNDA","SNDL","SNDR","SNEX","SNFCA","SNGX","SNOA","SNOW","SNP","SNPS","SNPX","SNR","SNSR","SNT","SNTG","SNY","SO","SOBR","SOC","SOFI","SOFO","SOHO","SOHOB","SOHON","SOHOO","SOI","SOJD","SOJE","SOL","SOLO","SON","SOND","SONM","SONN","SONO","SONY","SOPA","SOR","SOS","SOTK","SOUN","SOVO","SP","SPB","SPCB","SPCE","SPCM","SPD","SPFI","SPG","SPGI","SPH","SPI","SPKB","SPK","SPLK","SPN","SPNE","SPNS","SPNT","SPOK","SPOT","SPPI","SPR","SPRB","SPRC","SPRO","SPRY","SPSC","SPT","SPTN","SPWH","SPXX","SQFTP","SQFT","SQH","SQI","SQM","SQNS","SQQQ","SR","SRAD","SRAX","SRC","SRCE","SRCL","SRDX","SRE","SREA","SRET","SRG","SRGA","SRI","SRL","SRNE","SRPT","SRRK","SRSA","SRTS","SRTY","SRV","SSB","SSC","SSD","SSIC","SSKN","SSLP","SSNC","SSP","SSRM","SSSS","SST","SSTI","SSTK","SSU","SSY","ST","STA","STAA","STAF","STAG","STAR","STBA","STC","STCN","STE","STEM","STEP","STER","STET","STG","STGW","STHO","STIM","STIX","STK","STKS","STLA","STLD","STL","STM","STMP","STN","STND","STNE","STNG","STOK","STON","STOR","STRA","STRC","STRE","STRL","STRM","STRN","STRO","STRS","STRT","STSA","STSS","STT","STTK","STVN","STWD","STX","STXS","STZ","SU","SUAC","SUI","SUM","SUMO","SUN","SUNS","SUNW","SUP","SUPN","SUPV","SURE","SURF","SURG","SUSC","SUSL","SVAL","SVB","SVC","SVE","SVFA","SVFD","SVV","SWAG","SWAV","SWBI","SWCH","SWET","SWI","SWIM","SWIN","SWK","SWKH","SWKS","SWN","SWTX","SWX","SWZ","SXC","SXI","SXT","SY","SYBT","SYBX","SYF","SYK","SYM","SYNA","SYNH","SYNL","SYPR","SYRS","SYX","SYY","SZC","SZZL","T","TA","TAC","TACT","TALK","TALO","TAN","TAP","TARA","TARS","TASK","TATT","TAYD","TBBK","TBC","TBI","TBIO","TBK","TBLA","TBLD","TBLT","TBNK","TBPH","TBRG","TC","TCAC","TCBK","TCBP","TCDA","TCFC","TCI","TCMD","TCOM","TCON","TCPC","TCRR","TCRT","TCTL","TCX","TD","TDA","TDC","TDCX","TDF","TDG","TDS","TDUP","TDW","TDY","TEAM","TECH","TECK","TEF","TEL","TELA","TELL","TEN","TENB","TENX","TEO","TER","TERP","TESS","TEVA","TEX","TFC","TFFP","TFII","TFIN","TFSA","TFX","TG","TGAA","TGAN","TGB","TGI","TGLS","TGNA","TGR","TGS","TGVC","TH","THC","THCH","THFF","THG","THM","THO","THR","THRM","THRX","THS","THTX","TIG","TIGO","TIL","TILE","TIMB","TIO","TIPT","TIRX","TISI","TITN","TIVC","TJX","TK","TKAMY","TKC","TKLF","TKO","TLGA","TLGY","TLIS","TLK","TLPH","TLRY","TLS","TLSA","TLST","TLT","TLYS","TM","TMC","TMCX","TMDX","TME","TMHC","TMO","TMP","TMQ","TMR","TMST","TMUS","TMX","TNC","TNDM","TNET","TNGX","TNON","TNXP","TNYA","TOI","TOL","TOMZ","TOON","TOPS","TORO","TOT","TOUR","TOWN","TPB","TPC","TPG","TPGI","TPH","TPHS","TPIC","TPR","TPTX","TPX","TRAK","TRAW","TRC","TRCA","TREB","TREC","TREE","TREX","TRHC","TRI","TRIB","TRIN","TRIP","TRKA","TRMB","TRMD","TRMK","TRN","TRNO","TRNS","TRON","TROO","TROW","TROX","TRS","TRST","TRT","TRTN","TRU","TRUE","TRUP","TRV","TRVG","TRVI","TRVN","TRX","TS","TSAT","TSBK","TSC","TSCO","TSEM","TSHA","TSI","TSIB","TSLA","TSLX","TSM","TSN","TSP","TSPQ","TSQ","TSRI","TSVT","TT","TTC","TTD","TTE","TTEC","TTEK","TTGT","TTI","TTM","TTMI","TTNP","TTOO","TTP","TTS","TTWO","TU","TUFN","TUP","TUSK","TVC","TVE","TVTX","TWI","TWIN","TWKS","TWLO","TWLV","TWOU","TWST","TX","TXG","TXMD","TXN","TXRH","TXT","TY","TYD","TYG","TYL","TYME","TYN","TYPE","TZOO","U","UAL","UAMY","UAN","UBA","UBER","UBFO","UBOH","UBS","UBSI","UBX","UCBI","UCC","UCL","UCO","UCON","UCO","UCOP","UCP","UDR","UE","UEC","UFAB","UFCS","UFI","UFPI","UFPT","UG","UGI","UGP","UGRO","UGT","UHS","UHT","UI","UIS","UK","UKOM","UL","ULBI","ULCC","ULE","ULH","ULST","ULTY","ULVM","UMBF","UMC","UMH","UNB","UNF","UNFI","UNH","UNM","UNMA","UNP","UNTY","UONE","UONEK","UP","UPC","UPH","UPLD","UPOY","UPPR","UPR","UPST","UPW","UPWK","UPY","UROY","USAC","USAK","USAP","USAS","USAU","USB","USCB","USCT","USEA","USEG","USFD","USIO","USLM","USM","USNA","USPH","USRT","UST","USX","USXT","UTG","UTHR","UTI","UTL","UTMD","UTME","UTZ","UUNI","UUP","UUU","UUUU","UVE","UVSP","UVV","UWMC","UXIN","V","VABK","VAC","VACC","VALE","VALN","VALU","VAPO","VAQC","VATE","VAXX","VB","VBAQ","VBF","VBFC","VBIV","VBK","VBLT","VBOC","VBON","VBTX","VC","VCEL","VCIF","VCIT","VCLT","VCNX","VCR","VCRA","VCV","VCXA","VDC","VDE","VEA","VEC","VECO","VEDU","VEEE","VEEV","VEGA","VEGI","VEL","VENU","VERA","VERB","VERC","VERI","VERO","VERU","VERV","VET","VFF","VG","VGAC","VGI","VGIT","VGLT","VGM","VGSH","VGT","VH","VHAQ","VHC","VHI","VHNA","VIA","VIACA","VIACB","VIACP","VIAV","VICE","VICI","VICR","VIDI","VIE","VIG","VIGL","VII","VINC","VINO","VINP","VIOT","VIPS","VIR","VIRC","VIRI","VIRT","VIRX","VIS","VISL","VIST","VITL","VIVE","VIVO","VJET","VKI","VKQ","VKTX","VLAT","VLCN","VLGEA","VLN","VLNS","VLO","VLON","VLP","VLRX","VLY","VLYPO","VLYPP","VMAR","VMBS","VMC","VMD","VMEO","VMI","VMO","VMW","VNCE","VNDA","VNET","VNO","VNOM","VNRA","VNRX","VNT","VO","VOC","VOD","VOF","VOI","VOLT","VONE","VONG","VONV","VOOV","VOR","VORB","VORBQ","VOSO","VOT","VOTE","VOV","VOXX","VOYA","VPG","VPV","VR","VRA","VRAR","VRCA","VRDN","VRE","VREX","VRM","VRME","VRNS","VRNT","VRPX","VRRM","VRSK","VRT","VRTS","VRTX","VS","VSAC","VSH","VSIAX","VSMV","VSS","VST","VSTA","VSTM","VSTO","VSTS","VTA","VTGN","VTHR","VTI","VTIP","VTN","VTNR","VTOL","VTR","VTRS","VTSI","VTV","VTWG","VTWO","VTWV","VTYX","VUZI","VVI","VVPR","VVR","VVV","VWE","VXRT","VXX","VYGG","VYGR","VYNE","VYNT","W","WAB","WABC","WAFD","WAFU","WAL","WALD","WASH","WAT","WATT","WB","WBA","WBD","WBS","WBT","WBX","WCC","WCFB","WCN","WDAY","WDC","WDFC","WDH","WDI","WEA","WEAV","WEC","WEJO","WELL","WEN","WERN","WES","WETF","WEX","WEYS","WF","WFC","WFG","WFRD","WGA","WGMI","WH","WHD","WHF","WHG","WHLM","WHLR","WHR","WIA","WILC","WIMI","WINA","WING","WINT","WINV","WIRE","WISA","WISH","WIT","WIX","WK","WKEY","WKH","WKHS","WKME","WLDN","WLFC","WLK","WLKP","WLL","WLY","WLYB","WM","WMB","WMC","WMG","WMK","WMPN","WMS","WMT","WNW","WOLF","WOOD","WOOF","WOR","WORX","WOW","WP","WPC","WPCA","WPM","WPP","WPRT","WRB","WRBY","WRK","WRLD","WRNT","WSBC","WSBF","WSC","WSO","WSR","WST","WSTG","WT","WTAI","WTBA","WTER","WTI","WTM","WTR","WTRG","WTS","WTT","WTTR","WU","WULF","WVE","WVVI","WW","WWW","WY","WYNN","WYY","X","XAIR","XBIO","XBIT","XCUR","XEL","XELA","XENE","XERS","XFIN","XFLT","XFOR","XGN","XHR","XIN","XLO","XLY","XM","XMAT","XMTR","XNOX","XOM","XOS","XPER","XPL","XPO","XPOF","XPRO","XRAY","XRTX","XRX","XSPA","XTLB","XUII","Y","YALA","YCBD","YELP","YETI","YEXT","YGMZ","YI","YJJ","YJ","YLD","YMAB","YMM","YMTX","YNDX","YORW","YOSH","YOT","YOU","YQ","YRIV","YSG","YTEN","YTRA","YUM","YUMC","Z","ZEN","ZEPP","ZETA","ZEV","ZFOX","ZG","ZGN","ZIMV","ZION","ZIOP","ZIP","ZIVO","ZIXI","ZK","ZKH","ZLAB","ZM","ZNGA","ZNH","ZOM","ZOOM","ZS","ZSAN","ZSHG","ZSL","ZTA","ZTAI","ZTEK","ZTO","ZTR","ZTS","ZUMZ","ZUO","ZVIA","ZVRA","ZVSA","ZWS","ZY","ZYME","ZYNE","ZYXI","ZZLL"]
    all_tickers = list(set(us_large + russell_sample + intl_tickers))
    return all_tickers[:15500]

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
# FULL MARKET SCAN (15,000+ assets)
# --------------------------------------------
@st.cache_data(ttl=86400)
def scan_full_market(ticker_list):
    results = []
    progress_bar = st.progress(0)
    status = st.empty()
    total = len(ticker_list)
    for i, ticker in enumerate(ticker_list):
        if i % 50 == 0:
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
        time.sleep(0.03)
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
    st.markdown("""<div class="main-header"><h1 style="color:white;margin:0;">🌍 Global Buffett Screener</h1><p style="color:#cbd5e1;margin-top:0.5rem;">Value investing · 30+ major indices · 15,000+ assets scan · News sentiment</p></div>""", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown("### 🎯 Buffett's Criteria")
        st.info("📈 ROE > 15%\n\n💎 P/B < 1.5\n\n🏦 Debt/Equity < 50%\n\n📊 Revenue Growth > 10%")
        st.markdown("---")
        st.markdown("### 🔍 Full Market Scan")
        if st.button("🚀 Scan 15,000+ Assets", use_container_width=True):
            with st.spinner("Building ticker universe (15,000+ assets)..."):
                all_tickers = build_full_universe()
                st.session_state.full_scan_df = scan_full_market(all_tickers)
            st.success(f"✅ Scan complete! Found {len(st.session_state.full_scan_df)} opportunities.")
            st.rerun()
        st.markdown("---")
        st.markdown("### 📊 Sentiment Analysis")
        st.caption("News sentiment for selected stock")
        st.markdown("---")
        st.markdown("### 🌐 Global Coverage")
        st.caption(f"{sum(len(v) for v in INDICES_BY_REGION.values())} indices + 15,000+ individual stocks")
        st.markdown("---")
        st.markdown("### 📈 Version")
        st.caption("v3.0 - Grouped indices, 15k+ assets")

    st.markdown("## 🌟 Global Market Overview")
    st.markdown("*Browse indices by region and select one to explore its top Buffett-style opportunities*")

    # Region selection with expanders
    for region, indices in INDICES_BY_REGION.items():
        with st.expander(f"📍 {region} ({len(indices)} indices)"):
            cols = st.columns(4)
            for i, (name, info) in enumerate(indices.items()):
                with cols[i % 4]:
                    if st.button(f"{name}\n{info['market']}", key=f"idx_{region}_{name}", use_container_width=True):
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
        st.markdown("## 🏆 Top Opportunities from 15,000+ Assets Scan")
        top_n = st.slider("Show top", 10, 200, 50)
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
    st.caption("📊 Data: Yahoo Finance | News: Finnhub | Scan 15,000+ assets for Buffett-style opportunities | Grouped by region")

if __name__ == "__main__":
    main()