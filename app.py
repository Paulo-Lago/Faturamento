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
    /* 1. Transparência global para ver a marca d'água */
    .stApp, .stMain, .stHeader, .stAppHeader, .block-container, [data-testid=\"stTabContent\"] {{
        background-color: transparent !important;
        color: #000000 !important;
    }}

    /* 2. Legibilidade do texto e Abas Pretas */
    .stMarkdown, .stText, [data-testid=\"stMetricValue\"], label, h1, h2, h3, [data-testid=\"stWidgetLabel\"] p {{
        color: #000000 !important;
        font-weight: 500 !important;
    }}

    /* Forçar texto das abas para preto */
    button[data-testid=\"stMarker\"] p, [data-testid=\"stTab\"] p {{
        color: #000000 !important;
        font-weight: bold !important;
    }}

    /* 3. Imagem de fundo estilo Marca d'água (Centralizada e Suave) */
    .main-bg-container {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        display: flex !important;
        justify-content: center;
        align-items: center;
        z-index: -1 !important;
        pointer-events: none;
        background-color: #ffffff;
    }}
    
    .bg-image {{
        width: 70vw;
        max-width: 500px;
        opacity: 0.15 !important;
        filter: grayscale(20%) sepia(20%) saturate(150%) hue-rotate(310deg);
    }}

    /* Botões e Inputs */
    button[kind=\"primary\"], button[kind=\"secondary\"], .stButton > button {{
        background-color: #ffc4d8 !important;
        color: #000000 !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        border: 1px solid #ffb0cc !important;
    }}

    .stTextInput>div>div>input, .stNumberInput>div>div>input {{
        background-color: rgba(255, 255, 255, 0.8) !important;
        color: #000000 !important;
        border: 1px solid #ffc4d8 !important;
    }}

    /* Abas */
    div[data-testid=\"stTabs\"] button {{
        background-color: transparent !important;
    }}
    </style>
    <div class='main-bg-container'><img src='{URL_ICONE}' class='bg-image'></div>
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
    st.markdown("<h1 style='text-align: center;'>Acesso ao Sistema</h1>", unsafe_allow_html=True)
    user = st.text_input("Usuário", key="login_user")
    pw = st.text_input("Senha", type="password", key="login_pw")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar"):
            if user and pw:
                conn = sqlite3.connect('servicos_financeiro.db')
                c = conn.cursor()
                c.execute("SELECT password FROM usuarios WHERE username = ?", (user,))
                res = c.fetchone()
                conn.close()
                if res and res[0] == pw:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.rerun()
                else: st.error("Login inválido")
    with col2:
        if st.button("Criar Conta"):
            if user and pw:
                try:
                    conn = sqlite3.connect('servicos_financeiro.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO usuarios VALUES (?, ?)", (user, pw))
                    conn.commit()
                    conn.close()
                    st.success("Conta criada!")
                except: st.error("Usuário já existe")
else:
    st.markdown(f"<h1 style='text-align: center;'>Painel Financeiro</h1>", unsafe_allow_html=True)
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    conn = sqlite3.connect('servicos_financeiro.db')
    df_full = pd.read_sql(f"SELECT * FROM servicos WHERE username='{st.session_state.username}'", conn)
    conn.close()

    hoje = datetime.now().date()
    inicio_mes = hoje.replace(day=1)

    if not df_full.empty:
        df_full['data_dt'] = pd.to_datetime(df_full['data'])
        fat_dia = df_full[df_full['data_dt'].dt.date == hoje]['valor'].sum()
        fat_mes = df_full[df_full['data_dt'].dt.date >= inicio_mes]['valor'].sum()
        
        m1, m2 = st.columns(2)
        m1.metric("Faturamento Hoje", f"R$ {fat_dia:,.2f}")
        m2.metric("Faturamento Mês", f"R$ {fat_mes:,.2f}")

    tab1, tab2, tab3 = st.tabs(["➕ Novo Serviço", "📊 Histórico", "📈 Ranking & Tendências"])

    with tab1:
        st.markdown("### Registrar novo serviço")
        data_serv = st.date_input("Data", value=hoje, format="DD/MM/YYYY")
        cat_serv = st.selectbox("Tipo de Serviço", LISTA_SERVICOS)
        desc_serv = st.text_input("Detalhes")
        valor_serv = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
        if st.button("Salvar"):
            conn = sqlite3.connect('servicos_financeiro.db')
            c = conn.cursor()
            c.execute("INSERT INTO servicos VALUES (?, ?, ?, ?, ?)", (st.session_state.username, data_serv.strftime('%Y-%m-%d'), cat_serv, desc_serv, valor_serv))
            conn.commit()
            conn.close()
            st.success("Registro efetuado com sucesso!")
            st.rerun()

    with tab2:
        if not df_full.empty:
            st.markdown("### Histórico")
            df_view = df_full[['data', 'categoria', 'descricao', 'valor']].copy()
            df_view['data'] = pd.to_datetime(df_view['data']).dt.strftime('%d/%m/%Y')
            st.dataframe(df_view.sort_values('data', ascending=False), use_container_width=True)

    with tab3:
        if not df_full.empty:
            # Ranking por Categoria
            st.markdown("### Faturamento por Categoria (Mês Atual)")
            df_mes = df_full[df_full['data_dt'].dt.date >= inicio_mes]
            if not df_mes.empty:
                df_rank = df_mes.groupby('categoria')['valor'].sum().reset_index().sort_values('valor', ascending=False)
                fig_rank = px.bar(df_rank, x='categoria', y='valor', color_discrete_sequence=['#ffc4d8'])
                fig_rank.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    font=dict(color='black'),
                    xaxis=dict(title_font=dict(color='black'), tickfont=dict(color='black')),
                    yaxis=dict(title_font=dict(color='black'), tickfont=dict(color='black'))
                )
                st.plotly_chart(fig_rank, use_container_width=True)

            # Faturamento Semanal
            st.markdown("### Faturamento por Semana")
            df_full['semana'] = df_full['data_dt'].dt.isocalendar().week
            df_semana = df_full.groupby('semana')['valor'].sum().reset_index()
            fig_semanal = px.line(df_semana, x='semana', y='valor', markers=True, color_discrete_sequence=['#ffc4d8'])
            fig_semanal.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)', 
                font=dict(color='black'),
                xaxis=dict(title='Número da Semana', title_font=dict(color='black'), tickfont=dict(color='black')),
                yaxis=dict(title='Faturamento (R$)', title_font=dict(color='black'), tickfont=dict(color='black'))
            )
            st.plotly_chart(fig_semanal, use_container_width=True)
