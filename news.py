import streamlit as st
import pandas as pd
import numpy as np
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

# Headers de camuflagem para simular um browser real e passar os bloqueios da Streamlit Cloud
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive"
}

# --- GLOBAL AUTOSUGGEST ENGINE ---

def fetch_autosuggest(query: str) -> list:
    """Procura empresas mundiais por nome ou palavra-chave via API de sugestões."""
    if not query or len(query) < 2:
        return []
    
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=6&newsCount=0"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            quotes = response.json().get("quotes", [])
            suggestions = []
            for q in quotes:
                symbol = q.get("symbol")
                name = q.get("shortname") or q.get("longname") or symbol
                exchange = q.get("exchange", "Global")
                asset_type = q.get("quoteType", "EQUITY")
                suggestions.append({
                    "display": f"{symbol} - {name} ({exchange} | {asset_type})",
                    "symbol": symbol
                })
            return suggestions
    except Exception:
        return []
    return []

# --- SAFE DATA EXTRACTION ENGINE (CLOUD COMPATIBLE) ---

@st.cache_data(ttl=1800)
def get_fundamentals(ticker: str) -> dict:
    """Extrai os dados via endpoint v6 direto em JSON, imune aos bloqueios do yfinance."""
    ticker = ticker.strip().upper()
    url = f"https://query2.finance.yahoo.com/v6/finance/quoteSummary/{ticker}?modules=summaryDetail,financialData,defaultKeyStatistics,price"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=7)
        if response.status_code != 200:
            return None
            
        json_data = response.json()
        result_list = json_data.get("quoteSummary", {}).get("result", [])
        if not result_list:
            return None
            
        res = result_list[0]
        
        def get_val(module, key, subkey="raw"):
            return res.get(module, {}).get(key, {}).get(subkey, None)

        price = get_val("financialData", "currentPrice") or get_val("summaryDetail", "regularMarketPrice") or get_val("price", "regularMarketPrice") or 0.0
        company_name = res.get("price", {}).get("longName", ticker) or ticker
        
        if float(price) == 0.0:
            return None

        return {
            "ticker": ticker,
            "name": company_name,
            "price": float(price),
            "market_cap": get_val("summaryDetail", "marketCap") or get_val("price", "marketCap") or 0,
            "pe": get_val("summaryDetail", "trailingPE") or get_val("summaryDetail", "forwardPE") or 0.0,
            "eps": get_val("defaultKeyStatistics", "trailingEps") or 0.0,
            "roe": get_val("financialData", "returnOnEquity") or 0.0,         
            "margin": get_val("financialData", "profitMargins") or 0.0,       
            "debt_to_equity": get_val("financialData", "debtToEquity") or 0.0, 
            "growth": get_val("financialData", "earningsGrowth") or 0.0,      
            "fcf": get_val("financialData", "freeCashflow") or get_val("financialData", "operatingCashflow") or 0.0,
            "currency": res.get("price", {}).get("currency", "USD")
        }
    except Exception:
        return None

# --- VALUE INVESTING LOGIC RATIOS ---

def calculate_buffett_score(f: dict) -> int:
    score = 0
    if f["roe"] and f["roe"] >= 0.15: score += 20
    if f["margin"] and f["margin"] >= 0.15: score += 20
    if f["debt_to_equity"] and f["debt_to_equity"] <= 100: score += 15
    if f["growth"] and f["growth"] >= 0.10: score += 15
    if f["fcf"] and f["fcf"] > 0: score += 15
    if f["pe"] and 0 < f["pe"] <= 25: score += 15
    return min(score, 100)

def calculate_intrinsic_value(f: dict) -> float:
    """Fórmula de Benjamin Graham Corrigida: V = EPS * (8.5 + 2 * g)"""
    eps = f.get("eps") or 0.0
    growth = f.get("growth") or 0.0
    if eps <= 0:
        return 0.0  
    growth_percentage = max(growth * 100, 0.0) 
    return max(eps * (8.5 + (2 * growth_percentage)), 0.0)


# --- LAYOUT INTERFACE DESIGN ---

st.title(" Warren Buffett Global Screener Pro")
st.markdown("Search and filter equities worldwide using specialized quantitative analysis parameters.")

col_sidebar, col_main = st.columns([1.2, 3])

