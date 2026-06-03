import streamlit as st
import feedparser
import urllib.parse
import requests

# 1. Configuração de Arquitetura da UI (Streamlit)
st.set_page_config(
    page_title="Markets Data | Financial Times Style",
    page_icon="📰",
    layout="wide"
)

# 2. INJEÇÃO DE DESIGN EDITORIAL (Estilo Financial Times - #fff1e5 background)
st.markdown("""
    <style>
        /* Fundo principal e cor do texto editorial */
        .stApp {
            background-color: #fff1e5 !important;
            color: #333333 !important;
            font-family: 'MetricWeb', 'Georgia', serif !important;
        }
        
        /* Cabeçalhos e Títulos estilo Jornal */
        h1, h2, h3, h4 {
            color: #0d2d3a !important;
            font-family: 'FinancierDisplayWeb', 'Georgia', serif !important;
            font-weight: 700 !important;
            border-bottom: 2px solid #333333;
            padding-bottom: 5px;
        }
        
        /* Customização de blocos de informação */
        .ft-card {
            background-color: #f6ede3;
            border-top: 4px solid #0d2d3a;
            padding: 20px;
            margin-bottom: 20px;
            color: #333333;
        }
        .ft-opportunity {
            background-color: #f1f6f1;
            border-left: 5px solid #117d10;
            padding: 15px;
            margin-bottom: 10px;
        }
        .ft-risk {
            background-color: #fdf2f2;
            border-left: 5px solid #c11717;
            padding: 15px;
            margin-bottom: 10px;
        }
        
        /* Ajuste fino nos inputs para não quebrarem o contraste */
        label {
            color: #0d2d3a !important;
            font-weight: bold !important;
        }
    </style>
""", unsafe_allow_html=True)


# 3. MOTOR DE SUGUETÃO POR APROXIMAÇÃO GLOBAL (Acesso a 15.000+ Ativos via API Yahoo)
def buscar_ativos_por_aproximacao(query_usuario):
    """Consulta a API de pesquisa global para sugerir ativos e nomes por aproximação."""
    if not query_usuario or len(query_usuario) < 2:
        return [("BTC-USD", "Bitcoin Crypto"), ("AAPL", "Apple Inc."), ("NFLX", "Netflix Inc.")]
        
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query_usuario)}&quotesCount=10"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resposta = requests.get(url, headers=headers, timeout=5)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            sugestoes = []
            for resultado in dados.get("quotes", []):
                ticker = resultado.get("symbol")
                nome = resultado.get("shortname") or resultado.get("longname") or "Ativo Global"
                if ticker:
                    sugestoes.append((ticker, nome))
            if sugestoes:
                return congestoes
    except:
        pass
    return [("BTC-USD", "Bitcoin Crypto"), ("AAPL", "Apple Inc.")]


# 4. RASTREADOR WEB AVANÇADO DE SENTIMENTO, OPORTUNIDADES E RISCOS
def analisar_sinais_mercado_comunidades(nome_empresa):
    """Varre fóruns e canais de imprensa globais à procura de catalisadores do último mês."""
    termos_positivos = ['buy', 'growth', 'surge', 'bullish', 'gain', 'profit', 'beat', 'revenue', 'ai', 'innovation', 'expand', 'higher', 'partnership', 'dividend', 'deal', 'undervalued', 'breakout']
    termos_negativos = ['lawsuit', 'sued', 'court', 'legal', 'class action', 'loss', 'miss', 'drop', 'fell', 'crash', 'down', 'bearish', 'risk', 'warns', 'investigation', 'probe', 'short', 'dilution', 'dump']
    
    try:
        query_avancada = f'"{nome_empresa}" (news OR forum OR discussion OR thread OR stocktwits OR reddit)'
        nome_codificado = urllib.parse.quote_plus(query_avancada)
        url_rastreio = f"https://news.google.com/rss/search?q={nome_codificado}+when:30d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url_rastreio)
        
        if not feed.entries:
            return "Neutro", ["Volume de discussões de rede baixo para mapear riscos adicionais."], ["Sem catalisadores de retalho fora do radar de momento."], 0
            
        score_sentimento = 0
        total_sinais = 0
        problemas_detetados = set()
        oportunidades_detetadas = set()
        
        for entry in feed.entries[:40]:
            titulo = entry.get('title', '').lower()
            if not titulo:
                continue
            total_sinais += 1
            
            for n_neg in termos_negativos:
                if n_neg in titulo:
                    score_sentimento -= 1
                    if n_neg in ['lawsuit', 'sued', 'court', 'legal', 'class action']:
                        problemas_detetados.add("Litígios Judiciais: Comunidade a debater riscos de processos ou escrutínio legal em andamento.")
                    elif n_neg in ['investigation', 'probe', 'warns']:
                        problemas_detetados.add("Risco de Compliance: Menções em threads a investigações operacionais ou alertas macro.")
                    elif n_neg in ['dilution', 'short', 'dump']:
                        problemas_detetados.add("Pressão de Oferta: Debates focados em potencial diluição de capital ou aumento de short-selling.")
                    else:
                        problemas_detetados.add("Pressão de Venda Corrente: Ajuste técnico de carteiras captado em fóruns de retalho.")

            for p in termos_positivos:
                if p in titulo:
                    score_sentimento += 1
                    if p in ['ai', 'innovation', 'tech']:
                        oportunidades_detetadas.add("Alavancagem Tecnológica: Expansão em infraestrutura de IA ou adoção de novos produtos de software.")
                    elif p in ['partnership', 'deal', 'expand']:
                        oportunidades_detetadas.add("Parcerias Estratégicas: Forte volume de interações comentando expansão geográfica ou acordos comerciais.")
                    elif p in ['beat', 'revenue', 'profit']:
                        oportunidades_detetadas.add("Eficiência Financeira: Discussões focadas no forte ritmo de receitas ou lucros acima do consenso.")
                    else:
                        oportunidades_detetadas.add("Sinal Técnico Otimista: Investidores de comunidades a acumular devido a preços descontados ou breakouts.")

        list_problemas = list(problemas_detetados)[:3] if problemas_detetados else ["Sem bandeiras vermelhas ou alertas críticos de fóruns identificados nas últimas semanas."]
        list_oportunidades = list(oportunidades_detetadas)[:3] if oportunidades_detetadas else ["Sem gatilhos assimétricos captados nos canais monitorizados."]

        if score_sentimento > 2:
            return "Bullish", list_problemas, list_oportunidades, total_sinais
        elif score_sentimento < -2:
            return "Bearish", list_problemas, list_oportunidades, total_sinais
        else:
            return "Neutro", list_problemas, list_oportunidades, total_sinais
            
    except Exception as e:
        return "Erro", [f"Falha técnica de comunicação: {e}"], ["Indisponível"], 0


