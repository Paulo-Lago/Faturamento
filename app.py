import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy import text

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
    /* Forçar fundo branco e texto preto em toda a aplicação */
    .stApp, .stMain, .stHeader, .stAppHeader, .block-container, [data-testid=\"stTabContent\"] {{
        background-color: #ffffff !important;
        color: #000000 !important;
    }}

    /* Forçar cor preta em TODOS os elementos de texto possíveis */
    html, body, [class*=\"st-b\"] {{
        color: #000000 !important;
    }}

    .stMarkdown, .stText, [data-testid=\"stMetricValue\"], label, h1, h2, h3, p, span, 
    [data-testid=\"stWidgetLabel\"] p, table, th, td, [data-testid=\"stTable\"] td, 
    .stDataFrame, [data-testid=\"stMetricLabel\"] p {{
        color: #000000 !important;
        font-weight: 600 !important;
    }}

    /* Estilo dos Inputs (Campos de texto e números) */
    input, select, textarea, [data-baseweb=\"select\"] div {{
        color: #000000 !important;
        background-color: #f0f2f6 !important;
    }}

    /* Botões */
    button[data-testid=\"baseButton-secondary\"], .stButton > button {{
        background-color: #ffc4d8 !important;
        color: #000000 !important;
        border-radius: 12px !important;
        width: 100% !important;
        border: 1px solid #ffb0cc !important;
        font-weight: bold !important;
    }}

    /* Imagem de Fundo */
    .main-bg-container {{ position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; background-color: #ffffff; display: flex; justify-content: center; align-items: center; }}
    .bg-image {{ width: 80vw; max-width: 500px; opacity: 0.15; }}
    </style>
    <div class='main-bg-container'><img src='{URL_ICONE}' class='bg-image'></div>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="Gestão de Serviços Pro", layout="wide")
aplicar_estilo_customizado()

# --- GERENCIAMENTO DE BANCO DE DADOS ---
def get_connection():
    try: return st.connection("postgresql", type="sql")
    except: return None

def run_query(query, params=None, is_select=True):
    conn_cloud = get_connection()
    if conn_cloud:
        with conn_cloud.session as s:
            if is_select: return pd.read_sql(text(query), s.bind, params=params)
            else:
                s.execute(text(query), params)
                s.commit()
                return None
    else:
        conn = sqlite3.connect('servicos_financeiro.db')
        if is_select:
            sql_mod = query
            p_list = []
            if params:
                for k, v in params.items():
                    sql_mod = sql_mod.replace(f":{k}", "?")
                    p_list.append(v)
            df = pd.read_sql(sql_mod, conn, params=p_list)
            conn.close()
            return df
        else:
            c = conn.cursor()
            sql_mod = query
            p_list = []
            if params:
                for k, v in params.items():
                    sql_mod = sql_mod.replace(f":{k}", "?")
                    p_list.append(v)
            c.execute(sql_mod, p_list)
            conn.commit()
            conn.close()
            return None

def init_db():
    run_query("CREATE TABLE IF NOT EXISTS usuarios (username TEXT UNIQUE, password TEXT)", is_select=False)
    run_query("CREATE TABLE IF NOT EXISTS servicos (username TEXT, data DATE, categoria TEXT, descricao TEXT, valor REAL)", is_select=False)
    run_query("CREATE TABLE IF NOT EXISTS creditos (username TEXT, cliente TEXT, valor REAL, data DATE)", is_select=False)

init_db()

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>Acesso ao Sistema</h1>", unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        user = st.text_input("Usuário", key="login_user")
        pw = st.text_input("Senha", type="password", key="login_pw")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Entrar"):
                if user:
                    res = run_query("SELECT password FROM usuarios WHERE username = :u", {"u": user})
                    if not res.empty and str(res.iloc[0]['password']) == str(pw):
                        st.session_state.logged_in = True
                        st.session_state.username = user
                        st.rerun()
                    else: st.error("Login ou senha incorretos")
                else: st.warning("Digite o usuário")
        with c2:
            if st.button("Criar Conta"):
                if user and pw:
                    check = run_query("SELECT username FROM usuarios WHERE username = :u", {"u": user})
                    if check.empty:
                        run_query("INSERT INTO usuarios (username, password) VALUES (:u, :p)", {"u": user, "p": pw}, is_select=False)
                        st.success("Conta criada com sucesso!")
                    else: st.error("Usuário já existe.")
                else: st.warning("Preencha tudo")
else:
    st.markdown(f"<h1 style='text-align: center;'>Painel Financeiro</h1>", unsafe_allow_html=True)
    if st.sidebar.button("Sair"): 
        st.session_state.logged_in = False
        st.rerun()

    df_full = run_query("SELECT * FROM servicos WHERE username=:u", {"u": st.session_state.username})
    df_creds = run_query("SELECT * FROM creditos WHERE username=:u", {"u": st.session_state.username})

    hoje = datetime.now().date()
    inicio_mes = hoje.replace(day=1)

    if not df_full.empty:
        df_full['data_dt'] = pd.to_datetime(df_full['data'])
        fat_dia = df_full[df_full['data_dt'].dt.date == hoje]['valor'].sum()
        fat_mes = df_full[df_full['data_dt'].dt.date >= inicio_mes]['valor'].sum()
        m1, m2 = st.columns(2)
        m1.metric("Faturamento Hoje", f"R$ {fat_dia:,.2f}")
        m2.metric("Faturamento Mês", f"R$ {fat_mes:,.2f}")

    tab1, tab2, tab3, tab4 = st.tabs(["➕ Novo", "📊 Histórico", "📈 Ranking", "💳 Créditos"])

    with tab1:
        st.markdown("### Novo serviço")
        data_serv = st.date_input("Data", value=hoje, format="DD/MM/YYYY")
        cat_serv = st.selectbox("Tipo", LISTA_SERVICOS)
        desc_serv = st.text_input("Detalhes")
        valor_serv = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
        if st.button("Salvar"):
            run_query("INSERT INTO servicos (username, data, categoria, descricao, valor) VALUES (:u, :d, :c, :de, :v)", 
                     {"u": st.session_state.username, "d": data_serv.strftime('%Y-%m-%d'), "c": cat_serv, "de": desc_serv, "v": valor_serv}, is_select=False)
            st.success("Registro efetuado!")
            st.rerun()

    with tab2:
        if not df_full.empty:
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
                st.plotly_chart(fig_rank, use_container_width=True)

    with tab4:
        c_nome = st.text_input("Nome do Cliente")
        c_valor = st.number_input("Valor do Crédito (R$)", min_value=0.0, step=0.5)
        cb1, cb2 = st.columns(2)
        with cb1:
            if st.button("Adicionar Crédito"):
                run_query("INSERT INTO creditos (username, cliente, valor, data) VALUES (:u, :cl, :v, :d)", 
                         {"u": st.session_state.username, "cl": c_nome.upper(), "v": c_valor, "d": hoje.strftime('%Y-%m-%d')}, is_select=False)
                st.rerun()
        with cb2:
            if st.button("Usar Crédito"):
                run_query("INSERT INTO creditos (username, cliente, valor, data) VALUES (:u, :cl, :v, :d)", 
                         {"u": st.session_state.username, "cl": c_nome.upper(), "v": -c_valor, "d": hoje.strftime('%Y-%m-%d')}, is_select=False)
                st.rerun()
        if not df_creds.empty:
            df_saldo = df_creds.groupby('cliente')['valor'].sum().reset_index()
            st.table(df_saldo[df_saldo['valor'] != 0])
