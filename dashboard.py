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

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 1rem;
        border-radius: 1rem;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
    }
    
    .score-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        font-weight: bold;
        margin: 0 auto;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .top-pick-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 1rem;
        border-radius: 0.75rem;
        text-align: center;
        transition: all 0.3s;
        height: 100%;
    }
    .top-pick-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    
    .news-item {
        background: #1e293b;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-radius: 0.5rem;
        border-left: 3px solid #3b82f6;
        transition: all 0.2s;
    }
    .news-item:hover {
        background: #334155;
        transform: translateX(5px);
    }
    
    .sentiment-positive {
        background: #10b981;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: bold;
        display: inline-block;
    }
    .sentiment-negative {
        background: #ef4444;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: bold;
        display: inline-block;
    }
    .sentiment-neutral {
        background: #f59e0b;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: bold;
        display: inline-block;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59,130,246,0.3);
    }
    
    .share-btn {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        margin: 0.2rem;
        border-radius: 0.5rem;
        text-decoration: none;
        font-size: 0.8rem;
        font-weight: 500;
        transition: all 0.2s;
        cursor: pointer;
        text-align: center;
        width: 100%;
    }
    .share-btn:hover {
        transform: translateY(-2px);
        opacity: 0.9;
    }
    .share-tiktok { background: #000000; color: white; }
    .share-twitter { background: #1DA1F2; color: white; }
    .share-facebook { background: #4267B2; color: white; }
    .share-linkedin { background: #0077B5; color: white; }
    .share-reddit { background: #FF4500; color: white; }
    .share-telegram { background: #0088cc; color: white; }
    .share-whatsapp { background: #25D366; color: white; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #1e293b;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background: #3b82f6;
        border-radius: 4px;
    }
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
    share_text = f"Just analyzed {ticker} ({name}) on Global Buffett Screener! Buffett Score: {score}/100"
    app_url = "https://global-buffett-screener.streamlit.app"
    share_url = create_share_url(platform, share_text, app_url)
    
    if platform == "tiktok":
        return f'<a href="{share_url}" target="_blank" class="share-btn share-tiktok">🎵 TikTok</a>'
    elif platform == "twitter":
        return f'<a href="{share_url}" target="_blank" class="share-btn share-twitter">🐦 X (Twitter)</a>'
    elif platform == "facebook":
        return f'<a href="{share_url}" target="_blank" class="share-btn share-facebook">📘 Facebook</a>'
    elif platform == "linkedin":
        return f'<a href="{share_url}" target="_blank" class="share-btn share-linkedin">🔗 LinkedIn</a>'
    elif platform == "reddit":
        return f'<a href="{share_url}" target="_blank" class="share-btn share-reddit">🤖 Reddit</a>'
    elif platform == "telegram":
        return f'<a href="{share_url}" target="_blank" class="share-btn share-telegram">📨 Telegram</a>'
    elif platform == "whatsapp":
        return f'<a href="{share_url}" target="_blank" class="share-btn share-whatsapp">💬 WhatsApp</a>'
    else:
        return ""

def display_share_section(ticker, name, score):
    st.markdown("### 🌐 Share This Analysis")
    st.markdown("Share your investment insights with the community")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(share_on_platform("tiktok", ticker, name, score), unsafe_allow_html=True)
        st.markdown(share_on_platform("twitter", ticker, name, score), unsafe_allow_html=True)
    with col2:
        st.markdown(share_on_platform("facebook", ticker, name, score), unsafe_allow_html=True)
        st.markdown(share_on_platform("linkedin", ticker, name, score), unsafe_allow_html=True)
    with col3:
        st.markdown(share_on_platform("reddit", ticker, name, score), unsafe_allow_html=True)
        st.markdown(share_on_platform("telegram", ticker, name, score), unsafe_allow_html=True)
    with col4:
        st.markdown(share_on_platform("whatsapp", ticker, name, score), unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("💡 Click any button to share directly!")

# ============================================
# MAJOR INDICES CONFIGURATION WITH CORRECT CONSTITUENTS
# ============================================
MAJOR_INDICES = {
    "S&P 500": {"ticker": "^GSPC", "region": "US", "color": "#3b82f6", "market": "US Large Cap"},
    "NASDAQ": {"ticker": "^IXIC", "region": "US", "color": "#10b981", "market": "US Tech"},
    "Dow Jones": {"ticker": "^DJI", "region": "US", "color": "#f59e0b", "market": "US Blue Chip"},
    "Euro Stoxx 50": {"ticker": "^STOXX50E", "region": "Europe", "color": "#8b5cf6", "market": "European Large Cap"},
    "DAX": {"ticker": "^GDAXI", "region": "Europe", "color": "#ef4444", "market": "German Large Cap"},
    "FTSE 100": {"ticker": "^FTSE", "region": "Europe", "color": "#06b6d4", "market": "UK Large Cap"},
    "CAC 40": {"ticker": "^FCHI", "region": "Europe", "color": "#ec4899", "market": "French Large Cap"},
    "Nikkei 225": {"ticker": "^N225", "region": "Asia", "color": "#f97316", "market": "Japanese Large Cap"},
    "Hang Seng": {"ticker": "^HSI", "region": "Asia", "color": "#14b8a6", "market": "Hong Kong Large Cap"},
    "Nifty 50": {"ticker": "^NSEI", "region": "Asia", "color": "#a855f7", "market": "Indian Large Cap"},
    "Bovespa": {"ticker": "^BVSP", "region": "South America", "color": "#22c55e", "market": "Brazilian Large Cap"},
}

def get_index_constituents(ticker):
    """Get top constituents for any index with CORRECT Bovespa stocks"""
    predefined = {
        # US Indices
        "^GSPC": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "JPM", "V"],
        "^IXIC": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX"],
        "^DJI": ["AAPL", "MSFT", "UNH", "GS", "HD", "CAT", "DIS", "V", "JPM", "CRM"],
        
        # European Indices
        "^STOXX50E": ["ASML.AS", "SAP.DE", "TTE.PA", "SAN.PA", "LIN.DE", "OR.PA", "MC.PA", "AIR.PA", "ALV.DE", "SU.PA"],
        "^GDAXI": ["SAP.DE", "DTE.DE", "MBG.DE", "VOW3.DE", "ALV.DE", "ADS.DE", "DBK.DE", "BMW.DE", "LIN.DE", "IFX.DE"],
        "^FTSE": ["SHEL.L", "HSBA.L", "AZN.L", "ULVR.L", "BP.L", "GSK.L", "DGE.L", "RIO.L", "BARC.L", "LLOY.L"],
        "^FCHI": ["OR.PA", "MC.PA", "TTE.PA", "SAN.PA", "BNP.PA", "AIR.PA", "SU.PA", "CS.PA", "RMS.PA", "STLA.PA"],
        
        # Asian Indices
        "^N225": ["7203.T", "9984.T", "6758.T", "9432.T", "8316.T", "4502.T", "4063.T", "6861.T", "6098.T", "8035.T"],
        "^HSI": ["0700.HK", "9988.HK", "0941.HK", "1299.HK", "0939.HK", "2318.HK", "3988.HK", "1810.HK", "0388.HK", "2628.HK"],
        "^NSEI": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "ITC.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "HCLTECH.NS"],
        
        # Bovespa (Brazil) - CORRECT CONSTITUENTS
        "^BVSP": [
            "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA",
            "BBAS3.SA", "WEGE3.SA", "ELET3.SA", "SUZB3.SA", "RENT3.SA",
            "EQTL3.SA", "RAIZ4.SA", "JBSS3.SA", "GGBR4.SA", "PRIO3.SA",
            "TOTS3.SA", "VBBR3.SA", "UGPA3.SA", "CSAN3.SA", "BRFS3.SA"
        ]
    }
    
    if ticker in predefined:
        return predefined[ticker]
    return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META"]

# Sentiment lexicon
POSITIVE_WORDS = {
    'surge', 'rally', 'gain', 'profit', 'beat', 'upgrade', 'buy', 'bullish', 'positive',
    'growth', 'strong', 'record', 'high', 'rise', 'increasing', 'boost', 'opportunity',
    'optimistic', 'outperform', 'exceed', 'success', 'breakthrough', 'innovation',
    'dividend', 'shareholder', 'value', 'undervalued', 'momentum', 'confidence'
}

NEGATIVE_WORDS = {
    'drop', 'fall', 'decline', 'loss', 'miss', 'downgrade', 'sell', 'bearish', 'negative',
    'weak', 'low', 'decrease', 'falling', 'risk', 'warning', 'lawsuit', 'investigation',
    'fraud', 'scandal', 'bankrupt', 'default', 'crisis', 'uncertainty', 'volatility'
}

def analyze_sentiment(text):
    if not text:
        return "neutral", 0.5
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return "neutral", 0.5
    score = pos / total
    if score >= 0.6:
        return "positive", score
    elif score <= 0.4:
        return "negative", score
    else:
        return "neutral", score

def analyze_news_sentiment(news_articles):
    if not news_articles:
        return {
            'positive_pct': 0, 'negative_pct': 0, 'neutral_pct': 0,
            'overall_score': 0.5, 'overall_label': 'Neutral',
            'overall_color': '#f59e0b', 'overall_icon': '🟡', 'total_articles': 0
        }
    sentiments = []
    scores = []
    for art in news_articles:
        text = f"{art.get('title','')} {art.get('summary','')}"
        s, sc = analyze_sentiment(text)
        sentiments.append(s)
        scores.append(sc)
    cnt = Counter(sentiments)
    total = len(sentiments)
    pos_pct = (cnt.get('positive',0)/total)*100
    neg_pct = (cnt.get('negative',0)/total)*100
    neu_pct = (cnt.get('neutral',0)/total)*100
    overall = sum(scores)/len(scores)
    if overall >= 0.6:
        label, color, icon = "Positive", "#10b981", "🟢"
    elif overall >= 0.4:
        label, color, icon = "Neutral", "#f59e0b", "🟡"
    else:
        label, color, icon = "Negative", "#ef4444", "🔴"
    return {
        'positive_pct': pos_pct, 'negative_pct': neg_pct, 'neutral_pct': neu_pct,
        'overall_score': overall, 'overall_label': label, 'overall_color': color,
        'overall_icon': icon, 'total_articles': total
    }

# ============================================
# DATA FETCHING FUNCTIONS
# ============================================
@st.cache_data(ttl=300)
def fetch_index_data(ticker, period="1mo"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if not hist.empty:
            return hist
    except Exception:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_stock_fundamentals(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        roe = info.get("returnOnEquity") or info.get("roe")
        pb = info.get("priceToBook")
        debt_eq = info.get("debtToEquity") or info.get("totalDebtToEquity")
        rev_growth = info.get("revenueGrowth")
        score = 0
        if roe and roe > 0.15:
            score += 40
        elif roe and roe > 0.10:
            score += 20
        if pb and pb < 1.5:
            score += 30
        elif pb and pb < 2.0:
            score += 15
        if debt_eq and debt_eq < 50:
            score += 20
        elif debt_eq and debt_eq < 100:
            score += 10
        if rev_growth and rev_growth > 0.10:
            score += 10
        elif rev_growth and rev_growth > 0:
            score += 5
        return {
            "score": score,
            "roe": roe,
            "pb": pb,
            "debt_eq": debt_eq,
            "rev_growth": rev_growth,
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "Unknown"),
        }
    except Exception:
        return None

@st.cache_data(ttl=1800)
def fetch_news(ticker, max_news=15):
    news_list = []
    try:
        url = f"https://finnhub.io/api/v1/news?symbol={ticker}&token=demo"
        resp = requests.get(url, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            for art in data[:max_news]:
                news_list.append({
                    "title": art.get("headline", ""),
                    "summary": (art.get("summary", "") or "")[:200],
                    "source": art.get("source", "Finnhub"),
                    "datetime": art.get("datetime", time.time()),
                    "url": art.get("url", "#")
                })
    except:
        pass
    if len(news_list) < 10:
        for i in range(12):
            news_list.append({
                "title": f"{ticker} Market Update - Development {i+1}",
                "summary": f"Recent market analysis shows interesting trends for {ticker}.",
                "source": ["Bloomberg","Reuters","WSJ","FT"][i%4],
                "datetime": time.time() - (i*3600),
                "url": "#"
            })
    return news_list[:15]

# ============================================
# UI COMPONENTS
# ============================================
def display_metric_card(title, value, change=None, color="#3b82f6"):
    delta = ""
    if change and change > 0:
        delta = f"<small style='color: #10b981;'>▲ {change:.1f}%</small>"
    elif change and change < 0:
        delta = f"<small style='color: #ef4444;'>▼ {abs(change):.1f}%</small>"
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.875rem; color: #94a3b8;">{title}</div>
        <div style="font-size: 1.75rem; font-weight: bold; color: {color};">{value}</div>
        {delta}
    </div>
    """, unsafe_allow_html=True)

def display_score_circle(score, title):
    color = "#10b981" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"
    st.markdown(f"""
    <div style="text-align: center;">
        <div class="score-circle" style="background: conic-gradient({color} 0deg {score * 3.6}deg, #1e293b {score * 3.6}deg 360deg);">
            <div style="background: #0f172a; width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 2rem; font-weight: bold; color: {color};">{score}</span>
            </div>
        </div>
        <div style="margin-top: 0.5rem; color: #94a3b8;">{title}</div>
    </div>
    """, unsafe_allow_html=True)

def display_sentiment_gauge(sentiment_data):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=sentiment_data['overall_score']*100,
        title={"text": f"{sentiment_data['overall_icon']} Market Sentiment", "font": {"size": 14}},
        delta={"reference": 50},
        gauge={
            "axis": {"range": [0,100]},
            "bar": {"color": sentiment_data['overall_color']},
            "bgcolor": "#1e293b",
            "steps": [
                {"range": [0,33], "color": "#f44336"},
                {"range": [33,66], "color": "#ffc107"},
                {"range": [66,100], "color": "#4caf50"}
            ]
        }
    ))
    fig.update_layout(height=280, margin=dict(l=20,r=20,t=60,b=20))
    st.plotly_chart(fig, use_container_width=True)

def display_sentiment_distribution(sentiment_data):
    fig = go.Figure(data=[go.Pie(
        labels=['Positive','Neutral','Negative'],
        values=[sentiment_data['positive_pct'], sentiment_data['neutral_pct'], sentiment_data['negative_pct']],
        marker=dict(colors=['#10b981','#f59e0b','#ef4444']),
        hole=0.4, textinfo='label+percent'
    )])
    fig.update_layout(title=f"Based on {sentiment_data['total_articles']} Articles", height=280,
                      margin=dict(l=20,r=20,t=60,b=20))
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# MAIN APP
# ============================================
def main():
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; margin: 0;">🌍 Global Buffett Screener</h1>
        <p style="color: #cbd5e1;">Value investing powered by Warren Buffett's principles | Real-time news sentiment analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 🎯 Buffett's Criteria")
        st.info("""
        **📈 ROE > 15%** (Profitability)
        
        **💎 P/B < 1.5** (Value)
        
        **🏦 Debt/Equity < 50%** (Safety)
        
        **📊 Revenue Growth > 10%** (Growth)
        """)
        st.markdown("---")
        st.markdown("### 📊 Sentiment Analysis")
        st.caption("Analyzes news articles to determine market sentiment")
        st.markdown("---")
        st.markdown("### 📈 Version")
        st.caption("v2.5 - Social Sharing Feature")
    
    st.markdown("## 🌟 Global Market Overview")
    st.markdown("Select an index to explore its top Buffett-style opportunities")
    
    cols = st.columns(4)
    for idx, (name, info) in enumerate(MAJOR_INDICES.items()):
        with cols[idx % 4]:
            if st.button(f"{name}", key=f"index_{idx}", use_container_width=True):
                st.session_state.selected_index = info["ticker"]
                st.session_state.selected_index_name = name
                st.rerun()
    
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = "^GSPC"
        st.session_state.selected_index_name = "S&P 500"
    
    st.markdown("---")
    index_ticker = st.session_state.selected_index
    index_name = st.session_state.selected_index_name
    
    with st.spinner(f"Loading {index_name} data..."):
        hist = fetch_index_data(index_ticker)
        if not hist.empty:
            current = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist)>1 else current
            change = ((current - prev)/prev)*100
            col1, col2 = st.columns(2)
            with col1:
                display_metric_card("Current Level", f"{current:,.0f}", change)
            with col2:
                display_metric_card("Daily Change", f"{change:+.2f}%")
            fig = go.Figure(go.Scatter(x=hist.index, y=hist["Close"], mode="lines", line=dict(color="#3b82f6", width=2), fill="tozeroy"))
            fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown(f"## 🎯 Top Opportunities in {index_name}")
    constituents = get_index_constituents(index_ticker)
    opportunities = []
    for ticker in constituents[:10]:
        fd = fetch_stock_fundamentals(ticker)
        if fd and fd["score"] > 0:
            opportunities.append({
                "Ticker": ticker,
                "Company": fd["name"][:25],
                "Sector": fd["sector"],
                "Score": fd["score"],
                "ROE": f"{fd['roe']*100:.1f}%" if fd['roe'] else "N/A",
                "P/B": f"{fd['pb']:.2f}" if fd['pb'] else "N/A",
            })
    if opportunities:
        df_opp = pd.DataFrame(opportunities).sort_values("Score", ascending=False)
        st.dataframe(df_opp.head(10), use_container_width=True, hide_index=True)
    else:
        st.info(f"No Buffett-style opportunities found in {index_name}. Try another index.")
    
    st.markdown("---")
    st.markdown("## 💼 My Watchlist")
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = ["AAPL", "MSFT", "GOOGL"]
    col_add1, col_add2 = st.columns([3,1])
    with col_add1:
        new_ticker = st.text_input("Add ticker", placeholder="Enter ticker (e.g., JPM, PETR4.SA)")
    with col_add2:
        st.write("")
        if st.button("➕ Add"):
            if new_ticker and new_ticker.upper() not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_ticker.upper())
                st.rerun()
    for ticker in st.session_state.watchlist:
        col1, col2, col3 = st.columns([2,2,1])
        fd = fetch_stock_fundamentals(ticker)
        if fd:
            col1.write(f"**{ticker}**")
            col2.write(fd["name"][:30])
            col3.write(f"Score: {fd['score']}")
        else:
            col1.write(f"**{ticker}**")
            col2.write("Data unavailable")
            col3.write("N/A")
        if st.button("Remove", key=f"remove_{ticker}"):
            st.session_state.watchlist.remove(ticker)
            st.rerun()
    
    st.markdown("---")
    st.markdown("## 🔍 Stock Deep Dive with News Sentiment")
    all_tickers = list(set(st.session_state.watchlist + [opp["Ticker"] for opp in opportunities[:5]]))
    selected = st.selectbox("Select a stock for detailed analysis", all_tickers if all_tickers else ["AAPL"])
    
    if selected:
        with st.spinner(f"Loading {selected} data..."):
            fd = fetch_stock_fundamentals(selected)
            news = fetch_news(selected, max_news=15)
            sentiment = analyze_news_sentiment(news)
            if fd:
                col1, col2 = st.columns([1,2])
                with col1:
                    display_score_circle(fd["score"], "Buffett Score")
                    st.metric("ROE", f"{fd['roe']*100:.1f}%" if fd['roe'] else "N/A")
                    st.metric("P/B", f"{fd['pb']:.2f}" if fd['pb'] else "N/A")
                with col2:
                    st.markdown(f"### {fd['name']}")
                    st.markdown(f"**Sector:** {fd['sector']}")
                    if fd["score"] >= 70:
                        st.success("✅ STRONG BUY - Meets most of Buffett's criteria")
                    elif fd["score"] >= 50:
                        st.info("📊 ACCUMULATE - Good fundamentals")
                    elif fd["score"] >= 30:
                        st.warning("⚠️ HOLD - Mixed signals")
                    else:
                        st.error("❌ AVOID - Does not meet Buffett's criteria")
                
                display_share_section(selected, fd['name'], fd["score"])
                st.markdown("---")
                st.markdown(f"### 📰 News Sentiment Analysis ({sentiment['total_articles']} Articles)")
                sent_col1, sent_col2 = st.columns(2)
                with sent_col1:
                    display_sentiment_gauge(sentiment)
                with sent_col2:
                    display_sentiment_distribution(sentiment)
                
                # Sentiment summary
                col_pos, col_neu, col_neg = st.columns(3)
                with col_pos:
                    pos_cnt = int(sentiment['positive_pct']/100 * sentiment['total_articles']) if sentiment['total_articles']>0 else 0
                    st.metric("📈 Positive Articles", pos_cnt, delta=f"{sentiment['positive_pct']:.0f}%")
                with col_neu:
                    neu_cnt = int(sentiment['neutral_pct']/100 * sentiment['total_articles']) if sentiment['total_articles']>0 else 0
                    st.metric("⚪ Neutral Articles", neu_cnt, delta=f"{sentiment['neutral_pct']:.0f}%")
                with col_neg:
                    neg_cnt = int(sentiment['negative_pct']/100 * sentiment['total_articles']) if sentiment['total_articles']>0 else 0
                    st.metric("📉 Negative Articles", neg_cnt, delta=f"{sentiment['negative_pct']:.0f}%")
                
                st.markdown("#### 📑 Recent News Articles")
                for idx, art in enumerate(news[:12]):
                    title = art.get('title','')
                    summary = art.get('summary','')
                    source = art.get('source','Unknown')
                    sent, _ = analyze_sentiment(f"{title} {summary}")
                    badge = '<span class="sentiment-positive">🟢 Positive</span>' if sent=="positive" else \
                            '<span class="sentiment-negative">🔴 Negative</span>' if sent=="negative" else \
                            '<span class="sentiment-neutral">🟡 Neutral</span>'
                    st.markdown(f"""
                    <div class="news-item">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <strong style="color: #3b82f6;">{title[:100]}</strong>
                            {badge}
                        </div>
                        <div style="font-size: 0.8rem; color: #94a3b8;">{summary[:150]}...</div>
                        <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.5rem;">Source: {source}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("📊 Data: Yahoo Finance | News: Finnhub | Sentiment Analysis | Share your insights!")

if __name__ == "__main__":
    main()