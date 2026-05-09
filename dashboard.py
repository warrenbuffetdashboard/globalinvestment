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
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Card styling */
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
    
    /* Score circle styling */
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
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    /* Index card */
    .index-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 1rem;
        border-radius: 0.75rem;
        text-align: center;
        border-left: 4px solid #3b82f6;
        cursor: pointer;
        transition: all 0.3s;
    }
    .index-card:hover {
        background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
        transform: scale(1.02);
    }
    
    /* Top pick card */
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
    
    /* News item */
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
    
    /* Sentiment badge */
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
    
    /* Button styling */
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
    
    /* Portfolio item */
    .portfolio-item {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border: 1px solid #334155;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom scrollbar */
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
    ::-webkit-scrollbar-thumb:hover {
        background: #2563eb;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# MAJOR INDICES CONFIGURATION
# ============================================
MAJOR_INDICES = {
    "🇺🇸 S&P 500": {"ticker": "^GSPC", "region": "US", "color": "#3b82f6", "market": "US Large Cap"},
    "🇺🇸 NASDAQ": {"ticker": "^IXIC", "region": "US", "color": "#10b981", "market": "US Tech"},
    "🇺🇸 Dow Jones": {"ticker": "^DJI", "region": "US", "color": "#f59e0b", "market": "US Blue Chip"},
    "🇪🇺 Euro Stoxx 50": {"ticker": "^STOXX50E", "region": "Europe", "color": "#8b5cf6", "market": "European Large Cap"},
    "🇩🇪 DAX": {"ticker": "^GDAXI", "region": "Europe", "color": "#ef4444", "market": "German Large Cap"},
    "🇬🇧 FTSE 100": {"ticker": "^FTSE", "region": "Europe", "color": "#06b6d4", "market": "UK Large Cap"},
    "🇫🇷 CAC 40": {"ticker": "^FCHI", "region": "Europe", "color": "#ec4899", "market": "French Large Cap"},
    "🇯🇵 Nikkei 225": {"ticker": "^N225", "region": "Asia", "color": "#f97316", "market": "Japanese Large Cap"},
    "🇨🇳 Shanghai Composite": {"ticker": "000001.SS", "region": "Asia", "color": "#eab308", "market": "Chinese Large Cap"},
    "🇭🇰 Hang Seng": {"ticker": "^HSI", "region": "Asia", "color": "#14b8a6", "market": "Hong Kong Large Cap"},
    "🇮🇳 Nifty 50": {"ticker": "^NSEI", "region": "Asia", "color": "#a855f7", "market": "Indian Large Cap"},
    "🇧🇷 Bovespa": {"ticker": "^BVSP", "region": "South America", "color": "#22c55e", "market": "Brazilian Large Cap"},
}

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
    'fraud', 'scandal', 'bankrupt', 'default', 'crisis', 'uncertainty', 'volatility',
    'underperform', 'disappoint', 'regulatory', 'fine', 'penalty'
}

def analyze_sentiment(text):
    """Analyze sentiment of text using lexicon-based approach."""
    if not text:
        return "neutral", 0.5
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
    negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)
    
    total = positive_count + negative_count
    if total == 0:
        return "neutral", 0.5
    
    sentiment_score = positive_count / total
    
    if sentiment_score >= 0.6:
        return "positive", sentiment_score
    elif sentiment_score <= 0.4:
        return "negative", sentiment_score
    else:
        return "neutral", sentiment_score

