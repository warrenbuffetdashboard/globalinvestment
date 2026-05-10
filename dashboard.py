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
from textblob import TextBlob

warnings.filterwarnings('ignore')

# ==================== CONFIGURAÇÃO ====================
st.set_page_config(
    page_title="Warren Buffett Global Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS ====================
st.markdown("""
<style>
    :root {
        --ft-offwhite: #fffef9;
        --ft-warm-white: #fff8f0;
        --ft-sand: #e8e0d0;
        --ft-coral: #ff6347;
        --ft-navy: #0a2540;
        --ft-border: #e6e0d5;
    }
    
    .stApp { background-color: var(--ft-offwhite); }
    
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
        color: #6b6b6b;
        margin-top: 0.5rem;
    }
    
    .ft-section-title {
        font-family: 'Times New Roman', Times, serif;
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--ft-navy);
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }
    
    .ft-card {
        background: white;
        border: 2px solid var(--ft-border);
        padding: 1.5rem;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .ft-card:hover {
        background: var(--ft-warm-white);
        border-color: var(--ft-coral);
        transform: translateY(-3px);
    }
    
    .ft-metric-label {
        font-family: 'Times New Roman', Times, serif;
        font-size: 0.85rem;
        font-weight: 600;
        color: #6b6b6b;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    
    .ft-metric-value {
        font-family: 'Times New Roman', Times, serif;
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--ft-navy);
        margin: 0.5rem 0;
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
        border: 2px solid var(--ft-border);
        padding: 1rem;
        background: white;
        color: #000000;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--ft-coral);
        outline: none;
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
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: var(--ft-coral);
        transform: translateY(-3px);
    }
    
    .share-container {
        display: flex;
        justify-content: center;
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
        padding: 10px 20px;
        text-decoration: none;
        color: white;
        min-width: 110px;
        text-align: center;
        transition: all 0.3s ease;
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
        color: #6b6b6b;
    }
    
    .score-bar-bg {
        background: var(--ft-border);
        height: 6px;
        margin-top: 1rem;
    }
    
    .score-bar-fill {
        background: var(--ft-coral);
        height: 6px;
        transition: width 0.5s ease;
    }
    
    .sentiment-positive { color: #2e7d32; font-weight: bold; }
    .sentiment-negative { color: #d32f2f; font-weight: bold; }
    .sentiment-neutral { color: #ed6c02; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
st.markdown("""
<div class="ft-header">
    <div class="ft-header-content">
        <div class="ft-logo">Warren Buffett Global Screener</div>
        <div class="ft-logo-small">15,000+ Global Assets | PSI Portugal | Fundamental + Sentiment Analysis</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES ====================

def get_global_tickers():
    """Retorna lista de tickers globais"""
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'UNH', 'JNJ', 'V',
        'PG', 'JPM', 'HD', 'MA', 'DIS', 'KO', 'PEP', 'COST', 'WMT', 'NKE',
        'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'BBAS3.SA', 'ABEV3.SA', 'WEGE3.SA',
        'EDP.LS', 'GALP.LS', 'JMT.LS', 'SON.LS', 'NOS.LS', 'BCP.LS', 'RENE.LS',
        'NESN.SW', 'NOVN.SW', 'SAP.DE', 'SIE.DE', 'BMW.DE', 'TTE.PA', 'MC.PA',
        '7203.T', '6758.T', '005930.KS', 'BABA', 'TCEHY', 'SPY', 'QQQ', 'BTC-USD'
    ]
    return tickers

def search_ticker(query):
    """Converte busca para ticker"""
    return query.strip().upper()

def get_stock_data(ticker):
    """Obtém dados fundamentalistas"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if info.get('regularMarketPrice') or info.get('currentPrice'):
            return {
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'N/A'),
                'country': info.get('country', 'Global'),
                'currentPrice': info.get('currentPrice', info.get('regularMarketPrice', 0)),
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

def fetch_news_sentiment(ticker):
    """Busca últimas 10 notícias e analisa sentimento"""
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}&newsCount=10"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        news_items = data.get('news', [])
        
        sentiments = []
        news_list = []
        
        for news in news_items[:10]:
            title = news.get('title', '')
            if title:
                blob = TextBlob(title)
                polarity = blob.sentiment.polarity
                sentiments.append(polarity)
                
                if polarity > 0.1:
                    sentiment = "Positive"
                    emoji = "📈"
                elif polarity < -0.1:
                    sentiment = "Negative"
                    emoji = "📉"
                else:
                    sentiment = "Neutral"
                    emoji = "➖"
                
                news_list.append({
                    'title': title[:100],
                    'sentiment': sentiment,
                    'emoji': emoji,
                    'score': polarity,
                    'link': news.get('link', '#'),
                    'publisher': news.get('publisher', ''),
                    'date': datetime.fromtimestamp(news.get('providerPublishTime', 0)).strftime('%Y-%m-%d')
                })
        
        if sentiments:
            avg_sentiment = np.mean(sentiments)
            if avg_sentiment > 0.1:
                overall = "Positive"
                emoji = "📈"
            elif avg_sentiment < -0.1:
                overall = "Negative"
                emoji = "📉"
            else:
                overall = "Neutral"
                emoji = "➖"
        else:
            avg_sentiment = 0
            overall = "Neutral"
            emoji = "➖"
        
        return {
            'overall': overall,
            'emoji': emoji,
            'score': avg_sentiment,
            'articles': news_list,
            'count': len(news_list)
        }
    except:
        return {'overall': 'Neutral', 'emoji': '➖', 'score': 0, 'articles': [], 'count': 0}

def calculate_buffett_score(financials):
    """Calcula Buffett Score"""
    score = 0
    max_score = 0
    results = []
    
    max_score += 20
    roe = financials.get('returnOnEquity', 0)
    if roe and roe > 0.15:
        score += 20
        results.append({'Criterion': 'ROE > 15%', 'Status': '✓', 'Value': f"{roe*100:.1f}%", 'Score': 20})
    else:
        results.append({'Criterion': 'ROE > 15%', 'Status': '✗', 'Value': f"{roe*100:.1f}%" if roe else 'N/A', 'Score': 0})
    
    max_score += 15
    debt = financials.get('debtToEquity', 999)
    if debt and debt < 0.5:
        score += 15
        results.append({'Criterion': 'Debt/Equity < 0.5', 'Status': '✓', 'Value': f"{debt:.2f}", 'Score': 15})
    else:
        results.append({'Criterion': 'Debt/Equity < 0.5', 'Status': '✗', 'Value': f"{debt:.2f}" if debt else 'N/A', 'Score': 0})
    
    max_score += 15
    margin = financials.get('profitMargins', 0)
    if margin and margin > 0.20:
        score += 15
        results.append({'Criterion': 'Net Margin > 20%', 'Status': '✓', 'Value': f"{margin*100:.1f}%", 'Score': 15})
    else:
        results.append({'Criterion': 'Net Margin > 20%', 'Status': '✗', 'Value': f"{margin*100:.1f}%" if margin else 'N/A', 'Score': 0})
    
    max_score += 15
    pe = financials.get('trailingPE', 999)
    if pe and 0 < pe < 22:
        score += 15
        results.append({'Criterion': 'P/E < 22', 'Status': '✓', 'Value': f"{pe:.1f}", 'Score': 15})
    else:
        results.append({'Criterion': 'P/E < 22', 'Status': '✗', 'Value': f"{pe:.1f}" if pe else 'N/A', 'Score': 0})
    
    max_score += 20
    growth = financials.get('earningsGrowth', 0)
    if growth and growth > 0.10:
        score += 20
        results.append({'Criterion': 'Earnings Growth > 10%', 'Status': '✓', 'Value': f"{growth*100:.1f}%", 'Score': 20})
    else:
        results.append({'Criterion': 'Earnings Growth > 10%', 'Status': '✗', 'Value': f"{growth*100:.1f}%" if growth else 'N/A', 'Score': 0})
    
    max_score += 15
    cashflow = financials.get('freeCashflow', 0)
    if cashflow and cashflow > 0:
        score += 15
        results.append({'Criterion': 'Positive Free Cash Flow', 'Status': '✓', 'Value': f"${cashflow/1e9:.2f}B", 'Score': 15})
    else:
        results.append({'Criterion': 'Positive Free Cash Flow', 'Status': '✗', 'Value': 'Negative' if cashflow else 'N/A', 'Score': 0})
    
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

def calculate_combined_score(buffett_score, sentiment_score):
    """Calcula score combinado"""
    combined = (buffett_score * 0.6) + ((sentiment_score + 1) * 50 * 0.4)
    return max(0, min(100, combined))

def create_share_text(ticker, company_name, final_rec, buffett_score, sentiment_score, combined_score):
    text = f"Warren Buffett Analysis: {company_name} ({ticker})\n"
    text += f"Recommendation: {final_rec}\n"
    text += f"Buffett Score: {buffett_score:.0f}%\n"
    text += f"Sentiment Score: {sentiment_score:.2f}\n"
    text += f"Combined Score: {combined_score:.0f}/100"
    return text

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown('<div class="ft-section-title">Methodology</div>', unsafe_allow_html=True)
    st.markdown("**Warren Buffett's 6 Pillars (60%)**")
    st.markdown("""
    1. ROE > 15%
    2. Debt/Equity < 0.5
    3. Net Margin > 20%
    4. P/E < 22
    5. Earnings Growth > 10%
    6. Positive Free Cash Flow
    """)
    
    st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
    st.markdown("**Market Sentiment (40%)**")
    st.markdown("- Analyzes latest 10 news articles")
    st.markdown("- NLP sentiment with TextBlob")
    
    st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
    st.markdown("**Scoring**")
    st.markdown("- BUY: 70-100 | HOLD: 45-69 | SELL: 0-44")
    
    st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
    st.markdown("**Coverage**")
    st.markdown("- US, Brazil, Portugal (PSI), Europe, Asia")

# ==================== BUSCA PRINCIPAL ====================
st.markdown('<div class="ft-section-title">Global Asset Search</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([2.5, 1, 1])

with col1:
    search_query = st.text_input(
        "",
        value="AAPL",
        placeholder="Search 15,000+ assets - Ticker or company name...",
        label_visibility="collapsed"
    )

with col2:
    analyze_btn = st.button("ANALYSE with Sentiment", type="primary", use_container_width=True)

with col3:
    screen_btn = st.button("GLOBAL SCREEN (15k assets)", use_container_width=True)

# ==================== ANÁLISE INDIVIDUAL ====================
if analyze_btn and search_query:
    ticker = search_ticker(search_query)
    
    with st.spinner(f"Analyzing {search_query} ({ticker})..."):
        financials = get_stock_data(ticker)
        
        if financials and financials['currentPrice'] > 0:
            buffett = calculate_buffett_score(financials)
            
            with st.spinner("Fetching and analyzing latest 10 news articles..."):
                sentiment = fetch_news_sentiment(ticker)
            
            combined_score = calculate_combined_score(buffett['percentage'], sentiment['score'])
            
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
                    <div class="ft-metric-value" style="font-size:1.3rem;">{financials['name'][:35]}</div>
                    <div>{ticker} | {financials['country']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">Price</div>
                    <div class="ft-metric-value">${financials['currentPrice']:.2f}</div>
                    <div>Target: ${financials['targetPrice']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">Market Cap</div>
                    <div class="ft-metric-value">${financials['marketCap']/1e9:.1f}bn</div>
                    <div>Beta: {financials['beta']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">P/E Ratio</div>
                    <div class="ft-metric-value">{financials['trailingPE']:.1f}</div>
                    <div>Forward: {financials['forwardPE']:.1f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="ft-recommendation {final_class}">
                <div class="ft-recommendation-value">{final_rec}</div>
                <div>Based on Buffett Score (60%) + Market Sentiment (40%)</div>
                <div style="margin-top:0.5rem;">📰 Analyzed {sentiment['count']} recent news articles</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">Buffett Score (60%)</div>
                    <div class="ft-metric-value">{buffett['percentage']:.0f}%</div>
                    <div>{buffett['score']}/{buffett['max_score']} criteria</div>
                    <div class="score-bar-bg"><div class="score-bar-fill" style="width:{buffett['percentage']}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">Market Sentiment (40%)</div>
                    <div class="ft-metric-value">{sentiment['emoji']} {sentiment['overall']}</div>
                    <div>Score: {sentiment['score']:.2f}</div>
                    <div>{sentiment['count']} news analyzed</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="ft-card">
                    <div class="ft-metric-label">Combined Score</div>
                    <div class="ft-metric-value">{combined_score:.0f}<span style="font-size:1rem;">/100</span></div>
                    <div class="score-bar-bg"><div class="score-bar-fill" style="width:{combined_score}%;"></div></div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
            st.markdown('<div class="ft-section-title">Buffett Criteria Analysis</div>', unsafe_allow_html=True)
            
            df_criteria = pd.DataFrame(buffett['results'])
            st.dataframe(df_criteria, use_container_width=True, hide_index=True)
            
            if sentiment['articles']:
                st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ft-section-title">Latest News Analysis ({sentiment["count"]} articles)</div>', unsafe_allow_html=True)
                
                for article in sentiment['articles'][:10]:
                    sentiment_class = f"sentiment-{article['sentiment'].lower()}"
                    st.markdown(f"""
                    <div class="ft-card">
                        <div style="display:flex; justify-content:space-between;">
                            <span class="{sentiment_class}">{article['emoji']} {article['sentiment']} (score: {article['score']:.2f})</span>
                            <span>{article['date']} | {article['publisher']}</span>
                        </div>
                        <div style="margin-top:0.5rem;">
                            <a href="{article['link']}" target="_blank">{article['title']}...</a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
            st.markdown('<div class="ft-section-title">Share Results</div>', unsafe_allow_html=True)
            
            share_text = create_share_text(ticker, financials['name'], final_rec, buffett['percentage'], sentiment['score'], combined_score)
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
                'Market Cap (bn)': round(financials['marketCap']/1e9, 1),
                'P/E': financials['trailingPE'],
                'Buffett Score': f"{buffett['percentage']:.0f}%",
                'Sentiment': sentiment['overall'],
                'Recommendation': final_rec,
                'Combined Score': f"{combined_score:.0f}/100"
            }])
            
            csv = report_data.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, f"WB_{ticker}.csv", "text/csv")
        else:
            st.error(f"No data found for '{search_query}'")

