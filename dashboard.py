# warren_buffett_global_screener.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import requests
import time
import warnings
import re
import json

warnings.filterwarnings('ignore')

# ==================== CONFIGURAÇÃO ====================
st.set_page_config(
    page_title="Warren Buffett Global Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS COM BOTÕES ALINHADOS ====================
st.markdown("""
<style>
    :root {
        --ft-offwhite: #fffef9;
        --ft-warm-white: #fff8f0;
        --ft-sand: #e8e0d0;
        --ft-coral: #ff6347;
        --ft-navy: #0a2540;
        --ft-border: #e6e0d5;
        --ft-text-light: #6b6b6b;
    }
    
    .stApp {
        background-color: var(--ft-offwhite);
    }
    
    body, .stMarkdown, p, div, span {
        font-size: 16px;
    }
    
    .ft-header {
        background: white;
        border-bottom: 2px solid var(--ft-coral);
        padding: 1.5rem 0;
        margin-bottom: 2rem;
    }
    
    .ft-header-content {
        max-width: 1400px;
        margin: 0 auto;
        padding: 0 2rem;
    }
    
    .ft-logo {
        font-family: 'Times New Roman', Times, serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--ft-navy);
        margin: 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid var(--ft-coral);
        display: inline-block;
    }
    
    .ft-logo-small {
        font-family: 'Times New Roman', Times, serif;
        font-size: 0.9rem;
        color: var(--ft-text-light);
        margin-top: 0.5rem;
    }
    
    .ft-section-title {
        font-family: 'Times New Roman', Times, serif;
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--ft-navy);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
    }
    
    .ft-card {
        background: white;
        border: 2px solid var(--ft-border);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .ft-card:hover {
        background: var(--ft-warm-white);
        border-color: var(--ft-coral);
    }
    
    .ft-metric-label {
        font-family: 'Times New Roman', Times, serif;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--ft-text-light);
        text-transform: uppercase;
        margin-bottom: 0.5rem;
        letter-spacing: 0.5px;
    }
    
    .ft-metric-value {
        font-family: 'Times New Roman', Times, serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--ft-navy);
        margin: 0.5rem 0;
    }
    
    .ft-metric-sub {
        font-family: 'Times New Roman', Times, serif;
        font-size: 0.9rem;
        color: var(--ft-text-light);
    }
    
    .ft-recommendation {
        font-family: 'Times New Roman', Times, serif;
        padding: 1.5rem;
        margin: 1.5rem 0;
        text-align: center;
        border: 2px solid;
    }
    
    .ft-buy {
        background: #e8f5e9;
        border-color: #2e7d32;
        color: #2e7d32;
    }
    
    .ft-hold {
        background: #fff3e0;
        border-color: #ed6c02;
        color: #ed6c02;
    }
    
    .ft-sell {
        background: #ffebee;
        border-color: #d32f2f;
        color: #d32f2f;
    }
    
    .ft-recommendation-value {
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: 2px;
    }
    
    .stTextInput > div > div > input {
        font-family: 'Times New Roman', Times, serif;
        font-size: 1.2rem;
        font-weight: 500;
        border: 2px solid var(--ft-border);
        padding: 1rem;
        background: white;
        color: #000000;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--ft-coral);
        box-shadow: 0 0 0 3px rgba(255, 99, 71, 0.2);
        outline: none;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #999;
        font-size: 1.1rem;
    }
    
    .stButton > button {
        font-family: 'Times New Roman', Times, serif;
        font-size: 1rem;
        font-weight: 600;
        background: var(--ft-navy);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: var(--ft-coral);
        transform: translateY(-2px);
    }
    
    .share-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
        flex-wrap: wrap;
        margin: 1.5rem 0;
        padding: 1rem;
        background: var(--ft-warm-white);
        border: 2px solid var(--ft-border);
    }
    
    .share-btn {
        font-family: 'Times New Roman', Times, serif;
        font-size: 0.95rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 10px 20px;
        text-decoration: none;
        color: white;
        text-align: center;
        min-width: 110px;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .share-btn:hover {
        transform: translateY(-2px);
        opacity: 0.9;
    }
    
    .btn-twitter { background: #1DA1F2; }
    .btn-linkedin { background: #0077B5; }
    .btn-whatsapp { background: #25D366; }
    .btn-facebook { background: #1877F2; }
    .btn-email { background: #EA4335; }
    
    .ft-separator {
        border-top: 2px solid var(--ft-border);
        margin: 2rem 0;
    }
    
    .ft-footer {
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        border-top: 2px solid var(--ft-border);
        font-size: 0.85rem;
        color: var(--ft-text-light);
    }
    
    .score-bar-bg {
        background: var(--ft-border);
        height: 4px;
        margin-top: 1rem;
    }
    
    .score-bar-fill {
        background: var(--ft-coral);
        height: 4px;
    }
    
    .dataframe {
        font-size: 1rem;
        font-family: 'Times New Roman', Times, serif;
    }
    
    .dataframe th {
        font-size: 0.9rem;
        font-weight: 700;
        background: var(--ft-warm-white);
        padding: 0.75rem;
    }
    
    .dataframe td {
        padding: 0.75rem;
        font-size: 0.95rem;
    }
    
    .css-1d391kg, .sidebar-content {
        background: var(--ft-warm-white);
        border-right: 2px solid var(--ft-border);
    }
    
    h1, h2, h3 {
        color: var(--ft-navy);
    }
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
st.markdown("""
<div class="ft-header">
    <div class="ft-header-content">
        <div class="ft-logo">Warren Buffett Global Screener</div>
        <div class="ft-logo-small">15,000+ Global Assets | All World Indices | Fundamental Analysis</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==================== DICIONÁRIO GLOBAL ====================
GLOBAL_COMPANY_MAP = {
    # US
    'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'amazon': 'AMZN',
    'nvidia': 'NVDA', 'meta': 'META', 'tesla': 'TSLA', 'netflix': 'NFLX',
    'disney': 'DIS', 'johnson': 'JNJ', 'visa': 'V', 'mastercard': 'MA',
    'coca cola': 'KO', 'pepsi': 'PEP', 'costco': 'COST', 'walmart': 'WMT',
    'mcdonalds': 'MCD', 'nike': 'NKE', 'starbucks': 'SBUX', 'intel': 'INTC',
    'cisco': 'CSCO', 'ibm': 'IBM', 'oracle': 'ORCL', 'qualcomm': 'QCOM',
    'amd': 'AMD', 'procter': 'PG', 'unitedhealth': 'UNH', 'home depot': 'HD',
    # Brazil
    'petrobras': 'PETR4.SA', 'vale': 'VALE3.SA', 'itau': 'ITUB4.SA',
    'bradesco': 'BBDC4.SA', 'banco do brasil': 'BBAS3.SA', 'ambev': 'ABEV3.SA',
    'weg': 'WEGE3.SA', 'magazine luiza': 'MGLU3.SA', 'renner': 'LREN3.SA',
    # Europe
    'nestle': 'NESN.SW', 'novartis': 'NOVN.SW', 'roche': 'ROG.SW', 'sap': 'SAP.DE',
    'siemens': 'SIE.DE', 'volkswagen': 'VOW3.DE', 'bmw': 'BMW.DE', 'lvmh': 'MC.PA',
    'totalenergies': 'TTE.PA', 'airbus': 'AIR.PA', 'unilever': 'ULVR.L', 'hsbc': 'HSBA.L',
    # Asia
    'toyota': '7203.T', 'honda': '7267.T', 'sony': '6758.T', 'samsung': '005930.KS',
    'alibaba': 'BABA', 'tencent': 'TCEHY', 'xiaomi': '1810.HK',
    # Canada
    'royal bank': 'RY.TO', 'toronto dominion': 'TD.TO', 'shopify': 'SHOP.TO',
    # Australia
    'cba': 'CBA.AX', 'bhp': 'BHP.AX', 'rio tinto': 'RIO.AX', 'csl': 'CSL.AX',
    # India
    'reliance': 'RELIANCE.NS', 'tcs': 'TCS.NS', 'hdfc bank': 'HDFCBANK.NS', 'infosys': 'INFY.NS',
    # ETFs
    'spy': 'SPY', 'qqq': 'QQQ', 'dia': 'DIA', 'iwm': 'IWM', 'voo': 'VOO',
    'gld': 'GLD', 'slv': 'SLV', 'uso': 'USO', 'xle': 'XLE', 'xlf': 'XLF',
    # Crypto
    'bitcoin': 'BTC-USD', 'ethereum': 'ETH-USD'
}

# ==================== FUNÇÕES ====================

def search_global_asset(query):
    """Busca qualquer ativo global"""
    query_clean = query.strip().upper()
    query_lower = query.strip().lower()
    
    ticker_pattern = r'^[A-Z0-9]{1,6}(\.[A-Z]{1,4})?(\-[A-Z]{1,4})?$'
    if re.match(ticker_pattern, query_clean):
        return query_clean
    
    if query_lower in GLOBAL_COMPANY_MAP:
        return GLOBAL_COMPANY_MAP[query_lower]
    
    for name, ticker in GLOBAL_COMPANY_MAP.items():
        if query_lower in name or name in query_lower:
            return ticker
    
    return query_clean

def get_stock_data(ticker):
    """Obtém dados da ação"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if info.get('regularMarketPrice') or info.get('currentPrice'):
            return {
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'country': info.get('country', 'Global'),
                'currentPrice': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'previousClose': info.get('previousClose', 0),
                'marketCap': info.get('marketCap', 0),
                'trailingPE': info.get('trailingPE', 0),
                'forwardPE': info.get('forwardPE', 0),
                'returnOnEquity': info.get('returnOnEquity', 0),
                'debtToEquity': info.get('debtToEquity', 0),
                'profitMargins': info.get('profitMargins', 0),
                'earningsGrowth': info.get('earningsGrowth', 0),
                'freeCashflow': info.get('freeCashflow', 0),
                'dividendYield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'targetPrice': info.get('targetMeanPrice', 0),
            }
        return None
    except:
        return None

def calculate_buffett_score(financials):
    """Calcula Buffett Score"""
    score = 0
    max_score = 0
    results = []
    
    # 1. ROE > 15%
    max_score += 20
    roe = financials.get('returnOnEquity', 0)
    if roe and roe > 0.15:
        score += 20
        results.append({'Criterion': 'ROE > 15%', 'Status': 'Yes', 'Value': f"{roe*100:.1f}%", 'Score': 20})
    else:
        results.append({'Criterion': 'ROE > 15%', 'Status': 'No', 'Value': f"{roe*100:.1f}%" if roe else 'N/A', 'Score': 0})
    
    # 2. Dívida/PL < 0.5
    max_score += 15
    debt = financials.get('debtToEquity', 999)
    if debt and debt < 0.5:
        score += 15
        results.append({'Criterion': 'Debt/Equity < 0.5', 'Status': 'Yes', 'Value': f"{debt:.2f}", 'Score': 15})
    else:
        results.append({'Criterion': 'Debt/Equity < 0.5', 'Status': 'No', 'Value': f"{debt:.2f}" if debt else 'N/A', 'Score': 0})
    
    # 3. Margem > 20%
    max_score += 15
    margin = financials.get('profitMargins', 0)
    if margin and margin > 0.20:
        score += 15
        results.append({'Criterion': 'Net Margin > 20%', 'Status': 'Yes', 'Value': f"{margin*100:.1f}%", 'Score': 15})
    else:
        results.append({'Criterion': 'Net Margin > 20%', 'Status': 'No', 'Value': f"{margin*100:.1f}%" if margin else 'N/A', 'Score': 0})
    
    # 4. P/L < 22
    max_score += 15
    pe = financials.get('trailingPE', 999)
    if pe and 0 < pe < 22:
        score += 15
        results.append({'Criterion': 'P/E < 22', 'Status': 'Yes', 'Value': f"{pe:.1f}", 'Score': 15})
    else:
        results.append({'Criterion': 'P/E < 22', 'Status': 'No', 'Value': f"{pe:.1f}" if pe else 'N/A', 'Score': 0})
    
    # 5. Crescimento > 10%
    max_score += 20
    growth = financials.get('earningsGrowth', 0)
    if growth and growth > 0.10:
        score += 20
        results.append({'Criterion': 'Earnings Growth > 10%', 'Status': 'Yes', 'Value': f"{growth*100:.1f}%", 'Score': 20})
    else:
        results.append({'Criterion': 'Earnings Growth > 10%', 'Status': 'No', 'Value': f"{growth*100:.1f}%" if growth else 'N/A', 'Score': 0})
    
    # 6. Fluxo Caixa positivo
    max_score += 15
    cashflow = financials.get('freeCashflow', 0)
    if cashflow and cashflow > 0:
        score += 15
        results.append({'Criterion': 'Positive Free Cash Flow', 'Status': 'Yes', 'Value': f"${cashflow/1e9:.2f}B", 'Score': 15})
    else:
        results.append({'Criterion': 'Positive Free Cash Flow', 'Status': 'No', 'Value': 'Negative' if cashflow else 'N/A', 'Score': 0})
    
    percentage = (score / max_score * 100) if max_score > 0 else 0
    
    if percentage >= 70:
        recommendation = "BUY"
        rec_class = "ft-buy"
    elif percentage >= 45:
        recommendation = "HOLD"
        rec_class = "ft-hold"
    else:
        recommendation = "SELL"
        rec_class = "ft-sell"
    
    return {
        'score': score,
        'max_score': max_score,
        'percentage': percentage,
        'results': results,
        'recommendation': recommendation,
        'rec_class': rec_class
    }

def create_share_text(ticker, company_name, final_rec, buffett_score):
    text = f"Warren Buffett Global Screener: {company_name} ({ticker})\n\n"
    text += f"Recommendation: {final_rec}\n"
    text += f"Buffett Score: {buffett_score:.0f}%"
    return text

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown('<div class="ft-section-title">Methodology</div>', unsafe_allow_html=True)
    st.markdown("**Warren Buffett's 6 Pillars**")
    st.markdown("""
    1. ROE > 15% - Profitability
    2. Debt/Equity < 0.5 - Solidity  
    3. Net Margin > 20% - Efficiency
    4. P/E < 22 - Fair Price
    5. Earnings Growth > 10% - Potential
    6. Positive Free Cash Flow - Health
    """)
    
    st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ft-section-title">Scoring</div>', unsafe_allow_html=True)
    st.markdown("""
    **Combined Score (0-100)**
    - Based on 6 Buffett criteria
    
    **Recommendations**
    - BUY: 70-100 points
    - HOLD: 45-69 points
    - SELL: 0-44 points
    """)
    
    st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ft-section-title">Coverage</div>', unsafe_allow_html=True)
    st.markdown("**15,000+ Global Assets**")
    st.markdown("""
    - US (S&P 500, NASDAQ, Dow Jones)
    - Brazil (Ibovespa)
    - Europe (DAX, CAC, FTSE)
    - Asia (Nikkei, Hang Seng)
    - Canada, Australia, India
    - ETFs, Commodities, Crypto
    """)

# ==================== BUSCA PRINCIPAL ====================
st.markdown('<div class="ft-section-title">Global Asset Search</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2.5, 1, 1])

with col1:
    search_query = st.text_input(
        "",
        value="AAPL",
        placeholder="Search 15,000+ assets - Any ticker or company name from any world index...",
        label_visibility="collapsed"
    )

with col2:
    analyze_btn = st.button("ANALYSE", type="primary", use_container_width=True)

with col3:
    screen_btn = st.button("GLOBAL SCREEN", use_container_width=True)

# ==================== ANÁLISE INDIVIDUAL ====================
if analyze_btn and search_query:
    ticker = search_global_asset(search_query)
    
    with st.spinner(f"Analysing {search_query} ({ticker})..."):
        financials = get_stock_data(ticker)
        
        if financials and financials['currentPrice'] > 0:
            buffett = calculate_buffett_score(financials)
            combined_score = buffett['percentage']
            
            if combined_score >= 70:
                final_rec = "BUY"
                final_class = "ft-buy"
            elif combined_score >= 45:
                final_rec = "HOLD"
                final_class = "ft-hold"
            else:
                final_rec = "SELL"
                final_class = "ft-sell"
            
            st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">Company</div>
                    <div class="ft-metric-value" style="font-size: 1.3rem;">{financials['name'][:35]}</div>
                    <div class="ft-metric-sub">{ticker} | {financials['country']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                price = financials['currentPrice']
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">Price</div>
                    <div class="ft-metric-value">${price:.2f}</div>
                    <div class="ft-metric-sub">Target: ${financials['targetPrice']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">Market Cap</div>
                    <div class="ft-metric-value">${financials['marketCap']/1e9:.1f}bn</div>
                    <div class="ft-metric-sub">Beta: {financials['beta']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                pe = financials['trailingPE']
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">P/E Ratio</div>
                    <div class="ft-metric-value">{pe:.1f}</div>
                    <div class="ft-metric-sub">Forward: {financials['forwardPE']:.1f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="ft-recommendation {final_class}">
                <div class="ft-recommendation-value">{final_rec}</div>
                <div>Based on Warren Buffett's 6 Fundamental Criteria</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">Buffett Score</div>
                    <div class="ft-metric-value">{buffett['percentage']:.0f}%</div>
                    <div>{buffett['score']}/{buffett['max_score']} criteria met</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">Score Bar</div>
                    <div class="score-bar-bg"><div class="score-bar-fill" style="width:{combined_score}%;"></div></div>
                    <div class="ft-metric-sub">0% - 50% - 100%</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
            st.markdown('<div class="ft-section-title">Buffett Criteria Analysis</div>', unsafe_allow_html=True)
            
            df_criteria = pd.DataFrame(buffett['results'])
            st.dataframe(df_criteria, use_container_width=True, hide_index=True)
            
            # ==================== BOTÕES DE COMPARTILHAMENTO ====================
            st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
            st.markdown('<div class="ft-section-title">Share Results</div>', unsafe_allow_html=True)
            
            share_text = create_share_text(ticker, financials['name'], final_rec, buffett['percentage'])
            share_encoded = share_text.replace('\n', '%0A')
            
            twitter_url = f"https://twitter.com/intent/tweet?text={share_encoded}"
            linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url=share&title={share_text}"
            whatsapp_url = f"https://wa.me/?text={share_encoded}"
            facebook_url = f"https://www.facebook.com/sharer/sharer.php?u=share&quote={share_text}"
            email_url = f"mailto:?subject=Warren Buffett Analysis: {ticker}&body={share_encoded}"
            
            st.markdown(f"""
            <div class="share-container">
                <a href="{twitter_url}" target="_blank" class="share-btn btn-twitter">Twitter</a>
                <a href="{linkedin_url}" target="_blank" class="share-btn btn-linkedin">LinkedIn</a>
                <a href="{whatsapp_url}" target="_blank" class="share-btn btn-whatsapp">WhatsApp</a>
                <a href="{facebook_url}" target="_blank" class="share-btn btn-facebook">Facebook</a>
                <a href="{email_url}" class="share-btn btn-email">Email</a>
            </div>
            """, unsafe_allow_html=True)
            
            report_data = pd.DataFrame([{
                'Ticker': ticker,
                'Company': financials['name'],
                'Price': financials['currentPrice'],
                'Market Cap Bn': financials['marketCap']/1e9,
                'P/E': financials['trailingPE'],
                'ROE': f"{financials['returnOnEquity']*100:.1f}%" if financials['returnOnEquity'] else "N/A",
                'Buffett Score': f"{buffett['percentage']:.0f}%",
                'Recommendation': final_rec
            }])
            
            csv = report_data.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, f"WB_{ticker}.csv", "text/csv")
            
        else:
            st.error(f"No data found for '{search_query}'. Please check the ticker or company name.")

# ==================== GLOBAL SCREENING ====================
if screen_btn:
    st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ft-section-title">Global Screening Results</div>', unsafe_allow_html=True)
    
    screening_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JNJ", "V", "WMT"]
    results = []
    progress_bar = st.progress(0)
    
    for idx, ticker in enumerate(screening_list):
        financials = get_stock_data(ticker)
        if financials and financials['currentPrice'] > 0:
            buffett = calculate_buffett_score(financials)
            
            rec = "BUY" if buffett['percentage'] >= 70 else "HOLD" if buffett['percentage'] >= 45 else "SELL"
            
            results.append({
                'Ticker': ticker,
                'Company': financials['name'][:30],
                'Price': financials['currentPrice'],
                'P/E': financials['trailingPE'],
                'ROE': f"{financials['returnOnEquity']*100:.1f}%" if financials['returnOnEquity'] else "N/A",
                'Buffett Score': f"{buffett['percentage']:.0f}%",
                'Recommendation': rec
            })
        
        progress_bar.progress((idx + 1) / len(screening_list))
        time.sleep(0.2)
    
    progress_bar.empty()
    
    if results:
        df_results = pd.DataFrame(results)
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        
        # Gráfico
        fig = px.bar(df_results, x='Ticker', y=[float(x.replace('%', '')) for x in df_results['Buffett Score']],
                     title='Global Screening - Buffett Scores',
                     color='Buffett Score', color_continuous_scale=['#d32f2f', '#ed6c02', '#2e7d32'])
        fig.update_layout(height=450)
        st.plotly_chart(fig, use_container_width=True)
        
        csv_screen = df_results.to_csv(index=False).encode('utf-8')
        st.download_button("Download Screening CSV", csv_screen, "WB_screening.csv", "text/csv")

# ==================== FOOTER ====================
st.markdown("""
<div class="ft-footer">
    <strong>15,000+ Global Assets | All World Indices</strong><br>
    Data: Yahoo Finance | Methodology: Warren Buffett's 6 Investment Principles<br>
    Educational purpose only. Not investment advice.
</div>
""", unsafe_allow_html=True)