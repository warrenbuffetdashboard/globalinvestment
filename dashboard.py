import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import difflib
import time

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Warren Buffet Global Screener",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS moderno e apelativo
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        text-align: center;
        color: #5a6e8a;
        margin-bottom: 2rem;
        font-size: 1rem;
    }
    .search-container {
        display: flex;
        justify-content: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #eef2f6 100%);
        border-radius: 20px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .score-badge {
        font-size: 2rem;
        font-weight: 800;
        display: inline-block;
        background: #1e3c72;
        color: white;
        border-radius: 60px;
        padding: 0.2rem 1rem;
        margin: 0.5rem 0;
    }
    .recommend {
        font-size: 2rem;
        font-weight: 800;
        border-radius: 40px;
        padding: 0.5rem 1.5rem;
        display: inline-block;
        text-align: center;
        width: 100%;
    }
    .buy { background: #10b981; color: white; box-shadow: 0 4px 12px rgba(16,185,129,0.3); }
    .hold { background: #f59e0b; color: white; box-shadow: 0 4px 12px rgba(245,158,11,0.3); }
    .sell { background: #ef4444; color: white; box-shadow: 0 4px 12px rgba(239,68,68,0.3); }
    .info-text {
        background: #f1f5f9;
        padding: 1rem;
        border-radius: 16px;
        margin-top: 1rem;
    }
    .footer {
        text-align: center;
        margin-top: 2rem;
        font-size: 0.75rem;
        color: #94a3b8;
    }
    hr {
        margin: 1.5rem 0;
        border-color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Título e descrição
st.markdown('<div class="main-title">🐂 WARREN BUFFET GLOBAL SCREENER</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Análise fundamentalista + sentimento de mercado | 300.000+ ativos | Pressione <kbd>Enter</kbd> para analisar</div>', unsafe_allow_html=True)

# ==================== FUNÇÕES PRINCIPAIS ====================

# Dicionário reduzido para nomes comuns (apenas para conveniência - não carrega lista)
NOME_PARA_TICKER = {
    "microsoft": "MSFT", "apple": "AAPL", "tesla": "TSLA", "amazon": "AMZN",
    "google": "GOOGL", "netflix": "NFLX", "meta": "META", "nvidia": "NVDA",
    "ibm": "IBM", "petrobras": "PETR4.SA", "vale": "VALE3.SA", "itau": "ITUB4.SA",
    "bradesco": "BBDC4.SA", "santander": "SAN.MC", "amd": "AMD", "intel": "INTC"
}

def normalizar_ticker(entrada):
    """Converte nome para ticker (fuzzy simples) - sem carregar listas enormes."""
    texto = entrada.strip().lower()
    if texto in NOME_PARA_TICKER:
        return NOME_PARA_TICKER[texto]
    # Se já parece um ticker (ex: AAPL, MSFT) -> maiúsculas
    if texto.isalpha() and len(texto) <= 5:
        return texto.upper()
    # Tentar correspondência aproximada
    matches = difflib.get_close_matches(texto, NOME_PARA_TICKER.keys(), n=1, cutoff=0.7)
    if matches:
        return NOME_PARA_TICKER[matches[0]]
    # Assume que é o ticker
    return texto.upper()

def calcular_score_buffett(info):
    """Score fundamental 0-10 baseado nos 5 critérios de Buffett."""
    score = 0.0
    detalhes = {}
    
    # ROE (returnOnEquity)
    roe = info.get('returnOnEquity')
    if roe is not None:
        roe_pct = roe * 100 if roe <= 1 else roe
        if roe_pct >= 20:
            score += 2.5
            detalhes['ROE'] = f"{roe_pct:.1f}% ✅ (2.5)"
        elif roe_pct >= 15:
            score += 1.5
            detalhes['ROE'] = f"{roe_pct:.1f}% 📊 (1.5)"
        else:
            detalhes['ROE'] = f"{roe_pct:.1f}% ❌ (0)"
    else:
        detalhes['ROE'] = "N/A (0)"
    
    # Margem líquida (profitMargins)
    margem = info.get('profitMargins')
    if margem is not None:
        margem_pct = margem * 100 if margem <= 1 else margem
        if margem_pct >= 15:
            score += 2.0
            detalhes['Margem Líquida'] = f"{margem_pct:.1f}% ✅ (2.0)"
        elif margem_pct >= 10:
            score += 1.0
            detalhes['Margem Líquida'] = f"{margem_pct:.1f}% 📊 (1.0)"
        else:
            detalhes['Margem Líquida'] = f"{margem_pct:.1f}% ❌ (0)"
    else:
        detalhes['Margem Líquida'] = "N/A (0)"
    
    # Dívida / Patrimônio (debtToEquity)
    divida = info.get('debtToEquity')
    if divida is not None:
        if divida < 50:
            score += 2.0
            detalhes['Dívida/PL'] = f"{divida:.1f}% ✅ (2.0)"
        elif divida < 100:
            score += 1.0
            detalhes['Dívida/PL'] = f"{divida:.1f}% 📊 (1.0)"
        else:
            detalhes['Dívida/PL'] = f"{divida:.1f}% ❌ (0)"
    else:
        detalhes['Dívida/PL'] = "N/A (0)"
    
    # Crescimento da receita (revenueGrowth)
    cresc = info.get('revenueGrowth')
    if cresc is not None:
        cresc_pct = cresc * 100 if cresc <= 1 else cresc
        if cresc_pct > 0:
            score += 1.5
            detalhes['Cresc. Receita'] = f"{cresc_pct:.1f}% ✅ (1.5)"
        else:
            detalhes['Cresc. Receita'] = f"{cresc_pct:.1f}% ❌ (0)"
    else:
        detalhes['Cresc. Receita'] = "N/A (0)"
    
    # Fluxo de caixa livre positivo
    fcf = info.get('freeCashflow')
    if fcf is not None and fcf > 0:
        score += 2.0
        detalhes['Fluxo Caixa Livre'] = "Positivo ✅ (2.0)"
    else:
        detalhes['Fluxo Caixa Livre'] = "Negativo/N/A ❌ (0)"
    
    score = min(score, 10.0)
    return score, detalhes

def calcular_sentimento_mercado(ticker, periodo_dias=10):
    """
    Calcula um score de sentimento (0-10) baseado em dados de mercado:
    - Retorno recente (5 dias)
    - Volume relativo
    - Volatilidade (quanto menor, melhor)
    """
    try:
        fim = datetime.now()
        inicio = fim - timedelta(days=periodo_dias+5)
        hist = yf.download(ticker, start=inicio, end=fim, progress=False)
        if hist.empty or len(hist) < 5:
            return 5.0, "Dados insuficientes"
        
        # Preço atual e há 5 dias
        preco_atual = hist['Close'].iloc[-1]
        preco_5d = hist['Close'].iloc[-6] if len(hist) >= 6 else hist['Close'].iloc[0]
        retorno_5d = (preco_atual - preco_5d) / preco_5d * 100
        
        # Volume relativo (últimos 5 vs média anterior)
        vol_ultimos = hist['Volume'].iloc[-5:].mean()
        vol_anteriores = hist['Volume'].iloc[:-5].mean() if len(hist) > 5 else vol_ultimos
        vol_rel = (vol_ultimos / vol_anteriores) if vol_anteriores > 0 else 1
        
        # Volatilidade (desvio padrão dos retornos diários)
        retornos = hist['Close'].pct_change().dropna()
        volatilidade = retornos.std() * 100  # percentual diário
        
        # Score: retorno (0-5 pontos), volume (0-3), volatilidade (0-2)
        score_ret = min(5, max(0, (retorno_5d + 10) / 4))  # mapeia -10% -> 0, +10% -> 5
        score_vol_rel = min(3, vol_rel / 2)  # volume 2x média dá 1 ponto, 6x dá 3
        score_volatil = max(0, 2 - (volatilidade / 5))  # vol 0% dá 2, vol >10% dá 0
        
        score_total = score_ret + score_vol_rel + score_volatil
        score_total = min(10, max(0, score_total))
        
        descricao = f"Retorno 5d: {retorno_5d:.1f}% | Volume rel: {vol_rel:.1f}x | Volatilidade: {volatilidade:.1f}%"
        return score_total, descricao
    except Exception as e:
        return 5.0, "Erro no cálculo"

def recomendar(score_fund, score_sent):
    """Combina os dois scores e gera recomendação."""
    ponderado = (score_fund * 0.7 + score_sent * 0.3) / 10
    if ponderado >= 0.65:
        return "BUY", ponderado
    elif ponderado >= 0.4:
        return "HOLD", ponderado
    else:
        return "SELL", ponderado

# ==================== CAMPO DE PESQUISA ====================
st.markdown('<div class="search-container">', unsafe_allow_html=True)
entrada = st.text_input("", placeholder="🔎 Digite o ticker ou nome da empresa (ex: AAPL, Microsoft, PETR4.SA)", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

if entrada:
    ticker = normalizar_ticker(entrada)
    
    with st.spinner(f"🔍 A analisar {ticker}..."):
        try:
            # Buscar dados do Yahoo Finance
            acao = yf.Ticker(ticker)
            info = acao.info
            
            if not info or info.get('regularMarketPrice') is None:
                st.error(f"❌ Ativo '{entrada}' não encontrado. Verifique o ticker.")
                st.stop()
            
            # Dados históricos para gráfico (últimos 3 meses)
            fim = datetime.now()
            inicio = fim - timedelta(days=90)
            hist = acao.history(start=inicio, end=fim)
            
            # Score fundamental (Buffett)
            fund_score, detalhes_fund = calcular_score_buffett(info)
            
            # Score de sentimento (baseado em mercado)
            sent_score, sent_desc = calcular_sentimento_mercado(ticker)
            
            # Recomendação final
            rec, conf = recomendar(fund_score, sent_score)
            
            # Nome da empresa
            nome_empresa = info.get('longName', ticker)
            
            # ==================== DASHBOARD PRINCIPAL ====================
            # Linha 1: Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            preco = info.get('regularMarketPrice', hist['Close'].iloc[-1] if not hist.empty else 0)
            var_dia = info.get('regularMarketChangePercent', 0)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("💰 Preço Atual", f"${preco:.2f}" if isinstance(preco, (int,float)) else preco, delta=f"{var_dia:+.2f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            with col2:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("🏆 Score Buffett", f"{fund_score:.1f} / 10")
                st.progress(fund_score/10, text="")
                st.markdown('</div>', unsafe_allow_html=True)
            with col3:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("📊 Sentimento Mercado", f"{sent_score:.1f} / 10")
                st.progress(sent_score/10, text="")
                st.markdown('</div>', unsafe_allow_html=True)
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.markdown(f'<div class="recommend {rec.lower()}">{rec}</div>', unsafe_allow_html=True)
                st.caption(f"Confiança: {conf*100:.0f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Linha 2: Gráfico de evolução
            if not hist.empty:
                st.subheader("📈 Evolução do Preço (últimos 90 dias)")
                st.line_chart(hist['Close'], use_container_width=True)
            
            # Linha 3: Detalhes fundamentalistas e sentimento (duas colunas)
            col_left, col_right = st.columns(2)
            with col_left:
                with st.expander("📘 Critérios Warren Buffett (detalhes)", expanded=True):
                    for crit, valor in detalhes_fund.items():
                        st.write(f"**{crit}:** {valor}")
                    st.caption("▶ ROE ≥20% | Margem ≥15% | Dívida/PL <50% | Crescimento + | Fluxo Caixa +")
            with col_right:
                with st.expander("📰 Sentimento de Mercado (como é calculado)", expanded=True):
                    st.write(sent_desc)
                    st.write("**Componentes:**")
                    st.write("- Retorno últimos 5 dias (quanto maior, melhor)")
                    st.write("- Volume relativo (volume recente vs histórico)")
                    st.write("- Volatilidade (menor volatilidade é mais positiva)")
                    st.caption("Sem necessidade de API externa – tudo derivado do preço e volume.")
            
            # Linha 4: Recomendação final com texto explicativo
            st.markdown("---")
            st.subheader("💡 Síntese para o Investidor")
            if rec == "BUY":
                st.success(f"**BUY** – Fundamentos sólidos (score {fund_score:.1f}) combinados com sentimento de mercado positivo ({sent_score:.1f}). Empresa com vantagem competitiva e bom momento.")
            elif rec == "HOLD":
                st.warning(f"**HOLD** – Pontuação moderada. Aguarde melhores níveis de entrada ou confirmação de melhora nos fundamentos / sentimento.")
            else:
                st.error(f"**SELL** – Fundamentos fracos (score {fund_score:.1f}) e/ou sentimento negativo ({sent_score:.1f}). Risco elevado.")
            
        except Exception as e:
            st.error(f"Erro ao analisar {ticker}: {str(e)}")
            st.info("Dica: Verifique o ticker (ex: AAPL, MSFT, PETR4.SA) ou tente novamente.")
else:
    # Mensagem inicial
    st.info("✨ Digite um ticker (ex: AAPL, TSLA, PETR4.SA) ou nome de empresa (ex: Microsoft) no campo acima e pressione **Enter** para iniciar a análise global.")
    
    # Exemplos e capacidade
    st.markdown("""
    <div class="info-text">
        <b>🌍 Capacidade:</b> Mais de 300.000 ativos (ações, ETFs, fundos) disponíveis no Yahoo Finance.<br>
        <b>📊 Metodologia:</b> 5 critérios de Warren Buffett + sentimento de mercado (retorno, volume, volatilidade).<br>
        <b>⚡ Performance:</b> Sem carregamento antecipado – análise individual sob demanda.
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="footer">© Warren Buffet Global Screener | Dados Yahoo Finance | Recomendação ilustrativa, não é conselho financeiro.</div>', unsafe_allow_html=True)