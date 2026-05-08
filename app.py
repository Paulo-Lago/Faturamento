import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
URL_ICONE = "https://preview.redd.it/53zg1z70jxzg1.jpeg?width=640&crop=smart&auto=webp&s=57ad5ec9bee948b825fe8e208f951f6ffd2739ee"
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
    /* 1. Reset e Transparência Global Responsiva */
    .stApp, .stMain, .stHeader, .stAppHeader, .block-container, [data-testid=\"stTabContent\"] {{
        background-color: transparent !important;
        color: #000000 !important;
    }}

    /* Ajuste de padding para telas pequenas */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }}

    /* 2. Legibilidade e Abas */
    .stMarkdown, .stText, [data-testid=\"stMetricValue\"], label, h1, h2, h3, [data-testid=\"stWidgetLabel\"] p {{
        color: #000000 !important;
        font-weight: 500 !important;
    }}

    /* Forçar texto das abas para preto e responsividade */
    button[data-testid=\"stMarker\"] p, [data-testid=\"stTab\"] p {{
        color: #000000 !important;
        font-weight: bold !important;
        font-size: clamp(0.8rem, 2.5vw, 1rem) !important;
    }}

    /* 3. Marca d'água Responsiva */
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
        width: 80vw;
        max-width: 500px;
        opacity: 0.12 !important;
        filter: grayscale(20%) sepia(20%) saturate(150%) hue-rotate(310deg);
    }}

    /* 4. Inputs e Botões Full-Width para Mobile */
    button[kind=\"primary\"], button[kind=\"secondary\"], .stButton > button {{
        background-color: #ffc4d8 !important;
        color: #000000 !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        border: 1px solid #ffb0cc !important;
        width: 100% !important;
        padding: 0.5rem !important;
    }}

    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox select {{
        background-color: rgba(255, 255, 255, 0.8) !important;
        color: #000000 !important;
        border: 1px solid #ffc4d8 !important;
        width: 100% !important;
    }}

    /* Ajuste de métricas para não quebrar em telas minúsculas */
    [data-testid=\"stMetric\"] {{ 
        background: rgba(255, 255, 255, 0.4);
        padding: 10px;
        border-radius: 10px;
    }}

    @media (max-width: 640px) {{
        h1 {{ font-size: 1.5rem !important; }}
        .bg-image {{ width: 90vw; }}
    }}
    </style>
    <div class='main-bg-container'><img src='{URL_ICONE}' class='bg-image'></div>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="Gestão de Serviços Pro", layout="wide") # Wide para melhor aproveitamento horizontal
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
    # Centraliza o formulário de login
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        user = st.text_input("Usuário", key="login_user")
        pw = st.text_input("Senha", type="password", key="login_pw")
        c1, c2 = st.columns(2)
        with c1:
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
        with c2:
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

    # Métricas responsivas
    if not df_full.empty:
        df_full['data_dt'] = pd.to_datetime(df_full['data'])
        fat_dia = df_full[df_full['data_dt'].dt.date == hoje]['valor'].sum()
        fat_mes = df_full[df_full['data_dt'].dt.date >= inicio_mes]['valor'].sum()

        m1, m2 = st.columns(2)
        m1.metric("Faturamento Hoje", f"R$ {fat_dia:,.2f}")
        m2.metric("Faturamento Mês", f"R$ {fat_mes:,.2f}")

    tab1, tab2, tab3 = st.tabs(["➕ Novo", "📊 Histórico", "📈 Ranking"])

    with tab1:
        st.markdown("### Novo serviço")
        data_serv = st.date_input("Data", value=hoje, format="DD/MM/YYYY")
        cat_serv = st.selectbox("Tipo", LISTA_SERVICOS)
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
            df_view['valor_fmt'] = df_view['valor'].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(df_view[['data', 'categoria', 'descricao', 'valor_fmt']].sort_values('data', ascending=False), use_container_width=True)

    with tab3:
        if not df_full.empty:
            st.markdown("### Faturamento por Categoria")
            df_mes = df_full[df_full['data_dt'].dt.date >= inicio_mes]
            if not df_mes.empty:
                df_rank = df_mes.groupby('categoria')['valor'].sum().reset_index().sort_values('valor', ascending=False)
                fig_rank = px.bar(df_rank, x='categoria', y='valor', color_discrete_sequence=['#ffc4d8'])
                fig_rank.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='black'),
                    margin=dict(l=20, r=20, t=30, b=20),
                    xaxis=dict(title_font=dict(color='black'), tickfont=dict(color='black')),
                    yaxis=dict(title='Total (R$)', title_font=dict(color='black'), tickfont=dict(color='black'), tickformat=".2f", tickprefix="R$ ")
                )
                st.plotly_chart(fig_rank, use_container_width=True)

            st.markdown("### Faturamento Semanal")
            df_full['segunda'] = df_full['data_dt'] - df_full['data_dt'].dt.weekday.map(lambda x: timedelta(days=x))
            df_full['domingo'] = df_full['segunda'] + timedelta(days=6)
            df_full['periodo'] = df_full['segunda'].dt.strftime('%d/%m') + "-" + df_full['domingo'].dt.strftime('%d/%m')
            df_semana = df_full.groupby(['segunda', 'periodo'])['valor'].sum().reset_index().sort_values('segunda')
            
            fig_semanal = px.bar(df_semana, x='periodo', y='valor', color_discrete_sequence=['#ffc4d8'])
            fig_semanal.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='black'),
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis=dict(title='Faturamento (R$)', tickformat=".2f", tickprefix="R$ ")
            )
            st.plotly_chart(fig_semanal, use_container_width=True)
