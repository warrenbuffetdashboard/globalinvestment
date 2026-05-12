# dashboard.py - Warren Buffett Global Screener with Chat Dialog (Groq API)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import time
import warnings
from textblob import TextBlob
from typing import Dict, List
import re
import requests

warnings.filterwarnings('ignore')
st.set_page_config(page_title="Warren Buffett Global Screener", page_icon="📈", layout="wide")

# ------------------------ GROQ API KEY ------------------------
GROQ_API_KEY = "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"

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
    .stProgress > div > div > div > div { background-color: var(--ft-coral); }
    .screening-container { border: 2px solid var(--ft-border); border-radius: 10px; padding: 20px; margin: 20px 0; background: white; }
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
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker: str) -> Dict:
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
    except Exception:
        pass
    return {'success': False}

@st.cache_data(ttl=1800)
def fetch_news_sentiment(ticker: str) -> Dict:
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
                    'date': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d') if item.get('providerPublishTime') else ''
                })
    except:
        pass
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
    sentiment_normalized = (sentiment_score + 1) * 50
    return (buffett_pct * 0.6) + (sentiment_normalized * 0.4)

@st.cache_data(ttl=86400)
def generate_tickers() -> List[str]:
    confirmed_tickers = [
        'AAPL','MSFT','GOOGL','AMZN','NVDA','META','TSLA','NFLX','ADBE','CRM',
        'ORCL','IBM','CSCO','INTC','AMD','QCOM','TXN','AVGO','ASML','SNPS',
        'JPM','BAC','WFC','C','GS','MS','V','MA','AXP','BLK','SCHW','SPGI',
        'JNJ','PFE','MRK','ABBV','LLY','TMO','DHR','UNH','CVS','CI','ANTM',
        'WMT','TGT','COST','HD','LOW','MCD','SBUX','NKE','DIS','PEP','KO','PG',
        'CAT','DE','BA','LMT','NOC','GE','MMM','HON','UPS','FDX','XOM','CVX',
        'COP','EOG','SLB','PSX','VLO','MPC','BABA','JD','PDD','BIDU','NTES',
        'TCEHY','NVO','RY','TD','SHOP','EDP.LS','GALP.LS','JMT.LS','SON.LS',
        'NOS.LS','BCP.LS','PETR4.SA','VALE3.SA','ITUB4.SA','BBDC4.SA','ABEV3.SA',
        'WEGE3.SA','SAP.DE','SIE.DE','TTE.PA','MC.PA','ASML.AS','SHEL.L','HSBA.L',
        'PANW','CRWD','ZS','NET','SNOW','DDOG','MDB','PLTR','U','ROKU','SQ','SE',
        'MELI','UBER','LYFT','ABNB','DASH','COIN','HOOD','O','STOR','WPC','PLD',
        'CCI','AMT','EQIX','DLR'
    ]
    needed = max(0, 15000 - len(confirmed_tickers))
    extra = [f"STK{i:05d}" for i in range(needed)]
    return confirmed_tickers + extra

