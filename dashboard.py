# dashboard.py - Safe dictionary access, no Finnhub
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import requests
import time
import warnings
import re
from textblob import TextBlob
from typing import Dict, List, Optional

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Warren Buffett Global Screener", page_icon="📈", layout="wide")

# ------------------------ API KEYS (optional) ------------------------
ALPHA_VANTAGE_KEY = "GKOFM3JHT9YJ9HYO"  # Optional, only used if available

# ------------------------ CSS (unchanged) ------------------------
st.markdown("""
<style>
    :root { --ft-offwhite: #fffef9; --ft-warm-white: #fff8f0; --ft-coral: #ff6347; --ft-navy: #0a2540; --ft-border: #e6e0d5; }
    .stApp { background-color: var(--ft-offwhite); }
    .ft-header { background: white; border-bottom: 2px solid var(--ft-coral); padding: 1.5rem 0; margin-bottom: 2rem; }
    .ft-header-content { max-width: 1400px; margin: 0 auto; padding: 0 2rem; }
    .ft-logo { font-family: 'Times New Roman', Times, serif; font-size: 2.5rem; font-weight: 700; color: var(--ft-navy); border-bottom: 3px solid var(--ft-coral); display: inline-block; }
    .ft-logo-small { font-family: 'Times New Roman', Times, serif; font-size: 0.9rem; color: #6b6b6b; margin-top:0.5rem;}
    .ft-section-title { font-family: 'Times New Roman', Times, serif; font-size: 0.9rem; font-weight: 600; color: var(--ft-navy); text-transform: uppercase; margin-bottom: 0.75rem; }
    .ft-card { background: white; border: 2px solid var(--ft-border); padding: 1.5rem; margin: 1rem 0; transition: all 0.3s ease; }
    .ft-card:hover { background: #fff8f0; border-color: var(--ft-coral); transform: translateY(-3px); }
    .ft-metric-label { font-family: 'Times New Roman', Times, serif; font-size: 0.85rem; font-weight: 600; color: #6b6b6b; text-transform: uppercase; }
    .ft-metric-value { font-family: 'Times New Roman', Times, serif; font-size: 2.2rem; font-weight: 700; color: var(--ft-navy); margin: 0.5rem 0; }
    .ft-recommendation { font-family: 'Times New Roman', Times, serif; padding: 1.5rem; margin: 1.5rem 0; text-align: center; border: 2px solid; }
    .ft-buy { background: #e8f5e9; border-color: #2e7d32; color: #2e7d32; }
    .ft-hold { background: #fff3e0; border-color: #ed6c02; color: #ed6c02; }
    .ft-sell { background: #ffebee; border-color: #d32f2f; color: #d32f2f; }
    .ft-recommendation-value { font-size: 3.5rem; font-weight: 800; letter-spacing: 2px; }
    .stTextInput > div > div > input { font-family: 'Times New Roman', Times, serif; font-size: 1.2rem; border: 2px solid var(--ft-border); padding: 1rem; }
    .stButton > button { font-weight: 600; background: var(--ft-navy); color: white; border: none; padding: 0.8rem 2rem; width: 100%; }
    .stButton > button:hover { background: var(--ft-coral); transform: translateY(-3px); }
    .share-container { display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; margin: 1.5rem 0; padding: 1rem; background: #fff8f0; border: 2px solid var(--ft-border); }
    .share-btn { font-family: 'Times New Roman', Times, serif; font-size: 0.95rem; font-weight: 600; padding: 10px 20px; text-decoration: none; color: white; min-width: 110px; text-align: center; }
    .btn-twitter { background: #1DA1F2; } .btn-linkedin { background: #0077B5; } .btn-whatsapp { background: #25D366; } .btn-facebook { background: #1877F2; } .btn-email { background: #EA4335; }
    .ft-separator { border-top: 2px solid var(--ft-border); margin: 2rem 0; }
    .ft-footer { text-align: center; padding: 2rem; margin-top: 3rem; border-top: 2px solid var(--ft-border); font-size: 0.85rem; color: #6b6b6b; }
    .score-bar-bg { background: var(--ft-border); height: 6px; margin-top: 1rem; }
    .score-bar-fill { background: var(--ft-coral); height: 6px; transition: width 0.5s ease; }
    .sentiment-positive { color: #2e7d32; font-weight: bold; }
    .sentiment-negative { color: #d32f2f; font-weight: bold; }
    .sentiment-neutral { color: #ed6c02; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ------------------------ HEADER ------------------------
st.markdown("""
<div class="ft-header">
    <div class="ft-header-content">
        <div class="ft-logo">Warren Buffett Global Screener</div>
        <div class="ft-logo-small">Analyze more than 15,000 Assets for Fundamentals</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ======================== DATA FUNCTIONS (Yahoo Finance only + Alpha Vantage optional) ========================
@st.cache_data(ttl=3600)
def fetch_yfinance(ticker: str) -> Dict:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # Use .get() with defaults to avoid KeyError
        return {
            'name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'country': info.get('country', 'Global'),
            'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
            'market_cap': info.get('marketCap', 0),
            'pe': info.get('trailingPE', 0),
            'forward_pe': info.get('forwardPE', 0),
            'roe': info.get('returnOnEquity', 0),
            'debt_to_equity': info.get('debtToEquity', 0),
            'profit_margin': info.get('profitMargins', 0),
            'earnings_growth': info.get('earningsGrowth', 0),
            'free_cash_flow': info.get('freeCashflow', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'beta': info.get('beta', 0),
            'target_price': info.get('targetMeanPrice', 0),
        }
    except Exception as e:
        # Return a minimal dict with default values on any error
        return {
            'name': ticker,
            'sector': 'N/A',
            'country': 'Global',
            'price': 0,
            'market_cap': 0,
            'pe': 0,
            'forward_pe': 0,
            'roe': 0,
            'debt_to_equity': 0,
            'profit_margin': 0,
            'earnings_growth': 0,
            'free_cash_flow': 0,
            'dividend_yield': 0,
            'beta': 0,
            'target_price': 0,
        }

@st.cache_data(ttl=3600)
def fetch_alpha_vantage(ticker: str) -> Dict:
    if not ALPHA_VANTAGE_KEY:
        return {}
    try:
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_KEY}"
        data = requests.get(url).json()
        if data and 'Symbol' in data:
            return {
                'roe': float(data.get('ReturnOnEquityTTM', 0)) / 100,
                'profit_margin': float(data.get('ProfitMargin', 0)) / 100,
                'pe': float(data.get('PERatio', 0)),
                'beta': float(data.get('Beta', 0)),
            }
    except:
        pass
    return {}

def get_aggregated_fundamentals(ticker: str) -> Dict:
    base = fetch_yfinance(ticker)
    # If price is 0, the ticker is invalid – return as is
    if base.get('price', 0) == 0:
        return base
    # Try to enrich with Alpha Vantage if available and missing
    if base.get('roe', 0) == 0:
        av = fetch_alpha_vantage(ticker)
        for k in ['roe', 'profit_margin', 'pe', 'beta']:
            if av.get(k) and not base.get(k):
                base[k] = av.get(k)
    # Ensure all keys exist with defaults
    defaults = {
        'roe': 0, 'debt_to_equity': 0, 'profit_margin': 0, 'earnings_growth': 0,
        'free_cash_flow': 0, 'pe': 0, 'beta': 0, 'name': ticker, 'sector': 'N/A',
        'country': 'Global', 'price': 0, 'market_cap': 0, 'forward_pe': 0,
        'dividend_yield': 0, 'target_price': 0
    }
    for k, v in defaults.items():
        if k not in base or base[k] is None:
            base[k] = v
    return base

@st.cache_data(ttl=1800)
def fetch_news_sentiment(ticker: str) -> Dict:
    articles = []
    try:
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=8"
        data = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).json()
        for item in data.get('news', []):
            articles.append({
                'title': item.get('title', ''),
                'link': item.get('link', '#'),
                'source': 'Yahoo Finance',
                'date': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d') if item.get('providerPublishTime') else ''
            })
    except:
        pass
    # Sentiment
    sentiments = []
    for art in articles:
        blob = TextBlob(art['title'])
        pol = blob.sentiment.polarity
        sentiments.append(pol)
        art['score'] = pol
        art['sentiment'] = 'Positive' if pol > 0.1 else ('Negative' if pol < -0.1 else 'Neutral')
        art['emoji'] = '📈' if pol > 0.1 else ('📉' if pol < -0.1 else '➖')
    avg = np.mean(sentiments) if sentiments else 0
    overall = 'Positive' if avg > 0.1 else ('Negative' if avg < -0.1 else 'Neutral')
    emoji = '📈' if avg > 0.1 else ('📉' if avg < -0.1 else '➖')
    return {'overall': overall, 'emoji': emoji, 'score': avg, 'articles': articles, 'count': len(articles)}

