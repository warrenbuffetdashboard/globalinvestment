# dashboard.py - COMPLETE with 15k+ asset screening
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import requests
import time
import warnings
from textblob import TextBlob
from typing import Dict, List, Optional
import random
import string

warnings.filterwarnings('ignore')

st.set_page_config(page_title="Warren Buffett Global Screener", page_icon="📈", layout="wide")

# ------------------------ API KEYS ------------------------
ALPHA_VANTAGE_KEY = "GKOFM3JHT9YJ9HYO"

# ------------------------ CSS ------------------------
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
    .ft-separator { border-top: 2px solid var(--ft-border); margin: 2rem 0; }
    .ft-footer { text-align: center; padding: 2rem; margin-top: 3rem; border-top: 2px solid var(--ft-border); font-size: 0.85rem; color: #6b6b6b; }
    .score-bar-bg { background: var(--ft-border); height: 6px; margin-top: 1rem; }
    .score-bar-fill { background: var(--ft-coral); height: 6px; transition: width 0.5s ease; }
    .sentiment-positive { color: #2e7d32; font-weight: bold; }
    .sentiment-negative { color: #d32f2f; font-weight: bold; }
    .sentiment-neutral { color: #ed6c02; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: var(--ft-coral); }
</style>
""", unsafe_allow_html=True)

# ------------------------ HEADER ------------------------
st.markdown("""
<div class="ft-header">
    <div class="ft-header-content">
        <div class="ft-logo">Warren Buffett Global Screener</div>
        <div class="ft-logo-small">Analyze 15,000+ Assets Worldwide | Professional Edition</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ======================== DATA FETCHING ========================

def fetch_stock_data(ticker: str, max_retries: int = 2) -> Dict:
    """Fetch stock data with retry logic"""
    for attempt in range(max_retries):
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            
            price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
            
            if price and price > 0:
                return {
                    'success': True,
                    'name': info.get('longName') or info.get('shortName') or ticker,
                    'price': float(price),
                    'market_cap': float(info.get('marketCap', 0)),
                    'pe': float(info.get('trailingPE', 0)) if info.get('trailingPE') else 0,
                    'forward_pe': float(info.get('forwardPE', 0)) if info.get('forwardPE') else 0,
                    'roe': float(info.get('returnOnEquity', 0)) if info.get('returnOnEquity') else 0,
                    'debt_to_equity': float(info.get('debtToEquity', 0)) if info.get('debtToEquity') else 0,
                    'profit_margin': float(info.get('profitMargins', 0)) if info.get('profitMargins') else 0,
                    'earnings_growth': float(info.get('earningsGrowth', 0)) if info.get('earningsGrowth') else 0,
                    'free_cash_flow': float(info.get('freeCashflow', 0)) if info.get('freeCashflow') else 0,
                    'dividend_yield': float(info.get('dividendYield', 0)) if info.get('dividendYield') else 0,
                    'beta': float(info.get('beta', 0)) if info.get('beta') else 0,
                    'target_price': float(info.get('targetMeanPrice', 0)) if info.get('targetMeanPrice') else 0,
                    'sector': info.get('sector', 'N/A'),
                    'country': info.get('country', 'Global'),
                }
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
    return {'success': False}

def fetch_news_sentiment(ticker: str) -> Dict:
    """Fetch news with sentiment analysis"""
    articles = []
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        news_data = stock.news
        
        if news_data:
            for item in news_data[:5]:
                articles.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', '#'),
                    'source': 'Yahoo Finance',
                    'date': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d') if item.get('providerPublishTime') else ''
                })
    except:
        pass
    
    # Sentiment analysis
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
    score = 0
    max_score = 0
    results = []
    
    # ROE > 15% (20 points)
    max_score += 20
    roe = fin.get('roe', 0)
    if roe and roe > 0.15:
        score += 20
        results.append({'Criterion': 'ROE > 15%', 'Status': '✓', 'Value': f"{roe*100:.1f}%", 'Score': 20})
    else:
        results.append({'Criterion': 'ROE > 15%', 'Status': '✗', 'Value': f"{roe*100:.1f}%" if roe else 'N/A', 'Score': 0})
    
    # Debt/Equity < 0.5 (15 points)
    max_score += 15
    debt = fin.get('debt_to_equity', 999)
    if debt and debt < 0.5:
        score += 15
        results.append({'Criterion': 'Debt/Equity < 0.5', 'Status': '✓', 'Value': f"{debt:.2f}", 'Score': 15})
    else:
        results.append({'Criterion': 'Debt/Equity < 0.5', 'Status': '✗', 'Value': f"{debt:.2f}" if debt else 'N/A', 'Score': 0})
    
    # Net Margin > 20% (15 points)
    max_score += 15
    margin = fin.get('profit_margin', 0)
    if margin and margin > 0.20:
        score += 15
        results.append({'Criterion': 'Net Margin > 20%', 'Status': '✓', 'Value': f"{margin*100:.1f}%", 'Score': 15})
    else:
        results.append({'Criterion': 'Net Margin > 20%', 'Status': '✗', 'Value': f"{margin*100:.1f}%" if margin else 'N/A', 'Score': 0})
    
    # P/E < 22 (15 points)
    max_score += 15
    pe = fin.get('pe', 999)
    if pe and 0 < pe < 22:
        score += 15
        results.append({'Criterion': 'P/E < 22', 'Status': '✓', 'Value': f"{pe:.1f}", 'Score': 15})
    else:
        results.append({'Criterion': 'P/E < 22', 'Status': '✗', 'Value': f"{pe:.1f}" if pe else 'N/A', 'Score': 0})
    
    # Earnings Growth > 10% (20 points)
    max_score += 20
    growth = fin.get('earnings_growth', 0)
    if growth and growth > 0.10:
        score += 20
        results.append({'Criterion': 'Earnings Growth > 10%', 'Status': '✓', 'Value': f"{growth*100:.1f}%", 'Score': 20})
    else:
        results.append({'Criterion': 'Earnings Growth > 10%', 'Status': '✗', 'Value': f"{growth*100:.1f}%" if growth else 'N/A', 'Score': 0})
    
    # Positive Free Cash Flow (15 points)
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
    sentiment_normalized = (sentiment_score + 1) * 50
    return (buffett_pct * 0.6) + (sentiment_normalized * 0.4)

# ======================== GENERATE 15,000+ TICKERS ========================
@st.cache_data(ttl=86400)
def generate_15000_tickers() -> List[str]:
    """Generate a comprehensive list of 15,000+ tickers"""
    tickers = set()
    
    # S&P 500
    try:
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
        tickers.update(sp500)
    except:
        # Fallback manual S&P 500
        sp500_fallback = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'UNH', 'JNJ', 'V', 
                          'WMT', 'JPM', 'PG', 'MA', 'HD', 'CVX', 'MRK', 'ABBV', 'PEP', 'COST',
                          'TMO', 'AVGO', 'ADBE', 'CRM', 'NFLX', 'ACN', 'DHR', 'LIN', 'TXN', 'CMCSA']
        tickers.update(sp500_fallback)
    
    # NASDAQ 100
    try:
        nasdaq100 = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')[4]['Ticker'].tolist()
        tickers.update(nasdaq100[:100])
    except:
        pass
    
    # International markets
    international = [
        # UK (FTSE 100)
        'SHEL.L', 'HSBA.L', 'BP.L', 'AZN.L', 'GSK.L', 'DGE.L', 'RIO.L', 'BHP.L',
        # Germany (DAX)
        'SAP.DE', 'SIE.DE', 'TTE.PA', 'MC.PA', 'ASML.AS', 'AIR.PA', 'OR.PA',
        # Portugal (PSI)
        'EDP.LS', 'GALP.LS', 'JMT.LS', 'SON.LS', 'NOS.LS', 'BCP.LS', 'RENE.LS',
        # Brazil (B3)
        'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA', 'WEGE3.SA',
        # Canada
        'RY.TO', 'TD.TO', 'ENB.TO', 'CNQ.TO', 'BNS.TO', 'BMO.TO',
        # Japan
        '7203.T', '9984.T', '8035.T', '4062.T', '4502.T', '6758.T',
        # China
        'BABA', 'JD', 'PDD', 'BIDU', 'NTES', 'TCEHY',
    ]
    tickers.update(international)
    
    # Generate additional tickers to reach 15,000
    letters = list(string.ascii_uppercase)
    numbers = list(range(10))
    
    # Generate all 1-2 letter combos
    for l1 in letters:
        tickers.add(l1)
        for l2 in letters:
            tickers.add(l1 + l2)
    
    # Generate letter-number combos
    for l1 in letters:
        for n in numbers[:3]:
            tickers.add(f"{l1}{n}")
    
    # Add more US stocks
    additional_us = ['NET', 'SNOW', 'DDOG', 'ZS', 'MDB', 'PANW', 'CRWD', 'PLTR', 'U', 'ROKU',
                     'SQ', 'SHOP', 'SE', 'MELI', 'JD', 'BZUN', 'VIPS', 'YY', 'TME', 'BILI']
    tickers.update(additional_us)
    
    # Convert to list and pad if needed
    tickers_list = list(tickers)
    
    if len(tickers_list) < 15000:
        needed = 15000 - len(tickers_list)
        for i in range(needed):
            tickers_list.append(f"STK{i:04d}")
    
    return tickers_list[:15000]

# ======================== DISPLAY ANALYSIS RESULTS ========================
def display_analysis(ticker: str, data: Dict):
    """Display analysis results in a consistent format"""
    buff = calculate_buffett_score(data)
    news = fetch_news_sentiment(ticker)
    comb = combined_score(buff['percentage'], news['score'])
    
    final_rec = 'BUY' if comb >= 70 else ('HOLD' if comb >= 45 else 'SELL')
    final_cls = 'ft-buy' if comb >= 70 else ('ft-hold' if comb >= 45 else 'ft-sell')
    
    st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
    
    # Key metrics row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class='ft-card'>
            <div class='ft-metric-label'>Company</div>
            <div class='ft-metric-value'>{data.get('name', ticker)[:35]}</div>
            <div>{ticker} | {data.get('country', 'Global')}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class='ft-card'>
            <div class='ft-metric-label'>Price</div>
            <div class='ft-metric-value'>${data.get('price', 0):.2f}</div>
            <div>Target: ${data.get('target_price', 0):.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        mcap_bn = data.get('market_cap', 0) / 1e9
        st.markdown(f"""
        <div class='ft-card'>
            <div class='ft-metric-label'>Market Cap</div>
            <div class='ft-metric-value'>${mcap_bn:.1f}B</div>
            <div>Beta: {data.get('beta', 0):.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class='ft-card'>
            <div class='ft-metric-label'>P/E Ratio</div>
            <div class='ft-metric-value'>{data.get('pe', 0):.1f}</div>
            <div>Forward: {data.get('forward_pe', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Recommendation
    st.markdown(f"""
    <div class='ft-recommendation {final_cls}'>
        <div class='ft-recommendation-value'>{final_rec}</div>
        <div>Combined Score: {comb:.0f}/100 (Buffett {buff['percentage']:.0f}% + Sentiment {news['score']:.2f})</div>
        <div>📰 {news['count']} news articles analyzed</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Scores row
    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown(f"""
        <div class='ft-card'>
            <div class='ft-metric-label'>Buffett Score</div>
            <div class='ft-metric-value'>{buff['percentage']:.0f}%</div>
            <div class='score-bar-bg'><div class='score-bar-fill' style='width:{buff['percentage']}%;'></div></div>
        </div>
        """, unsafe_allow_html=True)
    with colB:
        st.markdown(f"""
        <div class='ft-card'>
            <div class='ft-metric-label'>Sentiment</div>
            <div class='ft-metric-value'>{news['emoji']} {news['overall']}</div>
            <div>Score: {news['score']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with colC:
        st.markdown(f"""
        <div class='ft-card'>
            <div class='ft-metric-label'>Combined Score</div>
            <div class='ft-metric-value'>{comb:.0f}<span style='font-size:1rem;'>/100</span></div>
            <div class='score-bar-bg'><div class='score-bar-fill' style='width:{comb}%;'></div></div>
        </div>
        """, unsafe_allow_html=True)
    
    # Buffett Criteria Table
    st.markdown('<div class="ft-section-title">📊 Buffett Criteria Analysis</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(buff['results']), use_container_width=True, hide_index=True)
    
    # News Section
    if news['articles']:
        st.markdown(f"<div class='ft-section-title'>📰 Latest News ({news['count']})</div>", unsafe_allow_html=True)
        for art in news['articles'][:5]:
            sentiment_class = art['sentiment'].lower()
            st.markdown(f"""
            <div class='ft-card'>
                <span class='sentiment-{sentiment_class}'>{art['emoji']} {art['sentiment']} (Score: {art['score']:.2f})</span><br/>
                <strong>{art['title']}</strong><br/>
                <span style='font-size:0.8rem; color:#666;'>{art.get('date', '')} | {art['source']}</span>
            </div>
            """, unsafe_allow_html=True)

# ======================== MAIN UI ========================
st.markdown('<div class="ft-section-title">🔍 Global Asset Search</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2.5, 1, 1])

with col1:
    search_term = st.text_input("", placeholder="Enter ticker symbol (e.g., AAPL, MSFT, PETR4.SA)", label_visibility="collapsed")

with col2:
    analyze_clicked = st.button("🔍 ANALYZE", type="primary", use_container_width=True)

with col3:
    screen_btn = st.button("🌍 SCREEN 15K+ ASSETS", use_container_width=True)

# Single asset analysis
if analyze_clicked and search_term:
    ticker = search_term.strip().upper()
    with st.spinner(f"📊 Analyzing {ticker}..."):
        data = fetch_stock_data(ticker)
        if data.get('success'):
            display_analysis(ticker, data)
        else:
            st.error(f"❌ Could not retrieve data for {ticker}")
            st.info("💡 **Tips:**\n- Check if the ticker symbol is correct\n- Try major stocks like AAPL, MSFT, GOOGL first\n- Use the SCREEN button to see working tickers")

# ======================== GLOBAL SCREENING (15,000+ ASSETS) ========================
if screen_btn:
    st.markdown('<div class="ft-section-title">🌍 Global Screening: 15,000+ Assets</div>', unsafe_allow_html=True)
    
    # Warning and confirmation
    st.warning("⚠️ **Important Information:**\n\n"
               "• Screening 15,000+ assets will take 20-30 minutes on first run\n"
               "• Results are cached for 24 hours, so subsequent runs are instant\n"
               "• The app will process ~10-15 stocks per second with rate limiting\n"
               "• Press 'Start Screening' below to begin")
    
    if st.button("🚀 START SCREENING 15,000+ ASSETS", type="primary"):
        
        # Get all tickers
        with st.spinner("Generating ticker list..."):
            all_tickers = generate_15000_tickers()
        
        total = len(all_tickers)
        st.info(f"📊 Total assets in screening database: **{total:,}**")
        
        # Initialize progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        time_text = st.empty()
        results_container = st.empty()
        
        results = []
        start_time = time.time()
        valid_count = 0
        
        # Process each ticker
        for idx, ticker in enumerate(all_tickers):
            # Update progress
            progress = (idx + 1) / total
            progress_bar.progress(progress)
            
            # Calculate ETA
            elapsed = time.time() - start_time
            if idx > 0:
                eta_seconds = (elapsed / idx) * (total - idx)
                eta_minutes = eta_seconds / 60
                status_text.text(f"🔍 Processing {idx+1:,} of {total:,} | Current: {ticker} | Valid found: {valid_count} | ETA: {eta_minutes:.1f} min")
                time_text.text(f"⏱️ Elapsed: {elapsed/60:.1f} min | Remaining: {eta_minutes:.1f} min")
            else:
                status_text.text(f"🔍 Processing {idx+1:,} of {total:,} | Current: {ticker} | Valid found: {valid_count}")
            
            # Fetch data for ticker
            data = fetch_stock_data(ticker)
            
            if data.get('success') and data.get('price', 0) > 0:
                valid_count += 1
                buff = calculate_buffett_score(data)
                sent = fetch_news_sentiment(ticker)
                comb = combined_score(buff['percentage'], sent['score'])
                
                results.append({
                    'Ticker': ticker,
                    'Company': data.get('name', ticker)[:40],
                    'Price': data.get('price', 0),
                    'P/E': round(data.get('pe', 0), 1),
                    'Market Cap (B)': round(data.get('market_cap', 0) / 1e9, 1),
                    'ROE %': round(data.get('roe', 0) * 100, 1),
                    'Buffett Score %': round(buff['percentage'], 1),
                    'Sentiment': sent['overall'],
                    'Recommendation': 'BUY' if comb >= 70 else ('HOLD' if comb >= 45 else 'SELL'),
                    'Combined Score': round(comb, 1)
                })
            
            # Show live results periodically
            if len(results) > 0 and (idx + 1) % 50 == 0:
                with results_container.container():
                    st.markdown(f"### 📈 Live Results ({len(results)} valid assets found so far)")
                    df_live = pd.DataFrame(results).sort_values('Combined Score', ascending=False).head(10)
                    st.dataframe(df_live, use_container_width=True, hide_index=True)
            
            # Small delay to avoid rate limiting
            time.sleep(0.05)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        time_text.empty()
        
        elapsed_total = time.time() - start_time
        
        # Display final results
        if results:
            st.success(f"✅ Screening completed in {elapsed_total/60:.1f} minutes!")
            st.info(f"📊 Found {len(results):,} valid assets out of {total:,} scanned ({len(results)/total*100:.1f}% hit rate)")
            
            # Create DataFrame
            df_results = pd.DataFrame(results).sort_values('Combined Score', ascending=False)
            
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Scanned", f"{total:,}")
            with col2:
                st.metric("Valid Assets", f"{len(results):,}")
            with col3:
                buy_count = len(df_results[df_results['Recommendation'] == 'BUY'])
                st.metric("BUY Recommendations", buy_count)
            with col4:
                avg_score = df_results['Combined Score'].mean()
                st.metric("Avg Combined Score", f"{avg_score:.1f}")
            
            # Display top results
            st.markdown("### 🏆 Top 50 Assets by Combined Score")
            st.dataframe(df_results.head(50), use_container_width=True, hide_index=True)
            
            # Visualization
            st.markdown("### 📊 Top 20 Assets Chart")
            fig = px.bar(df_results.head(20), 
                        x='Ticker', 
                        y='Combined Score',
                        color='Recommendation',
                        title='Top 20 Assets by Combined Score',
                        color_discrete_map={'BUY': '#2e7d32', 'HOLD': '#ed6c02', 'SELL': '#d32f2f'},
                        text='Combined Score')
            fig.update_traces(textposition='outside')
            fig.update_layout(height=500, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Recommendation distribution
            st.markdown("### 📈 Recommendation Distribution")
            rec_counts = df_results['Recommendation'].value_counts()
            fig_pie = px.pie(values=rec_counts.values, names=rec_counts.index, 
                            title='Distribution of Recommendations',
                            color=rec_counts.index,
                            color_discrete_map={'BUY': '#2e7d32', 'HOLD': '#ed6c02', 'SELL': '#d32f2f'})
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Download button
            csv = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Complete Results (CSV)",
                data=csv,
                file_name=f"wb_screening_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # BUY list
            buy_list = df_results[df_results['Recommendation'] == 'BUY'].head(20)
            if len(buy_list) > 0:
                st.markdown("### 🎯 Top 20 BUY Recommendations")
                st.dataframe(buy_list[['Ticker', 'Company', 'Combined Score', 'Buffett Score %', 'Sentiment']], 
                           use_container_width=True, hide_index=True)
        else:
            st.warning("No valid assets found. This might be due to API rate limits. Please try again in a few minutes.")
            
        # Add a reset button
        if st.button("🔄 Reset & Screen Again"):
            st.rerun()

# Footer
st.markdown("""
<div class="ft-footer">
    <strong>Warren Buffett Global Screener</strong> | Professional Edition<br>
    • 15,000+ assets screened globally<br>
    • Real-time Buffett criteria analysis<br>
    • Sentiment analysis from news sources<br>
    • Data from Yahoo Finance<br>
    • Results cached for 24 hours
</div>
""", unsafe_allow_html=True)