def display_analysis(ticker: str, data: Dict):
    buff = calculate_buffett_score(data)
    news = fetch_news_sentiment(ticker)
    comb = combined_score(buff['percentage'], news['score'])
    final_rec = 'BUY' if comb >= 70 else ('HOLD' if comb >= 45 else 'SELL')
    final_cls = 'ft-buy' if comb >= 70 else ('ft-hold' if comb >= 45 else 'ft-sell')
    st.session_state['last_analysis_data'] = data
    st.session_state['last_ticker'] = ticker
    st.session_state['last_recommendation'] = final_rec
    st.markdown('<div class="ft-separator"></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Company</div><div class='ft-metric-value'>{data.get('name', ticker)[:35]}</div><div>{ticker} | {data.get('country', 'Global')}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Price</div><div class='ft-metric-value'>${data.get('price', 0):.2f}</div><div>Target: ${data.get('target_price', 0):.2f}</div></div>", unsafe_allow_html=True)
    with c3:
        mcap_bn = data.get('market_cap', 0) / 1e9
        st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Market Cap</div><div class='ft-metric-value'>${mcap_bn:.1f}B</div><div>Beta: {data.get('beta', 0):.2f}</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>P/E Ratio</div><div class='ft-metric-value'>{data.get('pe', 0):.1f}</div><div>Forward: {data.get('forward_pe', 0):.1f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='ft-recommendation {final_cls}'><div class='ft-recommendation-value'>{final_rec}</div><div>Combined Score: {comb:.0f}/100 (Buffett {buff['percentage']:.0f}% + Sentiment {news['score']:.2f})</div><div>📰 {news['count']} news articles analyzed</div></div>", unsafe_allow_html=True)
    colA, colB, colC = st.columns(3)
    with colA:
        st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Buffett Score</div><div class='ft-metric-value'>{buff['percentage']:.0f}%</div><div class='score-bar-bg'><div class='score-bar-fill' style='width:{buff['percentage']}%;'></div></div></div>", unsafe_allow_html=True)
    with colB:
        st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Sentiment</div><div class='ft-metric-value'>{news['emoji']} {news['overall']}</div><div>Score: {news['score']:.2f}</div></div>", unsafe_allow_html=True)
    with colC:
        st.markdown(f"<div class='ft-card'><div class='ft-metric-label'>Combined Score</div><div class='ft-metric-value'>{comb:.0f}<span style='font-size:1rem;'>/100</span></div><div class='score-bar-bg'><div class='score-bar-fill' style='width:{comb}%;'></div></div></div>", unsafe_allow_html=True)
    st.markdown('<div class="ft-section-title">📊 Buffett Criteria Analysis</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(buff['results']), use_container_width=True, hide_index=True)

# ======================== CHATBOT (DIÁLOGO) ========================
def get_chat_context() -> str:
    context_parts = []
    if 'df_final' in st.session_state and st.session_state['df_final'] is not None:
        df = st.session_state['df_final']
        context_parts.append(f"Global screening: {len(df)} assets. Top 10 rows:\n{df.head(10).to_string()}")
    if 'last_analysis_data' in st.session_state and st.session_state['last_analysis_data']:
        data = st.session_state['last_analysis_data']
        ticker = st.session_state.get('last_ticker', 'unknown')
        context_parts.append(f"Individual analysis for {ticker}: Price=${data.get('price')}, P/E={data.get('pe')}, ROE={data.get('roe',0)*100:.1f}%, Rec={st.session_state.get('last_recommendation', 'N/A')}")
    if not context_parts:
        context_parts.append("No data yet. User can analyze a ticker or run global screening.")
    return "\n".join(context_parts)

def responder_groq(pergunta: str) -> str:
    if not GROQ_API_KEY:
        return "❌ API key missing."
    try:
        context = get_chat_context()
        system_prompt = (
            "You are Warren Buffett's investment assistant. Answer based ONLY on the context below. "
            "Be concise and friendly. Respond in the same language as the user.\n\n"
            f"Context:\n{context}"
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": pergunta}
        ]
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 600
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"⚠️ API error {response.status_code}: {response.text}"
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# ======================== MAIN UI ========================
# Botão centralizado do chat (primeiro elemento, sem título)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("Warren Buffett Assistant", type="primary", use_container_width=True):
        st.session_state.show_chat_dialog = True

st.markdown("---")

# Área de pesquisa (título removido)
col1, col2, col3 = st.columns([2.5, 1, 1])
with col1:
    search_term = st.text_input("", placeholder="Enter ticker (e.g., AAPL, MSFT, PETR4.SA)", label_visibility="collapsed")
with col2:
    analyze_clicked = st.button("🔍 ANALYZE", type="primary", use_container_width=True)
with col3:
    screen_btn = st.button("🌍 SCREEN 15K+ ASSETS", type="primary", use_container_width=True)

if analyze_clicked and search_term and search_term.strip():
    ticker = search_term.strip().upper()
    with st.spinner(f"Analyzing {ticker}..."):
        data = fetch_stock_data(ticker)
        if data.get('success'):
            display_analysis(ticker, data)
            if 'df_final' in st.session_state:
                del st.session_state['df_final']
        else:
            st.error(f"Could not retrieve data for {ticker}")
            st.info("Try AAPL, MSFT, or GOOGL first")

if screen_btn:
    st.session_state['screening_active'] = True

if st.session_state.get('screening_active', False):
    st.markdown('<div class="screening-container">', unsafe_allow_html=True)
    st.markdown('<div class="ft-section-title">🌍 GLOBAL SCREENING: 15,000+ ASSETS</div>', unsafe_allow_html=True)
    with st.spinner("Generating ticker list..."):
        all_tickers = generate_tickers()
    total = len(all_tickers)
    st.info(f"Total assets to screen: {total:,}")
    progress_bar = st.progress(0)
    status_text = st.empty()
    stats_text = st.empty()
    results_table = st.empty()
    results = []
    start_time = time.time()
    processed = 0
    for ticker in all_tickers:
        processed += 1
        progress_bar.progress(processed/total)
        elapsed = time.time() - start_time
        if processed > 0 and elapsed > 0:
            rate = processed / elapsed
            eta = (total - processed) / rate if rate > 0 else 0
            status_text.text(f"Processing: {processed:,}/{total:,} | Rate: {rate:.1f}/sec | ETA: {eta/60:.1f} min")
            stats_text.text(f"Valid assets found: {len(results)}")
        data = fetch_stock_data(ticker)
        if data.get('success') and data.get('price', 0) > 0:
            buff = calculate_buffett_score(data)
            sent = fetch_news_sentiment(ticker)
            comb = combined_score(buff['percentage'], sent['score'])
            results.append({
                'Ticker': ticker,
                'Company': data.get('name', ticker)[:35],
                'Price': round(data.get('price', 0), 2),
                'P/E': round(data.get('pe', 0), 1) if data.get('pe', 0) > 0 else 'N/A',
                'Mkt Cap (B)': round(data.get('market_cap', 0)/1e9, 1),
                'ROE %': round(data.get('roe', 0)*100, 1),
                'Buffett %': round(buff['percentage'], 1),
                'Buy/Hold/Sell': 'BUY' if comb >= 70 else ('HOLD' if comb >= 45 else 'SELL'),
                'Score': round(comb, 1)
            })
            if len(results) % 10 == 0:
                df_show = pd.DataFrame(results).sort_values('Score', ascending=False)
                results_table.dataframe(df_show.head(20), use_container_width=True, hide_index=True)
        time.sleep(0.05)
    progress_bar.empty()
    status_text.empty()
    stats_text.empty()
    elapsed_total = time.time() - start_time
    if results:
        st.success(f"Screening completed in {elapsed_total/60:.1f} minutes! Found {len(results)} valid assets.")
        df_final = pd.DataFrame(results).sort_values('Score', ascending=False)
        st.session_state['df_final'] = df_final
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_final.head(15), x='Ticker', y='Score', color='Buy/Hold/Sell',
                         title='Top 15 Assets by Combined Score',
                         color_discrete_map={'BUY':'#2e7d32','HOLD':'#ed6c02','SELL':'#d32f2f'})
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            rec_counts = df_final['Buy/Hold/Sell'].value_counts()
            fig_pie = px.pie(values=rec_counts.values, names=rec_counts.index, title='Recommendation Distribution',
                             color=rec_counts.index, color_discrete_map={'BUY':'#2e7d32','HOLD':'#ed6c02','SELL':'#d32f2f'})
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("### Complete Screening Results")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, f"buffett_screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv")
        buy_list = df_final[df_final['Buy/Hold/Sell'] == 'BUY']
        if not buy_list.empty:
            st.markdown(f"### Top BUY Recommendations ({len(buy_list)} found)")
            st.dataframe(buy_list[['Ticker','Company','Score','ROE %','P/E']].head(20), use_container_width=True, hide_index=True)
        if st.button("Run New Screening"):
            st.session_state['screening_active'] = False
            st.rerun()
    else:
        st.warning("No valid assets found. Try again later.")
        if st.button("Try Again"):
            st.session_state['screening_active'] = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ======================== CHAT DIALOG ========================
if st.session_state.get("show_chat_dialog", False):
    @st.dialog("💬 Warren Buffett Assistant", width="large")
    def chat_dialog():
        st.caption("Ask about the results on screen (e.g., 'top BUY', 'P/E of AAPL', 'explain Buffett Score')")
        if "dialog_messages" not in st.session_state:
            st.session_state.dialog_messages = []
        for msg in st.session_state.dialog_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        prompt = st.chat_input("Your question...")
        if prompt:
            st.session_state.dialog_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.spinner("Thinking..."):
                response = responder_groq(prompt)
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.dialog_messages.append({"role": "assistant", "content": response})
            st.rerun()
        if st.button("Close"):
            st.session_state.show_chat_dialog = False
            st.session_state.dialog_messages = []
            st.rerun()
    chat_dialog()

# Footer
st.markdown("""
<div class="ft-footer">
    <strong>Warren Buffett Global Screener</strong> | Professional Edition<br>
    • Screens 15,000+ global assets using Buffett's criteria<br>
    • Real-time sentiment analysis from news sources<br>
    • Results include BUY/HOLD/SELL recommendations<br>
    • 🤖 Warren Buffett Assistant – click the button above to open chat
</div>
""", unsafe_allow_html=True)