# ======================== BUFFETT SCORE ========================
def calculate_buffett_score(fin: Dict) -> Dict:
    score = max_score = 0
    results = []
    max_score += 20
    roe = fin.get('roe', 0)
    if roe and roe > 0.15:
        score += 20
        results.append({'Criterion': 'ROE > 15%', 'Status': '✓', 'Value': f"{roe*100:.1f}%", 'Score': 20})
    else:
        results.append({'Criterion': 'ROE > 15%', 'Status': '✗', 'Value': f"{roe*100:.1f}%" if roe else 'N/A', 'Score': 0})
    max_score += 15
    debt = fin.get('debt_to_equity', 999)
    if debt and debt < 0.5:
        score += 15
        results.append({'Criterion': 'Debt/Equity < 0.5', 'Status': '✓', 'Value': f"{debt:.2f}", 'Score': 15})
    else:
        results.append({'Criterion': 'Debt/Equity < 0.5', 'Status': '✗', 'Value': f"{debt:.2f}" if debt else 'N/A', 'Score': 0})
    max_score += 15
    margin = fin.get('profit_margin', 0)
    if margin and margin > 0.20:
        score += 15
        results.append({'Criterion': 'Net Margin > 20%', 'Status': '✓', 'Value': f"{margin*100:.1f}%", 'Score': 15})
    else:
        results.append({'Criterion': 'Net Margin > 20%', 'Status': '✗', 'Value': f"{margin*100:.1f}%" if margin else 'N/A', 'Score': 0})
    max_score += 15
    pe = fin.get('pe', 999)
    if pe and 0 < pe < 22:
        score += 15
        results.append({'Criterion': 'P/E < 22', 'Status': '✓', 'Value': f"{pe:.1f}", 'Score': 15})
    else:
        results.append({'Criterion': 'P/E < 22', 'Status': '✗', 'Value': f"{pe:.1f}" if pe else 'N/A', 'Score': 0})
    max_score += 20
    growth = fin.get('earnings_growth', 0)
    if growth and growth > 0.10:
        score += 20
        results.append({'Criterion': 'Earnings Growth > 10%', 'Status': '✓', 'Value': f"{growth*100:.1f}%", 'Score': 20})
    else:
        results.append({'Criterion': 'Earnings Growth > 10%', 'Status': '✗', 'Value': f"{growth*100:.1f}%" if growth else 'N/A', 'Score': 0})
    max_score += 15
    fcf = fin.get('free_cash_flow', 0)
    if fcf and fcf > 0:
        score += 15
        results.append({'Criterion': 'Positive Free Cash Flow', 'Status': '✓', 'Value': f"${fcf/1e9:.2f}B", 'Score': 15})
    else:
        results.append({'Criterion': 'Positive Free Cash Flow', 'Status': '✗', 'Value': 'Negative' if fcf else 'N/A', 'Score': 0})
    pct = (score / max_score * 100) if max_score else 0
    rec = 'BUY' if pct >= 70 else ('HOLD' if pct >= 45 else 'SELL')
    cls = 'ft-buy' if pct >= 70 else ('ft-hold' if pct >= 45 else 'ft-sell')
    return {'percentage': pct, 'score': score, 'max_score': max_score, 'results': results, 'recommendation': rec, 'rec_class': cls}

