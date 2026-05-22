import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy import text
import re
import jwt
import json
from typing import Optional, Dict, Any
import hashlib
import secrets
import streamlit.components.v1 as components

# --- CONFIGURAÇÃO JWT ---
JWT_SECRET = "sua_chave_secreta_super_segura_aqui_123456"  # IMPORTANTE: Alterar em produção!
JWT_ALGORITHM = "HS256"        
TOKEN_EXPIRY_DAYS = 30

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
    /* Fundo principal branco */
    .stApp, .stMain, .stHeader, .stAppHeader, .block-container, [data-testid=\"stTabContent\"] {{
        background-color: #ffffff !important;
        color: #000000 !important;
    }}

    /* Forçar cor preta em textos e labels */
    html, body, [class*=\"st-b\"] {{ color: #000000 !important; }}
    .stMarkdown, .stText, [data-testid=\"stMetricValue\"], label, h1, h2, h3, p, span, 
    [data-testid=\"stWidgetLabel\"] p, table, th, td, [data-testid=\"stTable\"] td, 
    .stDataFrame, [data-testid=\"stMetricLabel\"] p {{
        color: #000000 !important;
        font-weight: 600 !important;
    }}
    
    /* Fix para Calendário e Selectbox */
    div[data-baseweb=\"calendar\"] *, div[data-baseweb=\"popover\"] *, 
    div[data-baseweb=\"select\"] *, .stSelectbox div[role=\"button\"] {{
        color: #000000 !important;
        background-color: #ffffff !important;
    }}

    /* Estilo dos campos de entrada */
    input, textarea {{ color: #000000 !important; background-color: #f0f2f6 !important; }}
    div[data-baseweb=\"select\"] > div {{ background-color: #ffffff !important; }}

    /* Botões */
    button[data-testid=\"baseButton-secondary\"], .stButton > button {{
        background-color: #ffc4d8 !important; color: #000000 !important; border-radius: 12px !important;
        width: 100% !important; border: 1px solid #ffb0cc !important; font-weight: bold !important;
    }}

    /* IMAGEM DE FUNDO - Restauração */
    .main-bg-container {{
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 0 !important;
        background-color: #ffffff;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        pointer-events: none !important;
    }}
    
    .bg-image {{
        width: 80vw !important;
        max-width: 500px !important;
        opacity: 0.15 !important;
    }}

    /* Garantir que o conteúdo do Streamlit fique por cima da imagem */
    [data-testid=\"stVerticalBlock\"] {{ position: relative !important; z-index: 10 !important; }}
    </style>
    <div class='main-bg-container'><img src='{URL_ICONE}' class='bg-image'></div>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="Gestão de Serviços Pro", layout="wide")
def salvar_token_localstorage(token: str):
    """Salva o token no localStorage do navegador via JavaScript"""
    components.html(f"""
        <script>
            localStorage.setItem('token', '{token}');
        </script>
    """, height=0)

def obter_token_localstorage() -> str | None:
    """Tenta ler o token do localStorage"""
    # Infelizmente não dá para ler diretamente do Python.
    # Vamos usar um componente que retorna o valor.
    # Alternativa: usar st.query_params para passar o token.
    pass
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
        sql_mod = query
        p_list = []
        if params:
            for k, v in params.items():
                sql_mod = re.sub(f":{k}\\b", "?", sql_mod)
                p_list.append(v)
        if is_select:
            df = pd.read_sql(sql_mod, conn, params=p_list)
            conn.close()
            return df
        else:
            c = conn.cursor()
            c.execute(sql_mod, p_list)
            conn.commit()
            conn.close()
            return None

def init_db():
    run_query("CREATE TABLE IF NOT EXISTS usuarios (username TEXT PRIMARY KEY, password TEXT)", is_select=False)
    run_query("CREATE TABLE IF NOT EXISTS servicos (username TEXT, data TEXT, categoria TEXT, descricao TEXT, valor NUMERIC)", is_select=False)
    run_query("CREATE TABLE IF NOT EXISTS creditos (username TEXT, cliente TEXT, valor NUMERIC, data TEXT)", is_select=False)
    run_query("""CREATE TABLE IF NOT EXISTS usuario_sessoes (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        token TEXT NOT NULL UNIQUE,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_expiracao TIMESTAMP NOT NULL,
        ativo BOOLEAN DEFAULT TRUE
    )""", is_select=False)

init_db()

# --- FUNÇÕES DE AUTENTICAÇÃO COM JWT ---
def gerar_token_jwt(username: str) -> str:
    """Gera um token JWT com expiração"""
    payload = {
        'username': username,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=TOKEN_EXPIRY_DAYS)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verificar_token_jwt(token: str) -> Optional[str]:
    """Verifica se o token JWT é válido e retorna o username"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get('username')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def salvar_sessao_supabase(username: str, token: str) -> bool:
    """Salva a sessão no banco de dados"""
    data_expiracao = datetime.utcnow() + timedelta(days=TOKEN_EXPIRY_DAYS)
    try:
        run_query("""INSERT INTO usuario_sessoes (username, token, data_expiracao) 
                    VALUES (:u, :t, :e)""",
                 {"u": username, "t": token, "e": data_expiracao},
                 is_select=False)
        return True
    except:
        return False

def validar_sessao_supabase(username: str, token: str) -> bool:
    """Valida se a sessão existe e está ativa no banco"""
    try:
        res = run_query("""SELECT ativo FROM usuario_sessoes 
                          WHERE username = :u AND token = :t AND data_expiracao > CURRENT_TIMESTAMP""",
                       {"u": username, "t": token})
        return not res.empty and res.iloc[0]['ativo']
    except:
        return False

def obter_usuario_de_token() -> str | None:
    # Primeiro tenta da URL
    token_url = st.query_params.get("token")
    if token_url:
        username = verificar_token_jwt(token_url)
        if username and validar_sessao_supabase(username, token_url):
            st.session_state.token_remember = token_url
            return username
         # Depois tenta do session_state (fallback)
    token = st.session_state.get('token_remember')
    if token:
        username = verificar_token_jwt(token)
        if username and validar_sessao_supabase(username, token):
            return username
        else:
            st.session_state.token_remember = None
    return None

def obter_usuario_de_cookies() -> Optional[str]:
    """Tenta recuperar usuário de um token salvo nos cookies do navegador"""
    # Nota: Streamlit não tem suporte nativo a cookies, mas podemos usar st.session_state como fallback
    # Para cookies reais, seria necessário usar uma biblioteca como streamlit-cookies ou javascript customizado
    if 'token_remember' in st.session_state and st.session_state.token_remember:
        token = st.session_state.token_remember
        username = verificar_token_jwt(token)
        if username and validar_sessao_supabase(username, token):
            return username
        else:
            # Token inválido ou expirado, limpar
            st.session_state.token_remember = None
    return None

def logout_completo():
    """Realiza logout completo, limpando sessões"""
    if 'username' in st.session_state and 'token_remember' in st.session_state:
        try:
            run_query("""UPDATE usuario_sessoes SET ativo = FALSE 
                        WHERE username = :u AND token = :t""",
                     {"u": st.session_state.username, "t": st.session_state.token_remember},
                     is_select=False)
        except:
            pass
    
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.token_remember = None

    st.query_params.clear()

# --- INICIALIZAR SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'token_remember' not in st.session_state: st.session_state.token_remember = None

# --- VERIFICAR SESSÃO SALVA AO INICIAR ---
if not st.session_state.logged_in:
    usuario_salvo = obter_usuario_de_cookies()
    if usuario_salvo:
        st.session_state.logged_in = True
        st.session_state.username = usuario_salvo
        st.rerun()

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center;'>Acesso ao Sistema</h1>", unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        user = st.text_input("Usuário", key="login_user")
        pw = st.text_input("Senha", type="password", key="login_pw")
        remember = st.checkbox("🔐 Lembrar meu login por 30 dias", value=False)
        
        if st.button("Entrar"):
            if user:
                res = run_query("SELECT password FROM usuarios WHERE username = :u", {"u": user})
                if not res.empty and str(res.iloc[0]['password']) == str(pw):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    
                    # Se marcou lembrar, gera e salva token
                    if remember:
                        token = gerar_token_jwt(user)
                        if salvar_sessao_supabase(user, token):
                            st.query_params["token"] = token
                            st.session_state.token_remember = token
                            st.success("✅ Login salvo! Você não precisará fazer login novamente por 30 dias.")
                        else:
                            st.warning("⚠️ Não foi possível salvar o login. Faça login normalmente da próxima vez.")
                    
                    st.rerun()
                else: st.error("Login ou senha incorretos")
            else: st.warning("Digite o usuário")
        
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
    
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("🚪 Sair"): 
            logout_completo()
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
            df_view['Valor'] = df_view['valor'].apply(lambda x: f"R$ {x:,.2f}")
            df_view = df_view.rename(columns={'data': 'Data', 'categoria': 'Categoria', 'descricao': 'Descrição'})
            st.dataframe(df_view[['Data', 'Categoria', 'Descrição', 'Valor']].sort_values('Data', ascending=False), use_container_width=True)

    with tab3:
        if not df_full.empty:
            st.markdown("### Faturamento por Categoria")
            df_mes = df_full[df_full['data_dt'].dt.date >= inicio_mes]
            if not df_mes.empty:
                df_rank = df_mes.groupby('categoria')['valor'].sum().reset_index().sort_values('valor', ascending=False)
                fig_rank = px.bar(df_rank, x='categoria', y='valor', color_discrete_sequence=['#ffc4d8'])
                st.plotly_chart(fig_rank, use_container_width=True)

            st.markdown("### Faturamento Semanal")
            df_full['segunda'] = df_full['data_dt'] - df_full['data_dt'].dt.weekday.map(lambda x: timedelta(days=x))
            df_full['domingo'] = df_full['segunda'] + timedelta(days=6)
            df_full['periodo'] = df_full['segunda'].dt.strftime('%d/%m') + " a " + df_full['domingo'].dt.strftime('%d/%m')
            df_semana = df_full.groupby(['segunda', 'periodo'])['valor'].sum().reset_index().sort_values('segunda')
            fig_semanal = px.bar(df_semana, x='periodo', y='valor', color_discrete_sequence=['#ffc4d8'])
            st.plotly_chart(fig_semanal, use_container_width=True)

    with tab4:
        c_nome = st.text_input("Nome do Cliente")
        c_valor = st.number_input("Valor (R$)", min_value=0.0, step=0.5)
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
            df_saldo['Saldo'] = df_saldo['valor'].apply(lambda x: f"R$ {x:,.2f}")
            df_saldo = df_saldo.rename(columns={'cliente': 'Cliente'})
            st.table(df_saldo[df_saldo['valor'] != 0][['Cliente', 'Saldo']])
