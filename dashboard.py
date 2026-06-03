import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import requests
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# 1. Page Configuration
st.set_page_config(
    page_title="Warren Buffett Global Screener Pro", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GLOBAL AUTOSUGGEST ENGINE ---

def fetch_autosuggest(query: str) -> list:
    """
    Scans the Yahoo search cluster for autosuggestions.
    Maps company names or keywords to global tickers.
    """
    if not query or len(query) < 2:
        return []
    
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=8&newsCount=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=4)
        if response.status_code == 200:
            quotes = response.json().get("quotes", [])
            suggestions = []
            for q in quotes:
                symbol = q.get("symbol")
                name = q.get("shortname") or q.get("longname") or symbol
                exchange = q.get("exchange", "Global")
                asset_type = q.get("quoteType", "EQUITY")
                
                # Exclude boring components if necessary
                suggestions.append({
                    "display": f"{symbol} - {name} ({exchange} | {asset_type})",
                    "symbol": symbol
                })
            return suggestions
    except Exception:
        return []
    return []

# --- SAFE DATA EXTRACTION ENGINE ---

@st.cache_data(ttl=3600)
def get_fundamentals(ticker: str) -> dict:
    """
    Extracts global normalized financial data using the updated yfinance core backend.
    """
    try:
        ticker_obj = yf.Ticker(ticker.strip().upper())
        info = ticker_obj.info
        
        if not info or "price" in info and info["price"] is None:
            return None
            
        # Extract currency with fallback
        currency = info.get("currency", "USD")
        
        return {
            "ticker": ticker.upper(),
            "name": info.get("longName") or info.get("shortName") or ticker.upper(),
            "price": info.get("currentPrice") or info.get("regularMarketPrice") or 0.0,
            "market_cap": info.get("marketCap", 0),
            "pe": info.get("trailingPE") or info.get("forwardPE", None),
            "eps": info.get("trailingEps", None),
            "roe": info.get("returnOnEquity", None),         # e.g., 0.18 for 18%
            "margin": info.get("profitMargins", None),       # e.g., 0.15 for 15%
            "debt_to_equity": info.get("debtToEquity", None),# e.g., 85.0 for 85%
            "growth": info.get("earningsGrowth", None),      # e.g., 0.12 for 12%
            "fcf": info.get("freeCashflow") or info.get("operatingCashflow", None),
            "currency": currency
        }
    except Exception:
        return None

# --- VALUE INVESTING LOGIC RATIOS ---

def calculate_buffett_score(f: dict) -> tuple:
    score = 0
    breakdown = {}
    
    # 1. Return on Equity (ROE >= 15%)
    roe_val = f.get("roe") or 0.0
    if roe_val >= 0.15:
        score += 20
        breakdown["ROE (>= 15%)"] = "✅ Excellent"
    else:
        breakdown["ROE (>= 15%)"] = f"❌ Weak ({roe_val*100:.1f}%)"

    # 2. Operating Margins (>= 15% - Economic Moat Indicator)
    margin_val = f.get("margin") or 0.0
    if margin_val >= 0.15:
        score += 20
        breakdown["Profit Margin (>= 15%)"] = "✅ High Moat"
    else:
        breakdown["Profit Margin (>= 15%)"] = f"❌ Compressed ({margin_val*100:.1f}%)"

    # 3. Leverage Control (Debt-to-Equity <= 100%)
    debt_val = f.get("debt_to_equity") or 0.0
    if 0 < debt_val <= 100:
        score += 15
        breakdown["Debt/Equity (<= 100%)"] = "✅ Balanced Leverage"
    elif debt_val == 0:
        score += 15
        breakdown["Debt/Equity (<= 100%)"] = "✅ Zero Debt Risk"
    else:
        breakdown["Debt/Equity (<= 100%)"] = f"❌ High Debt Risk ({debt_val:.1f}%)"

    # 4. Momentum / Expansion Growth (>= 10%)
    growth_val = f.get("growth") or 0.0
    if growth_val >= 0.10:
        score += 15
        breakdown["Earnings Growth (>= 10%)"] = "✅ Compounding"
    else:
        breakdown["Earnings Growth (>= 10%)"] = f"❌ Slow Growth ({growth_val*100:.1f}%)"

    # 5. Free Cash Flow Health
    fcf_val = f.get("fcf") or 0
    if fcf_val > 0:
        score += 15
        breakdown["Free Cash Flow Status"] = "✅ Cash Machine"
    else:
        breakdown["Free Cash Flow Status"] = "❌ Capital Destructive"

    # 6. Valuation Entry Point (P/E Ratio <= 25)
    pe_val = f.get("pe") or 0
    if 0 < pe_val <= 25:
        score += 15
        breakdown["Valuation Guardrail (P/E <= 25)"] = "✅ Fair Price"
    else:
        breakdown["Valuation Guardrail (P/E <= 25)"] = f"❌ Premium Multiples (P/E: {pe_val:.1f})"

    return min(score, 100), breakdown

def calculate_intrinsic_value(f: dict) -> float:
    """Benjamin Graham Formula: V = EPS * (8.5 + 2 * g)"""
    eps = f.get("eps")
    growth = f.get("growth") or 0.0
    if not eps or eps <= 0:
        return 0.0  
    growth_percentage = max(growth * 100, 0.0) 
    return max(eps * (8.5 + (2 * growth_percentage)), 0.0)


# --- LAYOUT INTERFACE DESIGN ---

st.title("📈 Warren Buffett Global Screener Pro")
st.markdown("Search and filter equities worldwide using specialized quantitative analysis parameters.")

