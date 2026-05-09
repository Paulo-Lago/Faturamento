import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
from sqlalchemy import text
import re

# --- CONFIGURAÇÃO ---
URL_ICONE = "https://preview.redd.it/53zg1z70jxzg1.jpeg?width=640&crop=smart&auto=webp&s=57ad5ec9bee948b825fe8e208f951f6ffd2739ee"
LISTA_SERVICOS = ["📄 Xérox", "🖨️ Impressão", "📝 Currículo", "🎬 Serviços de Edição", "🛡️ Plastificação", "📸 Impressão de Fotos", "⚙️ Outros"]

def aplicar_estilo_customizado():
    st.markdown(f"""<style>
    .stApp {{ background-color: #ffffff !important; color: #000000 !important; }}
    .stMarkdown, .stText, [data-testid='stMetricValue'], label, h1, h2, h3, p, span {{
        color: #000000 !important; font-weight: 600 !important;
    }}
    button {{ background-color: #ffc4d8 !important; color: #000000 !important; border-radius: 12px !important; }}
    </style>""", unsafe_allow_html=True)

st.set_page_config(page_title="Gestão de Serviços Pro", layout="wide")
aplicar_estilo_customizado()

# --- BANCO DE DADOS (SUPABASE PRIORITY) ---
def run_query(query, params=None, is_select=True):
    try:
        # Tenta conectar ao Supabase usando os Secrets do Streamlit Cloud
        conn = st.connection("postgresql", type="sql")
        with conn.session as s:
            if is_select:
                return pd.read_sql(text(query), s.bind, params=params)
            else:
                s.execute(text(query), params)
                s.commit()
                return None
    except Exception as e:
        st.warning("⚠️ Aviso: Usando banco local temporário. Configure os Secrets no Streamlit Cloud.")
        conn_local = sqlite3.connect('servicos_financeiro.db')
        sql_mod = query
        p_list = []
        if params:
            for k, v in params.items():
                sql_mod = re.sub(f":{k}\\b", "?", sql_mod)
                p_list.append(v)
        if is_select:
            df = pd.read_sql(sql_mod, conn_local, params=p_list)
            conn_local.close()
            return df
        else:
            c = conn_local.cursor()
            c.execute(sql_mod, p_list)
            conn_local.commit()
            conn_local.close()
            return None

def init_db():
    run_query("CREATE TABLE IF NOT EXISTS usuarios (username TEXT PRIMARY KEY, password TEXT)", is_select=False)
    run_query("CREATE TABLE IF NOT EXISTS servicos (id SERIAL PRIMARY KEY, username TEXT, data DATE, categoria TEXT, descricao TEXT, valor NUMERIC)", is_select=False)
    run_query("CREATE TABLE IF NOT EXISTS creditos (id SERIAL PRIMARY KEY, username TEXT, cliente TEXT, valor NUMERIC, data DATE)", is_select=False)

init_db()

# --- INTERFACE DE LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>Acesso ao Sistema</h1>", unsafe_allow_html=True)
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    c1, c2 = st.columns(2)
    if c1.button("Entrar"):
        res = run_query("SELECT password FROM usuarios WHERE username = :u", {"u": user})
        if not res.empty and str(res.iloc[0]['password']) == str(pw):
            st.session_state.logged_in, st.session_state.username = True, user
            st.rerun()
        else: st.error("Login inválido.")
    if c2.button("Criar Conta"):
        run_query("INSERT INTO usuarios (username, password) VALUES (:u, :p)", {"u": user, "p": pw}, is_select=False)
        st.success("Conta criada! Tente logar.")
else:
    st.sidebar.write(f"Usuário: **{st.session_state.username}**")
    if st.sidebar.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["➕ Novo", "📊 Histórico", "📈 Ranking", "💳 Créditos"])

    with tab1:
        st.subheader("Registrar Serviço")
        data_s = st.date_input("Data", datetime.now().date())
        cat_s = st.selectbox("Categoria", LISTA_SERVICOS)
        desc_s = st.text_input("Descrição")
        val_s = st.number_input("Valor", min_value=0.0)
        if st.button("Salvar Serviço"):
            run_query("INSERT INTO servicos (username, data, categoria, descricao, valor) VALUES (:u, :d, :c, :des, :v)",
                     {"u": st.session_state.username, "d": data_s, "c": cat_s, "des": desc_s, "v": val_s}, is_select=False)
            st.success("Salvo com sucesso!")

    with tab2:
        st.subheader("Histórico de Atividades")
        df = run_query("SELECT data, categoria, descricao, valor FROM servicos WHERE username = :u", {"u": st.session_state.username})
        if not df.empty:
            df_view = df.rename(columns={'data': 'Data', 'categoria': 'Categoria', 'descricao': 'Descrição', 'valor': 'Valor'})
            st.dataframe(df_view.sort_values('Data', ascending=False), use_container_width=True)
        else: st.info("Nenhum serviço registrado.")

    with tab3:
        df = run_query("SELECT categoria, valor FROM servicos WHERE username = :u", {"u": st.session_state.username})
        if not df.empty:
            fig = px.pie(df, values='valor', names='categoria', title="Faturamento por Categoria")
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Controle de Créditos")
        cli = st.text_input("Nome do Cliente")
        v_c = st.number_input("Valor", min_value=0.0)
        if st.button("Adicionar Crédito"):
            run_query("INSERT INTO creditos (username, cliente, valor, data) VALUES (:u, :cl, :v, :d)",
                     {"u": st.session_state.username, "cl": cli.upper(), "v": v_c, "d": datetime.now().date()}, is_select=False)
            st.rerun()
        df_c = run_query("SELECT cliente as Cliente, SUM(valor) as Saldo FROM creditos WHERE username = :u GROUP BY cliente", {"u": st.session_state.username})
        if not df_c.empty: st.table(df_c)