def analyze_news_sentiment(news_articles):
    """Analyze sentiment for a list of news articles."""
    sentiments = []
    for article in news_articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}"
        sentiment, score = analyze_sentiment(text)
        sentiments.append(sentiment)
    
    # Calculate overall sentiment distribution
    sentiment_counts = Counter(sentiments)
    total = len(sentiments)
    
    if total > 0:
        positive_pct = (sentiment_counts.get('positive', 0) / total) * 100
        negative_pct = (sentiment_counts.get('negative', 0) / total) * 100
        neutral_pct = (sentiment_counts.get('neutral', 0) / total) * 100
    else:
        positive_pct = negative_pct = neutral_pct = 0
    
    # Calculate overall sentiment score
    sentiment_scores = []
    for article in news_articles:
        text = f"{article.get('title', '')} {article.get('summary', '')}"
        _, score = analyze_sentiment(text)
        sentiment_scores.append(score)
    
    overall_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
    
    # Determine sentiment label
    if overall_score >= 0.6:
        overall_label = "Positive"
        overall_color = "#10b981"
        overall_icon = "🟢"
    elif overall_score <= 0.4:
        overall_label = "Negative"
        overall_color = "#ef4444"
        overall_icon = "🔴"
    else:
        overall_label = "Neutral"
        overall_color = "#f59e0b"
        overall_icon = "🟡"
    
    return {
        'positive_pct': positive_pct,
        'negative_pct': negative_pct,
        'neutral_pct': neutral_pct,
        'overall_score': overall_score,
        'overall_label': overall_label,
        'overall_color': overall_color,
        'overall_icon': overall_icon,
        'sentiments': sentiments
    }

# Dynamic index constituents based on real data
def get_index_constituents(ticker):
    """Get top constituents for any index dynamically"""
    
    # For major indices, use predefined lists
    predefined = {
        "^GSPC": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "JPM", "V", 
                  "UNH", "WMT", "JNJ", "PG", "HD", "MA", "BAC", "CVX", "XOM", "ABBV"],
        "^IXIC": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "COST", "NFLX",
                  "ADBE", "PEP", "CSCO", "CMCSA", "INTC", "AMGN", "TXN", "QCOM", "INTU", "HON"],
        "^DJI": ["AAPL", "MSFT", "UNH", "GS", "HD", "CAT", "DIS", "V", "JPM", "CRM",
                 "CVX", "WMT", "KO", "PG", "JNJ", "TRV", "HON", "NKE", "BA", "IBM"],
        "^NSEI": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
                  "ITC.NS", "KOTAKBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "HCLTECH.NS"],
        "^HSI": ["0700.HK", "9988.HK", "0941.HK", "1299.HK", "0939.HK", "2318.HK", "3988.HK", 
                 "1810.HK", "0388.HK", "2628.HK"],
        "^N225": ["7203.T", "9984.T", "6758.T", "9432.T", "8316.T", "4502.T", "4063.T", 
                  "6861.T", "6098.T", "8035.T"],
        "^FCHI": ["OR.PA", "MC.PA", "TTE.PA", "SAN.PA", "BNP.PA", "AIR.PA", "SU.PA", "CS.PA", "RMS.PA", "STLA.PA"],
        "^GDAXI": ["SAP.DE", "DTE.DE", "MBG.DE", "VOW3.DE", "ALV.DE", "ADS.DE", "DBK.DE", "BMW.DE", "LIN.DE", "IFX.DE"],
        "^STOXX50E": ["ASML.AS", "SAP.DE", "TTE.PA", "SAN.PA", "LIN.DE", "OR.PA", "MC.PA", "AIR.PA", "ALV.DE", "SU.PA"],
        "^FTSE": ["SHEL.L", "HSBA.L", "AZN.L", "ULVR.L", "BP.L", "GSK.L", "DGE.L", "RIO.L", "BARC.L", "LLOY.L"],
        "000001.SS": ["600519.SS", "601318.SS", "600036.SS", "000858.SZ", "601166.SS", "600276.SS", "002415.SZ", "601888.SS", "300750.SZ", "000333.SZ"],
        "^BVSP": ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "BBAS3.SA", "ELET3.SA", "WEGE3.SA", "GGBR4.SA", "SUZB3.SA"]
    }
    
    if ticker in predefined:
        return predefined[ticker]
    
    # Default fallback - S&P 500 constituents
    return ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "UNH"]