col_sidebar, col_main = st.columns([1.2, 3])

with col_sidebar:
    st.subheader("Global Discovery Hub")
    
    # Text Input triggering the autosuggest logic
    search_term = st.text_input("Search Company Name or Ticker:", placeholder="e.g., Apple, Petrobras, LVMH...")
    
    target_ticker = None
    if len(search_term) >= 2:
        with st.spinner("Scanning directory nodes..."):
            items = fetch_autosuggest(search_term)
        if items:
            mapping = {item["display"]: item["symbol"] for item in items}
            chosen_item = st.selectbox("Select exact security matching target:", options=list(mapping.keys()))
            if chosen_item:
                target_ticker = mapping[chosen_item]
        else:
            st.warning("No matches cataloged for your string query.")

    st.markdown("---")
    with st.form("direct_ticker_bypass"):
        override_ticker = st.text_input("Or bypass input with an exact Ticker:", value="AAPL")
        submitted_bypass = st.form_submit_button("Force Analytics Engine")
        
    if submitted_bypass:
        target_ticker = override_ticker

    st.markdown("---")
    st.subheader("Global Benchmark Targets")
    default_presets = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "ASML", "BRK-B", "PETR4.SA"]
    st.write(", ".join(default_presets))
    trigger_batch = st.button("Execute Multi-Thread Screener", use_container_width=True)

with col_main:
    # 1. INDIVIDUAL DATA ANALYTICS DISCOVERY
    if target_ticker:
        st.session_state.persisted_ticker = target_ticker

    if "persisted_ticker" in st.session_state:
        active_target = st.session_state.persisted_ticker
        
        with st.spinner(f"Running secure validation pipeline for {active_target}..."):
            data_metrics = get_fundamentals(active_target)
            
        if not data_metrics:
            st.error(f"❌ Target '{active_target}' could not recover a clean dataset profile. Check connections or try standard tickers.")
        else:
            final_score, rules_check = calculate_buffett_score(data_metrics)
            target_iv = calculate_intrinsic_value(data_metrics)
            price_now = data_metrics["price"]
            curr_sign = data_metrics["currency"]
            
            st.subheader(f"Analysis Snapshot: {data_metrics['name']} ({data_metrics['ticker']})")
            
            # Metric Rows KPIs
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Market Price", f"{price_now:.2f} {curr_sign}")
            m2.metric("Buffett Checklist Score", f"{final_score}/100")
            
            if target_iv > 0:
                safety_margin = ((target_iv - price_now) / price_now) * 100
                m3.metric("Graham Target Price", f"{target_iv:.2f} {curr_sign}", delta=f"{safety_margin:.1f}% Margin")
            else:
                m3.metric("Graham Target Price", "Inapplicable", help="Incompatible for net negative earnings entities.")
                
            m4.metric("Market Capitalization", f"{data_metrics['market_cap']:,} {curr_sign}")

            # Visual Splits
            left_split, right_split = st.columns([1, 1])
            with left_split:
                st.markdown("**Core Asset Properties Collected:**")
                view_df = pd.DataFrame([data_metrics]).T.reset_index()
                view_df.columns = ["Metric Structure", "Parsed Profile Value"]
                st.dataframe(view_df, use_container_width=True, hide_index=True)
                
            with right_split:
                st.markdown("**Buffett Philosophy Audit Logs:**")
                audit_df = pd.DataFrame(list(rules_check.items()), columns=["Audit Standard Rules", "Result Status"])
                st.dataframe(audit_df, use_container_width=True, hide_index=True)

    # 2. BATCH BROWSER SCREENER PIPELINE
    if trigger_batch:
        st.subheader("📊 Cross-Border Multi-Thread Matrix Matrix Monitoring")
        
        with st.spinner("Extracting parameters concurrently over 8 background nodes..."):
            collected_rows = []
            with ThreadPoolExecutor(max_workers=len(default_presets)) as manager:
                batch_responses = list(manager.map(get_fundamentals, default_presets))

            for block in batch_responses:
                if block:
                    computed_score, _ = calculate_buffett_score(block)
                    computed_iv = calculate_intrinsic_value(block)
                    
                    spread = f"{((computed_iv - block['price']) / block['price']) * 100:.1f}%" if computed_iv > 0 else "Inapplicable"
                    
                    collected_rows.append({
                        "Symbol": block["ticker"],
                        "Corporate Asset Name": block["name"],
                        "Buffett Score": computed_score,
                        "Price Point": f"{block['price']:.2f} {block['currency']}",
                        "P/E Metric": f"{block['pe']:.1f}" if block["pe"] else "N/A",
                        "Graham Fair Value": f"{computed_iv:.2f} {block['currency']}" if computed_iv > 0 else "N/A",
                        "Target Margin Spread": spread
                    })

        if collected_rows:
            output_table_df = pd.DataFrame(collected_rows).sort_values("Buffett Score", ascending=False)
            st.dataframe(output_table_df, use_container_width=True, hide_index=True)
            
            chart_fig = px.bar(
                output_table_df, 
                x="Symbol", 
                y="Buffett Score",
                color="Buffett Score",
                text_auto=True,
                title="Consolidated Asset Performance Vector Alignment Index",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            st.plotly_chart(chart_fig, use_container_width=True)
        else:
            st.error("Severe Network Blockade Detected. Destination interface rate limited.")

st.markdown("---")
st.caption(f"System monitoring logs clear • Core execution stack synced: {datetime.now():%Y-%m-%d %H:%M:%S}")