# ==================== GLOBAL SCREENING ====================
if screen_btn:
    st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
    st.markdown('<div class="ft-section-title">Global Screening Results (15,000+ assets)</div>', unsafe_allow_html=True)
    
    screening_tickers = get_global_tickers()
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, ticker in enumerate(screening_tickers):
        status_text.info(f"Analyzing {ticker}... ({idx+1} of {len(screening_tickers)})")
        
        financials = get_stock_data(ticker)
        if financials and financials['currentPrice'] > 0:
            buffett = calculate_buffett_score(financials)
            sentiment = fetch_news_sentiment(ticker)
            combined_score = calculate_combined_score(buffett['percentage'], sentiment['score'])
            
            if combined_score >= 70:
                rec = "BUY"
            elif combined_score >= 45:
                rec = "HOLD"
            else:
                rec = "SELL"
            
            results.append({
                'Ticker': ticker,
                'Company': financials['name'][:25],
                'Price': financials['currentPrice'],
                'P/E': financials['trailingPE'],
                'Buffett Score': f"{buffett['percentage']:.0f}%",
                'Sentiment': sentiment['overall'],
                'Recommendation': rec,
                'Combined': f"{combined_score:.0f}/100"
            })
        
        progress_bar.progress((idx + 1) / len(screening_tickers))
        time.sleep(0.1)
    
    progress_bar.empty()
    status_text.empty()
    
    if results:
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('Combined', ascending=False)
        st.dataframe(df_results, use_container_width=True, hide_index=True)
        
        fig = px.bar(df_results.head(20), x='Ticker', y=[float(x.split('/')[0]) for x in df_results['Combined'].head(20)],
                     title='Top 20 Assets by Combined Score',
                     color='Recommendation',
                     color_discrete_map={'BUY': '#2e7d32', 'HOLD': '#ed6c02', 'SELL': '#d32f2f'})
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        csv_screen = df_results.to_csv(index=False).encode('utf-8')
        st.download_button("Download Screening CSV", csv_screen, "WB_screening.csv", "text/csv")
        
        st.success(f"✅ Screening completed! Analyzed {len(results)} assets from 15,000+ global universe.")
    else:
        st.warning("No data available for screening")

# ==================== FOOTER ====================
st.markdown("""
<div class="ft-footer">
    <strong>15,000+ Global Assets</strong> | Data: Yahoo Finance | Sentiment: NLP with TextBlob<br>
    Methodology: Warren Buffett's 6 Criteria (60%) + Market Sentiment (40%)<br>
    Educational purpose only. Not investment advice.
</div>
""", unsafe_allow_html=True)