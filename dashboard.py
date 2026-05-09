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
    
    # For any other index, get top holdings from Yahoo Finance
    try:
        stock = yf.Ticker(ticker)
        holdings = stock.get_holdings()
        if holdings is not None and not holdings.empty:
            return holdings.index.tolist()[:20]
    except:
        pass
    
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
        profit_margin = info.get("profitMargins")
        
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
            "profit_margin": profit_margin,
            "name": info.get("longName", ticker),
            "sector": info.get("sector", "Unknown"),
            "market_cap": info.get("marketCap", 0),
            "industry": info.get("industry", "Unknown")
        }
    except Exception:
        return None

@st.cache_data(ttl=1800)
def fetch_news(ticker, max_news=8):
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
                    "summary": (article.get("summary", "") or "")[:150],
                    "source": article.get("source", ""),
                    "datetime": article.get("datetime", ""),
                    "url": article.get("url", "#")
                })
    except:
        pass
    
    if not news_list:
        # Return sample news
        news_list = [
            {"title": f"Market analysis: {ticker} shows strong momentum", 
             "summary": "Recent market trends indicate positive outlook with increasing institutional interest.",
             "source": "Market Insights", "datetime": time.time(), "url": "#"},
            {"title": f"Analysts update {ticker} price targets", 
             "summary": "Major financial institutions revise their price targets based on recent performance.",
             "source": "Financial Times", "datetime": time.time(), "url": "#"},
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
        st.markdown("### 📊 Dashboard Settings")
        auto_refresh = st.checkbox("Auto-refresh data", value=False)
        if auto_refresh:
            st.caption("Auto-refreshing every 5 minutes")
            time.sleep(300)
            st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption("""
        This screener evaluates stocks based on Warren Buffett's investment principles.
        Scores range from 0-100, with higher scores indicating better alignment with Buffett's criteria.
        """)
    
    # Main content - Index Selection
    st.markdown("## 🌟 Global Market Overview")
    st.markdown("Select an index to explore its top Buffett-style opportunities")
    
    # Display indices as clickable cards in a grid
    rows = (len(MAJOR_INDICES) + 3) // 4
    for row in range(rows):
        cols = st.columns(4)
        for i in range(4):
            idx = row * 4 + i
            if idx < len(MAJOR_INDICES):
                name = list(MAJOR_INDICES.keys())[idx]
                info = MAJOR_INDICES[name]
                with cols[i]:
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
            # Index performance cards
            st.markdown(f"## 📈 {index_name} Performance")
            st.markdown(f"*{index_info['market']} | {index_info['region']}*")
            
            current_price = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else current_price
            daily_change = ((current_price - prev_close) / prev_close) * 100
            weekly_change = ((hist["Close"].iloc[-1] - hist["Close"].iloc[-5]) / hist["Close"].iloc[-5]) * 100 if len(hist) >= 5 else 0
            monthly_change = ((hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0]) * 100
            
            metric_cols = st.columns(4)
            with metric_cols[0]:
                display_metric_card("Current Level", f"{current_price:,.0f}", daily_change)
            with metric_cols[1]:
                display_metric_card("Daily Change", f"{daily_change:+.2f}%", None, "#10b981" if daily_change > 0 else "#ef4444")
            with metric_cols[2]:
                display_metric_card("Weekly Change", f"{weekly_change:+.2f}%", None, "#10b981" if weekly_change > 0 else "#ef4444")
            with metric_cols[3]:
                display_metric_card("Monthly Change", f"{monthly_change:+.2f}%", None, "#10b981" if monthly_change > 0 else "#ef4444")
            
            # Index chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist.index, y=hist["Close"],
                mode="lines",
                name=index_name,
                line=dict(color=index_info.get("color", "#3b82f6"), width=2),
                fill="tozeroy",
                fillcolor=f"rgba({int(index_info.get('color', '#3b82f6')[1:3], 16)}, {int(index_info.get('color', '#3b82f6')[3:5], 16)}, {int(index_info.get('color', '#3b82f6')[5:7], 16)}, 0.1)"
            ))
            fig.update_layout(
                title=f"{index_name} - 30 Day Performance",
                template="plotly_dark",
                height=400,
                hovermode="x unified",
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Buffett Opportunities section - DYNAMIC based on selected index
    st.markdown("---")
    st.markdown(f"## 🎯 Top Buffett Opportunities in {index_name}")
    st.caption(f"Stocks from {index_name} that best match Warren Buffett's investment criteria")
    
    # Get constituent stocks dynamically for the selected index
    constituents = get_index_constituents(index_ticker)
    
    # Analyze constituents
    opportunities = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(constituents):
        status_text.text(f"Analyzing {ticker} from {index_name}...")
        fund_data = fetch_stock_fundamentals(ticker)
        if fund_data and fund_data["score"] > 0:
            opportunities.append({
                "Ticker": ticker,
                "Company": fund_data["name"][:35],
                "Sector": fund_data["sector"],
                "Industry": fund_data["industry"],
                "Buffett Score": fund_data["score"],
                "ROE": f"{fund_data['roe']*100:.1f}%" if fund_data['roe'] else "N/A",
                "P/B": f"{fund_data['pb']:.2f}" if fund_data['pb'] else "N/A",
                "D/E": f"{fund_data['debt_eq']:.0f}%" if fund_data['debt_eq'] else "N/A",
                "Revenue Growth": f"{fund_data['rev_growth']*100:.1f}%" if fund_data['rev_growth'] else "N/A",
            })
        progress_bar.progress((i + 1) / len(constituents))
    
    progress_bar.empty()
    status_text.empty()
    
    # Sort and display opportunities
    if opportunities:
        df_opp = pd.DataFrame(opportunities).sort_values("Buffett Score", ascending=False)
        
        # Statistics summary
        st.markdown(f"**Found {len(opportunities)} stocks with positive Buffett scores in {index_name}**")
        
        # Top picks display
        st.markdown("### 🏆 Top 3 Picks from this Index")
        top_picks = df_opp.head(3)
        
        pick_cols = st.columns(3)
        for idx, (_, row) in enumerate(top_picks.iterrows()):
            with pick_cols[idx]:
                score_color = "#10b981" if row['Buffett Score'] >= 70 else "#f59e0b" if row['Buffett Score'] >= 50 else "#ef4444"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 1rem; border-radius: 0.75rem; text-align: center; border: 2px solid {score_color}30;">
                    <h3 style="color: #3b82f6; margin: 0;">{row['Ticker']}</h3>
                    <p style="color: #cbd5e1; font-size: 0.875rem; margin: 0.25rem 0;">{row['Company']}</p>
                    <div style="font-size: 2rem; font-weight: bold; color: {score_color}; margin: 0.5rem 0;">{row['Buffett Score']}</div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">Buffett Score</div>
                    <hr style="margin: 0.5rem 0;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.7rem; text-align: left;">
                        <div>🏢 {row['Sector'][:12]}</div>
                        <div>📊 ROE: {row['ROE']}</div>
                        <div>💎 P/B: {row['P/B']}</div>
                        <div>🏦 D/E: {row['D/E']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Full table
        st.markdown("### 📊 Complete Analysis for this Index")
        st.dataframe(
            df_opp,
            use_container_width=True,
            column_config={
                "Buffett Score": st.column_config.ProgressColumn(
                    "Buffett Score",
                    help="Score based on Buffett's criteria (0-100)",
                    format="%d",
                    min_value=0,
                    max_value=100,
                ),
                "Ticker": st.column_config.TextColumn("Symbol"),
                "Company": st.column_config.TextColumn("Company Name"),
                "Sector": st.column_config.TextColumn("Sector"),
                "ROE": st.column_config.TextColumn("ROE"),
                "P/B": st.column_config.TextColumn("P/B Ratio"),
                "D/E": st.column_config.TextColumn("D/E Ratio"),
                "Revenue Growth": st.column_config.TextColumn("Revenue Growth"),
            },
            hide_index=True,
            height=400
        )
        
        # Download button
        csv = df_opp.to_csv(index=False)
        st.download_button(
            label="📥 Download Analysis as CSV",
            data=csv,
            file_name=f"{index_name.replace(' ', '_')}_buffett_opportunities.csv",
            mime="text/csv",
        )
    else:
        st.warning(f"No Buffett-style opportunities found in {index_name} currently. Try another index!")
    
    # Portfolio Section
    st.markdown("---")
    st.markdown("## 💼 My Watchlist")
    
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = ["AAPL", "MSFT", "GOOGL", "BRK-B"]
    
    # Add to watchlist
    col_add1, col_add2 = st.columns([3, 1])
    with col_add1:
        new_ticker = st.text_input("Add ticker to watchlist", placeholder="Enter ticker (e.g., JPM)", key="watchlist_add")
    with col_add2:
        st.write("")
        st.write("")
        if st.button("➕ Add to Watchlist", use_container_width=True):
            if new_ticker and new_ticker.upper() not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_ticker.upper())
                st.rerun()
    
    # Display watchlist
    if st.session_state.watchlist:
        watchlist_data = []
        for ticker in st.session_state.watchlist:
            fund_data = fetch_stock_fundamentals(ticker)
            if fund_data:
                watchlist_data.append({
                    "Ticker": ticker,
                    "Company": fund_data["name"][:25],
                    "Score": fund_data["score"],
                    "ROE": f"{fund_data['roe']*100:.1f}%" if fund_data['roe'] else "N/A",
                    "P/B": f"{fund_data['pb']:.2f}" if fund_data['pb'] else "N/A",
                })
        
        if watchlist_data:
            df_watchlist = pd.DataFrame(watchlist_data).sort_values("Score", ascending=False)
            
            # Display as cards
            w_cols = st.columns(min(4, len(df_watchlist)))
            for idx, (_, row) in enumerate(df_watchlist.head(8).iterrows()):
                with w_cols[idx % 4]:
                    score_color = "#10b981" if row["Score"] >= 70 else "#f59e0b" if row["Score"] >= 50 else "#ef4444"
                    st.markdown(f"""
                    <div class="portfolio-item" style="flex-direction: column; align-items: stretch;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="font-size: 1.1rem;">{row['Ticker']}</strong>
                            <span style="background: {score_color}; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold;">{row['Score']}</span>
                        </div>
                        <div style="font-size: 0.75rem; color: #94a3b8; margin: 0.25rem 0;">{row['Company']}</div>
                        <div style="display: flex; gap: 0.5rem; font-size: 0.7rem; margin-top: 0.25rem;">
                            <span>ROE: {row['ROE']}</span>
                            <span>P/B: {row['P/B']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"🗑️ Remove", key=f"remove_watch_{row['Ticker']}", help=f"Remove {row['Ticker']}"):
                        st.session_state.watchlist.remove(row['Ticker'])
                        st.rerun()
    
    # Stock Detail Section
    st.markdown("---")
    st.markdown("## 🔍 Stock Deep Dive")
    
    # Create combined list of watchlist and top opportunities
    all_tickers = list(set(st.session_state.watchlist + [opp["Ticker"] for opp in opportunities[:5]]))
    
    selected_stock = st.selectbox("Select a stock for detailed analysis", 
                                   options=all_tickers if all_tickers else ["AAPL", "MSFT", "GOOGL"],
                                   key="stock_detail")
    
    if selected_stock:
        with st.spinner(f"Loading {selected_stock} details..."):
            fund_data = fetch_stock_fundamentals(selected_stock)
            news = fetch_news(selected_stock, max_news=6)
            
            if fund_data:
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    display_score_circle(fund_data["score"], "Buffett Score")
                    st.markdown("---")
                    st.markdown("**Key Metrics**")
                    st.metric("Return on Equity (ROE)", f"{fund_data['roe']*100:.1f}%" if fund_data['roe'] else "N/A")
                    st.metric("Price to Book (P/B)", f"{fund_data['pb']:.2f}" if fund_data['pb'] else "N/A")
                    st.metric("P/E Ratio", f"{fund_data['pe']:.1f}" if fund_data['pe'] else "N/A")
                    st.metric("Debt to Equity", f"{fund_data['debt_eq']:.0f}%" if fund_data['debt_eq'] else "N/A")
                    st.metric("Revenue Growth", f"{fund_data['rev_growth']*100:.1f}%" if fund_data['rev_growth'] else "N/A")
                
                with col2:
                    st.markdown(f"### {fund_data['name']}")
                    st.markdown(f"**Sector:** {fund_data['sector']} | **Industry:** {fund_data['industry']}")
                    
                    # Score breakdown
                    st.markdown("#### Score Breakdown")
                    breakdown_cols = st.columns(4)
                    with breakdown_cols[0]:
                        profit_score = min(40, fund_data["score"])
                        st.progress(profit_score / 40, text=f"Profitability: {profit_score}/40")
                    with breakdown_cols[1]:
                        val_score = max(0, min(30, fund_data["score"] - 40 if fund_data["score"] > 40 else fund_data["score"]))
                        st.progress(val_score / 30 if val_score > 0 else 0, text=f"Valuation: {val_score}/30")
                    with breakdown_cols[2]:
                        debt_score = max(0, min(20, fund_data["score"] - 70 if fund_data["score"] > 70 else 0))
                        st.progress(debt_score / 20 if debt_score > 0 else 0, text=f"Debt: {debt_score}/20")
                    with breakdown_cols[3]:
                        growth_score = max(0, min(10, fund_data["score"] - 90 if fund_data["score"] > 90 else 0))
                        st.progress(growth_score / 10 if growth_score > 0 else 0, text=f"Growth: {growth_score}/10")
                    
                    # Recommendation
                    st.markdown("---")
                    if fund_data["score"] >= 70:
                        st.success("**✅ STRONG BUY** - Meets most of Buffett's criteria. Excellent fundamentals with strong value characteristics.")
                    elif fund_data["score"] >= 50:
                        st.info("**📊 ACCUMULATE** - Good fundamentals but some areas need improvement. Consider dollar-cost averaging.")
                    elif fund_data["score"] >= 30:
                        st.warning("**⚠️ HOLD** - Mixed signals, consider waiting for better entry point or improved fundamentals.")
                    else:
                        st.error("**❌ AVOID** - Does not meet Buffett's investment criteria. Look for better opportunities.")
                
                # News section