with col_sidebar:
    st.subheader("Global Discovery Hub")
    
    # Input de pesquisa por nome (ex: "amorim") como na tua imagem
    search_term = st.text_input("Search Company Name or Ticker:", placeholder="e.g., Amorim, Apple, LVMH...")
    
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
            st.warning("No matches cataloged for your query.")

    st.markdown("---")
    with st.form("direct_ticker_bypass"):
        override_ticker = st.text_input("Or bypass input with an exact Ticker:", value="AAPL")
        submitted_bypass = st.form_submit_button("Force Analytics Engine")
        
    if submitted_bypass:
        target_ticker = override_ticker

    st.markdown("---")
    st.subheader("Global Benchmark Targets")
    default_presets = ["AAPL", "MSFT", "GOOGL", "KO", "BRK-B", "ASML"]
    st.write(", ".join(default_presets))
    trigger_batch = st.button("Execute Global Screener", use_container_width=True)

with col_main:
    # Lógica de Estado para reter o Ticker Ativo
    if target_ticker:
        st.session_state.persisted_ticker = target_ticker

    if "persisted_ticker" in st.session_state:
        active_target = st.session_state.persisted_ticker
        
        with st.spinner(f"Running validation pipeline for {active_target}..."):
            data_metrics = get_fundamentals(active_target)
            
        if not data_metrics:
            st.error(f"❌ Target '{active_target}' could not recover a clean profile. The server IP might be temporarily rate-limited by Yahoo. Please try again or use the direct bypass input.")
        else:
            final_score = calculate_buffett_score(data_metrics)
            target_iv = calculate_intrinsic_value(data_metrics)
            price_now = data_metrics["price"]
            curr_sign = data_metrics["currency"]
            
            st.subheader(f"Analysis Snapshot: {data_metrics['name']} ({data_metrics['ticker']})")
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Market Price", f"{price_now:.2f} {curr_sign}")
            m2.metric("Buffett Checklist Score", f"{final_score}/100")
            
            if target_iv > 0:
                safety_margin = ((target_iv - price_now) / price_now) * 100
                m3.metric("Graham Target Price", f"{target_iv:.2f} {curr_sign}", delta=f"{safety_margin:.1f}% Margin")
            else:
                m3.metric("Graham Target Price", "Inapplicable")
                
            m4.metric("Market Capitalization", f"{data_metrics['market_cap']:,} {curr_sign}")

            left_split, right_split = st.columns([1, 1])
            with left_split:
                st.markdown("**Core Asset Properties Collected:**")
                view_df = pd.DataFrame([data_metrics]).T.reset_index()
                view_df.columns = ["Metric Structure", "Parsed Profile Value"]
                st.dataframe(view_df, use_container_width=True, hide_index=True)
                
            with right_split:
                st.markdown("**Buffett Philosophy Metrics Requirements:**")
                # Exibição simplificada e limpa para evitar quebras de string
                metrics_summary = {
                    "ROE (>= 15%)": f"{data_metrics['roe']*100:.1f}%",
                    "Profit Margin (>= 15%)": f"{data_metrics['margin']*100:.1f}%",
                    "Debt to Equity (<= 100%)": f"{data_metrics['debt_to_equity']:.1f}%",
                    "Earnings Growth (>= 10%)": f"{data_metrics['growth']*100:.1f}%",
                    "Free Cash Flow": f"{data_metrics['fcf']:,} {curr_sign}",
                    "P/E Ratio": f"{data_metrics['pe']:.1f}"
                }
                audit_df = pd.DataFrame(list(metrics_summary.items()), columns=["Indicator", "Value Discovered"])
                st.dataframe(audit_df, use_container_width=True, hide_index=True)

    # 2. BATCH BROWSER SCREENER PIPELINE
    if trigger_batch:
        st.subheader("📊 Cross-Border Screener Results")
        
        with st.spinner("Extracting parameters over background Cloud nodes..."):
            collected_rows = []
            # Reduzido para max_workers=3 para não levantar suspeitas de spam nos servidores da Cloud
            with ThreadPoolExecutor(max_workers=3) as manager:
                batch_responses = list(manager.map(get_fundamentals, default_presets))

            for block in batch_responses:
                if block:
                    computed_score = calculate_buffett_score(block)
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
            st.error("Severe Datacenter Blockade Detected by Yahoo. The server Cloud IP is temporarily throttled.")

st.markdown("---")
st.caption(f"Core cloud execution stack synced: {datetime.now():%Y-%m-%d %H:%M:%S}")