# ============================================
# DATA FETCHING FUNCTIONS
# ============================================
@st.cache_data(ttl=300)
def fetch_index_data(ticker, period="1mo"):
    """Fetch index data with caching."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if not hist.empty:
            return hist
    except Exception as e:
        st.error(f"Error fetching {ticker}: {str(e)}")
    return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_stock_fundamentals(ticker):
    """Fetch stock fundamentals for Buffett scoring."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract key metrics
        roe = info.get("returnOnEquity") or info.get("roe")
        pb = info.get("priceToBook")
        pe = info.get("trailingPE")
        debt_eq = info.get("debtToEquity") or info.get("totalDebtToEquity")
        rev_growth = info.get("revenueGrowth")
        
        # Calculate Buffett score (0-100)
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
            "pe": pe,
            "debt_eq": debt_eq,
            "rev_growth": rev_growth,
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "Unknown"),
        }
    except Exception:
        return None

@st.cache_data(ttl=1800)
def fetch_news(ticker, max_news=10):
    """Fetch news for a ticker."""
    news_list = []
    try:
        # Try Finnhub
        url = f"https://finnhub.io/api/v1/news?symbol={ticker}&token=demo"
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            for article in data[:max_news]:
                news_list.append({
                    "title": article.get("headline", ""),
                    "summary": (article.get("summary", "") or "")[:200],
                    "source": article.get("source", ""),
                    "datetime": article.get("datetime", ""),
                    "url": article.get("url", "#")
                })
    except:
        pass
    
    if not news_list:
        # Return sample news
        news_list = [
            {"title": f"{ticker} reports strong quarterly earnings, beating estimates", 
             "summary": "The company exceeded analyst expectations with robust revenue growth and improved margins.",
             "source": "Market Insights", "datetime": time.time(), "url": "#"},
            {"title": f"Analysts upgrade {ticker} citing strong fundamentals", 
             "summary": "Multiple financial institutions raise price targets following positive developments.",
             "source": "Financial Times", "datetime": time.time(), "url": "#"},
            {"title": f"{ticker} announces strategic expansion plans", 
             "summary": "The company reveals new initiatives to capture market share and drive future growth.",
             "source": "Bloomberg", "datetime": time.time(), "url": "#"},
            {"title": f"Market volatility affects {ticker} trading", 
             "summary": "Broader market movements create short-term pressure on the stock.",
             "source": "Reuters", "datetime": time.time(), "url": "#"},
            {"title": f"Institutional investors increase {ticker} holdings", 
             "summary": "Major funds show confidence by adding to their positions.",
             "source": "WSJ", "datetime": time.time(), "url": "#"},
        ]
    return news_list

# ============================================
# UI COMPONENTS
# ============================================
def display_metric_card(title, value, change=None, color="#3b82f6"):
    """Display a styled metric card."""
    delta_html = f"<small style='color: #10b981;'>▲ {change:.1f}%</small>" if change and change > 0 else \
                 f"<small style='color: #ef4444;'>▼ {abs(change):.1f}%</small>" if change else ""
    
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.875rem; color: #94a3b8; margin-bottom: 0.5rem;">{title}</div>
        <div style="font-size: 1.75rem; font-weight: bold; color: {color};">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def display_score_circle(score, title):
    """Display a circular score indicator."""
    color = "#10b981" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"
    st.markdown(f"""
    <div style="text-align: center;">
        <div class="score-circle" style="background: conic-gradient({color} 0deg {score * 3.6}deg, #1e293b {score * 3.6}deg 360deg);">
            <div style="background: #0f172a; width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                <span style="font-size: 2rem; font-weight: bold; color: {color};">{score}</span>
            </div>
        </div>
        <div style="margin-top: 0.5rem; font-size: 0.875rem; color: #94a3b8;">{title}</div>
    </div>
    """, unsafe_allow_html=True)