# --- ESTRUTURAÇÃO DA INTERFÁCIA EDITORIAL (ESTILO FINANCIAL TIMES) ---
st.markdown("<h1 style='text-align: center; border: none;'>FINANCIAL TIMES STYLE MARKETS DASHBOARD</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-style: italic; color: #555555;'>Global Intelligence System — News, Fora & Sentiment Tracker</p>", unsafe_allow_html=True)
st.markdown("---")

# Seção de Entrada Inteligente (Auto-Suggest Real)
st.markdown("### 🔍 Global Market Search Engine")
texto_busca = st.text_input("Escreva o Nome da Empresa ou o Ticker (Ex: 'Tesla', 'Nvidia', 'Marathon', 'Petrobras'):", value="Marathon Digital")

# Dispara a busca dinâmica em tempo real com base no que o usuário digita
lista_sugestoes = buscar_ativos_por_aproximacao(texto_busca)
opcoes_formatadas = [f"{t} - {n}" for t, n in lista_sugestoes]

escolha_final = st.selectbox(
    "Selecione o ativo correspondente encontrado por aproximação:",
    options=opcoes_formatadas,
    index=0
)

# Isola os metadados selecionados
ticker_ativo = escolha_final.split(" - ")[0]
nome_ativo = escolha_final.split(" - ")[1]

st.markdown("---")

# Exibição dos resultados com design jornalístico limpo
st.markdown(f"<h2>MARKET REPORT: {nome_ativo.upper()} ({ticker_ativo})</h2>", unsafe_allow_html=True)

with st.spinner("A efetuar rastreio editorial de rede e inteligência de fóruns..."):
    tipo_sentimento, problemas, oportunidades, volume_dados = analisar_sinais_mercado_comunidades(nome_ativo)

# Linha Editorial Superior: Sentimento Macro
c_sent, c_vol = st.columns([3, 1])
with c_sent:
    if tipo_sentimento == "Bullish":
        st.markdown("<p style='font-size: 20px; color: #117d10;'><strong>Current Network Sentiment:</strong> 🟢 BULLISH — Positive catalysts dominate the web ticker.</p>", unsafe_allow_html=True)
    elif tipo_sentimento == "Bearish":
        st.markdown("<p style='font-size: 20px; color: #c11717;'><strong>Current Network Sentiment:</strong> 🔴 BEARISH — Caution advised. Communities highlighting high operational stress.</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='font-size: 20px; color: #b77a00;'><strong>Current Network Sentiment:</strong> 🟡 NEUTRAL / MIXED — Balanced flow of news and lateral discussion.</p>", unsafe_allow_html=True)
with c_vol:
    st.markdown(f"<p style='text-align: right; color: #555555;'>Data Streams Scanned: <strong>{volume_dados}</strong></p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Duas Colunas Editoriais Clássicas: Oportunidades vs Problemas
col_esquerda, col_direita = st.columns(2)

with col_esquerda:
    st.markdown("<h3 style='border-bottom: 2px solid #117d10;'>🔥 Key Upside Opportunities</h3>", unsafe_allow_html=True)
    for op in oportunidades:
        st.markdown(f"<div class='ft-opportunity'><strong>🚀 Catalyst:</strong> {op}</div>", unsafe_allow_html=True)

with col_direita:
    st.markdown("<h3 style='border-bottom: 2px solid #c11717;'>⚠️ Major Risks & Headwinds</h3>", unsafe_allow_html=True)
    for prob in problemas:
        st.markdown(f"<div class='ft-risk'><strong>📉 Threat:</strong> {prob}</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<p style='text-align: center; font-size: 11px; color: #777777;'>Financial Times Look & Feel Web App Prototype © 2026. Data sourced autonomously via Open Index RSS feeds.</p>", unsafe_allow_html=True)