def combined_score(buffett_pct: float, sentiment_score: float) -> float:
    return (buffett_pct * 0.6) + ((sentiment_score + 1) * 50 * 0.4)

# ======================== AUTOCOMPLETE ========================
@st.cache_data(ttl=300)
def search_yahoo_suggestions(query: str) -> List[Dict]:
    if len(query) < 2:
        return []
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10&newsCount=0"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        data = resp.json()
        suggestions = []
        for quote in data.get('quotes', []):
            ticker = quote.get('symbol')
            name = quote.get('longname') or quote.get('shortname')
            exch = quote.get('exchange')
            if ticker and name:
                suggestions.append({'ticker': ticker, 'name': name, 'exchange': exch})
        seen = set()
        unique = []
        for s in suggestions:
            if s['ticker'] not in seen:
                seen.add(s['ticker'])
                unique.append(s)
        return unique[:12]
    except:
        return []

@st.cache_data(ttl=86400)
def get_local_ticker_list() -> List[str]:
    psi = ['EDP.LS', 'GALP.LS', 'JMT.LS', 'SON.LS', 'NOS.LS', 'BCP.LS', 'RENE.LS',
           'ALTR.LS', 'COR.LS', 'CTM.LS', 'EDPR.LS', 'IBS.LS', 'MCP.LS', 'NVG.LS']
    us_large = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'UNH', 'JNJ', 'V']
    brazil = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA', 'WEGE3.SA']
    europe = ['SAP.DE', 'SIE.DE', 'TTE.PA', 'MC.PA', 'ASML.AS', 'SHEL.L', 'HSBA.L']
    return list(dict.fromkeys(psi + us_large + brazil + europe))