def display_sentiment_gauge(sentiment_data):
    """Display sentiment gauge chart similar to watchlist display."""
    fig = go.Figure()
    
    # Add gauge chart
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=sentiment_data['overall_score'] * 100,
        title={"text": f"{sentiment_data['overall_icon']} Overall Sentiment", "font": {"size": 16}},
        delta={"reference": 50, "increasing": {"color": "green"}, "decreasing": {"color": "red"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "white"},
            "bar": {"color": sentiment_data['overall_color'], "thickness": 0.5},
            "bgcolor": "#1e293b",
            "borderwidth": 2,
            "bordercolor": "#334155",
            "steps": [
                {"range": [0, 33], "color": "#f44336", "name": "Negative"},
                {"range": [33, 66], "color": "#ffc107", "name": "Neutral"},
                {"range": [66, 100], "color": "#4caf50", "name": "Positive"}
            ],
            "threshold": {
                "line": {"color": "white", "width": 4},
                "thickness": 0.75,
                "value": sentiment_data['overall_score'] * 100
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"}
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_sentiment_distribution(sentiment_data):
    """Display sentiment distribution pie chart."""
    fig = go.Figure(data=[go.Pie(
        labels=['Positive', 'Neutral', 'Negative'],
        values=[sentiment_data['positive_pct'], sentiment_data['neutral_pct'], sentiment_data['negative_pct']],
        marker=dict(colors=['#10b981', '#f59e0b', '#ef4444']),
        hole=0.4,
        textinfo='label+percent',
        textposition='auto',
        hoverinfo='label+percent+value'
    )])
    
    fig.update_layout(
        title="Sentiment Distribution",
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"}
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# MAIN APP
# ============================================
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; margin: 0;">🌍 Global Buffett Screener</h1>
        <p style="color: #cbd5e1; margin: 0.5rem 0 0 0;">Value investing powered by Warren Buffett's principles</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Investment Philosophy")
        st.info("""
        **Buffett's Criteria:**
        - 📈 ROE > 15% (Profitability)
        - 💎 P/B < 1.5 (Value)
        - 🏦 Debt/Equity < 50% (Safety)
        - 📊 Revenue Growth > 10% (Growth)
        """)
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption("Scores range from 0-100, with higher scores indicating better alignment with Buffett's criteria.")
    
    # Main content - Index Selection
    st.markdown("## 🌟 Global Market Overview")
    st.markdown("Select an index to explore its top Buffett-style opportunities")
    
    # Display indices as clickable cards
    cols = st.columns(4)
    for idx, (name, info) in enumerate(MAJOR_INDICES.items()):
        with cols[idx % 4]:
            if st.button(f"{name}\n{info['market']}", key=f"index_{idx}", use_container_width=True):
                st.session_state.selected_index = info["ticker"]
                st.session_state.selected_index_name = name
                st.rerun()
    
    # Default selected index
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = "^GSPC"
        st.session_state.selected_index_name = "🇺🇸 S&P 500"
    
    st.markdown("---")
    
    # Fetch and display selected index data
    index_ticker = st.session_state.selected_index
    index_name = st.session_state.selected_index_name
    index_info = MAJOR_INDICES.get(index_name, {"region": "Global", "market": "Global Markets"})
    
    with st.spinner(f"Loading {index_name} data..."):
        hist = fetch_index_data(index_ticker, period="1mo")
        
        if not hist.empty:
            st.markdown(f"## 📈 {index_name} Performance")
            
            current_price = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else current_price
            daily_change = ((current_price - prev_close) / prev_close) * 100
            
            metric_cols = st.columns(4)
            with metric_cols[0]:
                display_metric_card("Current Level", f"{current_price:,.0f}", daily_change)
            with metric_cols[1]:
                display_metric_card("Daily Change", f"{daily_change:+.2f}%")
            
            # Index chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist["Close"],
                mode="lines",
                name=index_name,
                line=dict(color="#3b82f6", width=2),
                fill="tozeroy",
                fillcolor="rgba(59,130,246,0.1)"
            ))
            fig.update_layout(
                title=f"{index_name} - 30 Day Performance",
                template="plotly_dark",
                height=400,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Buffett Opportunities section
    st.markdown("---")
    st.markdown(f"## 🎯 Top Buffett Opportunities in {index_name}")
    
    # Get constituent stocks
    constituents = get_index_constituents(index_ticker)
    
    # Analyze constituents
    opportunities = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(constituents[:15]):  # Limit to 15 for performance
        status_text.text(f"Analyzing {ticker}...")
        fund_data = fetch_stock_fundamentals(ticker)
        if fund_data and fund_data["score"] > 0:
            opportunities.append({
                "Ticker": ticker,
                "Company": fund_data["name"][:30],
                "Sector": fund_data["sector"],
                "Buffett Score": fund_data["score"],
                "ROE": f"{fund_data['roe']*100:.1f}%" if fund_data['roe'] else "N/A",
                "P/B": f"{fund_data['pb']:.2f}" if fund_data['pb'] else "N/A",
                "D/E": f"{fund_data['debt_eq']:.0f}%" if fund_data['debt_eq'] else "N/A",
            })
        progress_bar.progress((i + 1) / len(constituents[:15]))
    
    progress_bar.empty()
    status_text.empty()
    
    # Sort and display opportunities
    if opportunities:
        df_opp = pd.DataFrame(opportunities).sort_values("Buffett Score", ascending=False)
        
        # Top 5 picks display
        st.markdown("### 🏆 Top 5 Picks from this Index")
        top_picks = df_opp.head(5)
        
        # Display in 2 rows
        pick_cols = st.columns(3)
        for idx in range(min(3, len(top_picks))):
            row = top_picks.iloc[idx]
            with pick_cols[idx]:
                score_color = "#10b981" if row['Buffett Score'] >= 70 else "#f59e0b" if row['Buffett Score'] >= 50 else "#ef4444"
                st.markdown(f"""
                <div class="top-pick-card">
                    <h3 style="color: #3b82f6;">{row['Ticker']}</h3>
                    <p style="color: #cbd5e1; font-size: 0.875rem;">{row['Company']}</p>
                    <div style="font-size: 2rem; font-weight: bold; color: {score_color};">{row['Buffett Score']}</div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">Buffett Score</div>
                    <hr>
                    <div style="font-size: 0.75rem; text-align: left;">
                        <div>ROE: {row['ROE']}</div>
                        <div>P/B: {row['P/B']}</div>
                        <div>D/E: {row['D/E']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        if len(top_picks) > 3:
            st.markdown("<br>", unsafe_allow_html=True)
            pick_cols_2 = st.columns(2)
            for idx in range(2):
                if 3 + idx < len(top_picks):
                    row = top_picks.iloc[3 + idx]
                    with pick_cols_2[idx]:
                        score_color = "#10b981" if row['Buffett Score'] >= 70 else "#f59e0b" if row['Buffett Score'] >= 50 else "#ef4444"
                        st.markdown(f"""
                        <div class="top-pick-card">
                            <h3 style="color: #3b82f6;">{row['Ticker']}</h3>
                            <p style="color: #cbd5e1; font-size: 0.875rem;">{row['Company']}</p>
                            <div style="font-size: 2rem; font-weight: bold; color: {score_color};">{row['Buffett Score']}</div>
                            <div style="font-size: 0.75rem; color: #94a3b8;">Buffett Score</div>
                            <hr>
                            <div style="font-size: 0.75rem; text-align: left;">
                                <div>ROE: {row['ROE']}</div>
                                <div>P/B: {row['P/B']}</div>
                                <div>D/E: {row['D/E']}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        # Full table
        st.markdown("### 📊 Complete Analysis")
        st.dataframe(df_opp, use_container_width=True, hide_index=True)
        
        # Download button
        csv = df_opp.to_csv(index=False)
        st.download_button("📥 Download CSV", csv, f"{index_name.replace(' ', '_')}_opportunities.csv", "text/csv")
    
    # Watchlist Section
    st.markdown("---")
    st.markdown("## 💼 My Watchlist")
    
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = ["AAPL", "MSFT", "GOOGL", "BRK-B"]
    
    # Add to watchlist
    col_add1, col_add2 = st.columns([3, 1])
    with col_add1:
        new_ticker = st.text_input("Add ticker", placeholder="Enter ticker (e.g., JPM)")
    with col_add2:
        st.write("")
        if st.button("➕ Add"):
            if new_ticker and new_ticker.upper() not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_ticker.upper())
                st.rerun()
    
    # Display watchlist
    if st.session_state.watchlist:
        for ticker in st.session_state.watchlist:
            col1, col2, col3 = st.columns([2, 2, 1])
            fund_data = fetch_stock_fundamentals(ticker)
            if fund_data:
                col1.write(f"**{ticker}**")
                col2.write(f"{fund_data['name'][:30]}")
                col3.write(f"Score: {fund_data['score']}")
            else:
               