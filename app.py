import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
URL_ICONE = "https://preview.redd.it/d7ajx3csqpzg1.jpeg?width=640&crop=smart&auto=webp&s=52f986fe2c31fe8b67d7502f4b1a02f9646cba1d"
LISTA_SERVICOS = [
    "📄 Xérox", 
    "🖨️ Impressão", 
    "📝 Currículo", 
    "🎬 Serviços de Edição", 
    "🛡️ Plastificação", 
    "📸 Impressão de Fotos",
    "⚙️ Outros"
]

def aplicar_estilo_customizado():
    st.markdown(f"""
    <style>
    .stApp, .stMain, .stHeader, .stAppHeader, .block-container {{ background-color: transparent !important; color: black !important; }}
    body {{ background-color: white !important; }}
    .main-bg-container {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; display: flex !important; justify-content: center; align-items: center; z-index: -2 !important; pointer-events: none; overflow: hidden; }}
    .egg-icon-bg-persistent {{ width: 85vw; max-width: 650px; opacity: 0.10 !important; filter: grayscale(100%); }}
    h1 {{ font-size: calc(1.6rem + 1vw) !important; text-align: center; margin-bottom: 0.5rem; }}
    .sub-texto {{ text-align: center; margin-bottom: 2rem; font-size: 1.1rem; opacity: 0.7; }}
    div.stButton > button {{ background-color: #2E86C1 !important; color: white !important; border-radius: 12px !important; font-weight: bold !important; width: 100% !important; }}
    </style>
    <div class='main-bg-container'><img src='{URL_ICONE}' class='egg-icon-bg-persistent'></div>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="Gestão de Serviços Pro", layout="centered")
aplicar_estilo_customizado()

def init_db():
    conn = sqlite3.connect('servicos_financeiro.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (username TEXT UNIQUE, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS servicos (username TEXT, data DATE, categoria TEXT, descricao TEXT, valor REAL)')
    conn.commit()
    conn.close()

init_db()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""

if not st.session_state.logged_in:
    st.markdown("<h1>Gestor de Serviços</h1>", unsafe_allow_html=True)
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        conn = sqlite3.connect('servicos_financeiro.db')
        c = conn.cursor()
        c.execute("SELECT password FROM usuarios WHERE username = ?", (user,))
        res = c.fetchone()
        conn.close()
        if res and res[0] == pw:
            st.session_state.logged_in = True
            st.session_state.username = user
            st.rerun()
        else: st.error("Erro de login")
else:
    st.markdown(f"<h1>Painel de Faturamento</h1>", unsafe_allow_html=True)
    if st.sidebar.button("Sair"): 
        st.session_state.logged_in = False
        st.rerun()

    conn = sqlite3.connect('servicos_financeiro.db')
    df_full = pd.read_sql(f"SELECT * FROM servicos WHERE username='{st.session_state.username}'", conn)
    conn.close()

    hoje = datetime.now().date()
    inicio_mes = hoje.replace(day=1)

    if not df_full.empty:
        df_full['data'] = pd.to_datetime(df_full['data'])
        fat_dia = df_full[df_full['data'].dt.date == hoje]['valor'].sum()
        fat_mes = df_full[df_full['data'].dt.date >= inicio_mes]['valor'].sum()
        m1, m2 = st.columns(2)
        m1.metric("Faturamento Hoje", f"R$ {fat_dia:,.2f}")
        m2.metric("Faturamento Mês", f"R$ {fat_mes:,.2f}")

    tab1, tab2, tab3 = st.tabs(["➕ Novo Serviço", "📊 Histórico", "📈 Ranking de Serviços"])

    with tab1:
        st.markdown("### Registrar novo serviço")
        data_serv = st.date_input("Data", value=hoje)
        cat_serv = st.selectbox("Tipo de Serviço", LISTA_SERVICOS)
        desc_serv = st.text_input("Detalhes Adicionais (opcional)")
        valor_serv = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
        if st.button("Salvar"):
            conn = sqlite3.connect('servicos_financeiro.db')
            c = conn.cursor()
            c.execute("INSERT INTO servicos VALUES (?, ?, ?, ?, ?)", (st.session_state.username, data_serv, cat_serv, desc_serv, valor_serv))
            conn.commit()
            conn.close()
            st.success("Registrado!")
            st.rerun()

    with tab2:
        if not df_full.empty:
            st.dataframe(df_full[['data', 'categoria', 'descricao', 'valor']].sort_values('data', ascending=False), use_container_width=True)

    with tab3:
        if not df_full.empty:
            st.markdown("### Qual serviço fatura mais no mês?")
            df_mes = df_full[df_full['data'].dt.date >= inicio_mes]
            if not df_mes.empty:
                df_rank = df_mes.groupby('categoria')['valor'].sum().reset_index().sort_values('valor', ascending=False)
                fig_rank = px.bar(df_rank, x='categoria', y='valor', 
                                 title=f"Faturamento por Categoria ({hoje.strftime('%B/%Y')})",
                                 labels={'categoria': 'Serviço', 'valor': 'Total (R$)'},
                                 color='valor', color_continuous_scale='Viridis')
                st.plotly_chart(fig_rank, use_container_width=True)
            else:
                st.info("Ainda não há dados para o mês atual.")