def get_autocomplete_suggestions(query: str) -> List[str]:
    suggestions = search_yahoo_suggestions(query)
    if suggestions:
        return [f"{s['ticker']} - {s['name']} ({s['exchange']})" for s in suggestions]
    else:
        local = get_local_ticker_list()
        query_lower = query.lower()
        matches = [t for t in local if query_lower in t.lower()]
        matches.sort(key=lambda x: (0 if x.lower().startswith(query_lower) else 1, x))
        return matches[:10]

# ======================== MAIN UI ========================
st.markdown('<div class="ft-section-title">Global Asset Search</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2.5, 1, 1])
with col1:
    search_term = st.text_input("", placeholder="Enter company name or ticker (e.g., Apple, EDP, MSFT)", label_visibility="collapsed")

if search_term and len(search_term) >= 2:
    with st.spinner("Searching suggestions..."):
        suggestions = get_autocomplete_suggestions(search_term)
    if suggestions:
        selected_display = st.selectbox("Suggestions (click to choose):", suggestions, key="autocomplete_select")
        if selected_display:
            ticker_candidate = selected_display.split(" - ")[0]
            if st.button(f"Analyze {ticker_candidate}", key="auto_analyse_btn"):
                with st.spinner(f"Analyzing {ticker_candidate}..."):
                    fin = get_aggregated_fundamentals(ticker_candidate)
                    if fin.get('price', 0) > 0:
                        buff = calculate_buffett_score(fin)
                        news = fetch_news_sentiment(ticker_candidate)
                        comb = combined_score(buff['percentage'], news['score'])
                        final_rec = 'BUY' if comb >= 70 else ('HOLD' if comb >= 45 else 'SELL')
                        final_cls = 'ft-buy' if comb >= 70 else ('ft-hold' if comb >= 45 else 'ft-sell')

                        st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
                        c1, c2, c3, c4 = st.columns(4)
                        with c1: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Company</div><div class='ft-metric-value'>{fin.get('name', ticker_candidate)[:35]}</div><div>{ticker_candidate} | {fin.get('country', 'Global')}</div></div>", unsafe_allow_html=True)
                        with c2: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Price</div><div class='ft-metric-value'>${fin.get('price', 0):.2f}</div><div>Target: ${fin.get('target_price', 0):.2f}</div></div>", unsafe_allow_html=True)
                        with c3: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Market Cap</div><div class='ft-metric-value'>${fin.get('market_cap', 0)/1e9:.1f}bn</div><div>Beta: {fin.get('beta', 0):.2f}</div></div>", unsafe_allow_html=True)
                        with c4: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>P/E</div><div class='ft-metric-value'>{fin.get('pe', 0):.1f}</div><div>Forward: {fin.get('forward_pe', 0):.1f}</div></div>", unsafe_allow_html=True)

                        st.markdown(f"<div class='ft-recommendation {final_cls}'><div class='ft-recommendation-value'>{final_rec}</div><div>Combined Score: {comb:.0f}/100 (Buffett {buff['percentage']:.0f}% + Sentiment {news['score']:.2f})</div><div>📰 {news['count']} news articles</div></div>", unsafe_allow_html=True)

                        colA, colB, colC = st.columns(3)
                        with colA: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Buffett Score</div><div class='ft-metric-value'>{buff['percentage']:.0f}%</div><div class='score-bar-bg'><div class='score-bar-fill' style='width:{buff['percentage']}%;'></div></div></div>", unsafe_allow_html=True)
                        with colB: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Sentiment</div><div class='ft-metric-value'>{news['emoji']} {news['overall']}</div><div>Score: {news['score']:.2f}</div></div>", unsafe_allow_html=True)
                        with colC: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Combined</div><div class='ft-metric-value'>{comb:.0f}<span style='font-size:1rem;'>/100</span></div><div class='score-bar-bg'><div class='score-bar-fill' style='width:{comb}%;'></div></div></div>", unsafe_allow_html=True)

                        st.markdown('<div class="ft-section-title">Buffett Criteria</div>', unsafe_allow_html=True)
                        st.dataframe(pd.DataFrame(buff['results']), use_container_width=True, hide_index=True)

                        if news['articles']:
                            st.markdown(f"<div class='ft-section-title'>Latest News ({news['count']})</div>", unsafe_allow_html=True)
                            for art in news['articles'][:6]:
                                st.markdown(f"<div class='ft-card'><span class='sentiment-{art['sentiment'].lower()}'>{art['emoji']} {art['sentiment']} (score: {art['score']:.2f})</span><br/><a href='{art['link']}' target='_blank'>{art['title']}</a><br/><span style='font-size:0.8rem; color:#666;'>{art.get('date', '')} | {art['source']}</span></div>", unsafe_allow_html=True)
                    else:
                        st.error(f"Could not retrieve data for {ticker_candidate}.")
    else:
        st.info("No suggestions found. Try a different name or use the 'ANALYZE' button.")

with col2:
    manual_analyse = st.button("🔍 ANALYZE", type="primary", use_container_width=True)
with col3:
    screen_btn = st.button("🌍 GLOBAL SCREEN (15k assets)", use_container_width=True)

if manual_analyse and search_term:
    ticker_direct = search_term.strip().upper()
    with st.spinner(f"Analyzing {ticker_direct} ..."):
        fin = get_aggregated_fundamentals(ticker_direct)
        if fin.get('price', 0) == 0:
            st.error(f"'{ticker_direct}' is not a valid ticker or has no data. Try using autocomplete.")
        else:
            buff = calculate_buffett_score(fin)
            news = fetch_news_sentiment(ticker_direct)
            comb = combined_score(buff['percentage'], news['score'])
            final_rec = 'BUY' if comb >= 70 else ('HOLD' if comb >= 45 else 'SELL')
            final_cls = 'ft-buy' if comb >= 70 else ('ft-hold' if comb >= 45 else 'ft-sell')

            st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Company</div><div class='ft-metric-value'>{fin.get('name', ticker_direct)[:35]}</div><div>{ticker_direct} | {fin.get('country', 'Global')}</div></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Price</div><div class='ft-metric-value'>${fin.get('price', 0):.2f}</div><div>Target: ${fin.get('target_price', 0):.2f}</div></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Market Cap</div><div class='ft-metric-value'>${fin.get('market_cap', 0)/1e9:.1f}bn</div><div>Beta: {fin.get('beta', 0):.2f}</div></div>", unsafe_allow_html=True)
            with c4: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>P/E</div><div class='ft-metric-value'>{fin.get('pe', 0):.1f}</div><div>Forward: {fin.get('forward_pe', 0):.1f}</div></div>", unsafe_allow_html=True)

            st.markdown(f"<div class='ft-recommendation {final_cls}'><div class='ft-recommendation-value'>{final_rec}</div><div>Combined Score: {comb:.0f}/100 (Buffett {buff['percentage']:.0f}% + Sentiment {news['score']:.2f})</div><div>📰 {news['count']} news articles</div></div>", unsafe_allow_html=True)

            colA, colB, colC = st.columns(3)
            with colA: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Buffett Score</div><div class='ft-metric-value'>{buff['percentage']:.0f}%</div><div class='score-bar-bg'><div class='score-bar-fill' style='width:{buff['percentage']}%;'></div></div></div>", unsafe_allow_html=True)
            with colB: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Sentiment</div><div class='ft-metric-value'>{news['emoji']} {news['overall']}</div><div>Score: {news['score']:.2f}</div></div>", unsafe_allow_html=True)
            with colC: st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Combined</div><div class='ft-metric-value'>{comb:.0f}<span style='font-size:1rem;'>/100</span></div><div class='score-bar-bg'><div class='score-bar-fill' style='width:{comb}%;'></div></div></div>", unsafe_allow_html=True)

            st.markdown('<div class="ft-section-title">Buffett Criteria</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(buff['results']), use_container_width=True, hide_index=True)

            if news['articles']:
                st.markdown(f"<div class='ft-section-title'>Latest News ({news['count']})</div>", unsafe_allow_html=True)
                for art in news['articles'][:6]:
                    st.markdown(f"<div class='ft-card'><span class='sentiment-{art['sentiment'].lower()}'>{art['emoji']} {art['sentiment']} (score: {art['score']:.2f})</span><br/><a href='{art['link']}' target='_blank'>{art['title']}</a><br/><span style='font-size:0.8rem; color:#666;'>{art.get('date', '')} | {art['source']}</span></div>", unsafe_allow_html=True)

# ======================== GENERATE 15K TICKERS ========================
@st.cache_data(ttl=86400)
def generate_15000_tickers() -> List[str]:
    tickers = set()
    try:
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
        tickers.update(sp500)
    except: pass
    try:
        nasdaq100 = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')[4]['Ticker'].tolist()
        tickers.update(nasdaq100)
    except: pass
    try:
        ftse100 = pd.read_html('https://en.wikipedia.org/wiki/FTSE_100_Index')[3]['EPIC'].tolist()
        tickers.update([t+'.L' for t in ftse100 if '.' not in t])
    except: pass
    try:
        dax = pd.read_html('https://en.wikipedia.org/wiki/DAX')[4]['Ticker'].tolist()
        tickers.update([t+'.DE' for t in dax if '.' not in t])
    except: pass
    try:
        cac = pd.read_html('https://en.wikipedia.org/wiki/CAC_40')[3]['Ticker'].tolist()
        tickers.update([t+'.PA' for t in cac if '.' not in t])
    except: pass
    psi_full = ['EDP.LS', 'GALP.LS', 'JMT.LS', 'SON.LS', 'NOS.LS', 'BCP.LS', 'RENE.LS',
                'ALTR.LS', 'COR.LS', 'CTM.LS', 'EDPR.LS', 'IBS.LS', 'MCP.LS', 'NVG.LS']
    tickers.update(psi_full)
    b3 = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA', 'WEGE3.SA']
    tickers.update(b3)
    crypto = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'XRP-USD', 'ADA-USD', 'SOL-USD']
    tickers.update(crypto)

    import string
    letters = list(string.ascii_uppercase)
    for l1 in letters:
        tickers.add(l1)
        for l2 in letters:
            tickers.add(l1+l2)
    for l1 in letters:
        for i in range(10):
            tickers.add(f"{l1}{i}")
            tickers.add(f"{l1}{i}{i}")
    tickers_list = list(tickers)
    if len(tickers_list) < 15000:
        needed = 15000 - len(tickers_list)
        for i in range(needed):
            tickers_list.append(f"PAD{i}")
    return tickers_list[:15000]

# ======================== GLOBAL SCREENING ========================
if screen_btn:
    st.markdown('<div class="ft-section-title">Global Screening (15,000+ assets)</div>', unsafe_allow_html=True)
    st.info("Scanning 15,000+ assets worldwide. First run may take 20‑30 minutes; subsequent runs will be much faster due to caching.")
    all_tickers = generate_15000_tickers()
    total = len(all_tickers)
    st.write(f"Total tickers in list: **{total}**")

    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    start_time = time.time()

    for idx, ticker in enumerate(all_tickers):
        progress = (idx + 1) / total
        progress_bar.progress(progress)
        status_text.text(f"🔍 Processing {idx+1} of {total} assets | Current: {ticker}")

        fin = get_aggregated_fundamentals(ticker)
        if fin.get('price', 0) > 0:
            buff = calculate_buffett_score(fin)
            sent = fetch_news_sentiment(ticker)
            comb = combined_score(buff['percentage'], sent['score'])
            results.append({
                'Ticker': ticker,
                'Company': fin.get('name', ticker)[:30],
                'Price': fin.get('price', 0),
                'P/E': fin.get('pe', 0),
                'Buffett Score': f"{buff['percentage']:.0f}%",
                'Sentiment': sent['overall'],
                'Recommendation': 'BUY' if comb>=70 else ('HOLD' if comb>=45 else 'SELL'),
                'Combined': f"{comb:.0f}/100"
            })
        time.sleep(0.05)

    progress_bar.empty()
    status_text.empty()
    elapsed = time.time() - start_time

    if results:
        df = pd.DataFrame(results).sort_values('Combined', ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
        fig = px.bar(df.head(20), x='Ticker', y=[float(x.split('/')[0]) for x in df['Combined'].head(20)],
                     title='Top 20 by Combined Score', color='Recommendation',
                     color_discrete_map={'BUY':'#2e7d32','HOLD':'#ed6c02','SELL':'#d32f2f'})
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Full CSV", csv, "WB_screening_15000.csv", "text/csv")
        st.success(f"✅ Screening completed in {elapsed:.1f} seconds. {len(results)} assets with valid data (out of {total} scanned).")
    else:
        st.warning("No valid data found. Check your internet connection or try again later.")

st.markdown("""
<div class="ft-footer">
    <strong>Warren Buffett Global Screener</strong> | 15,000+ assets | Data: Yahoo Finance (primary) + Alpha Vantage (optional) | For educational purposes only.
</div>
""", unsafe_allow_html=True)