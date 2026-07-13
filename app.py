import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
import re
import jwt  # pyright: ignore[reportMissingImports]
from typing import Optional

# --- CONFIGURAÇÃO JWT ---
JWT_SECRET = st.secrets["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_DAYS = 30

# --- CONFIGURAÇÃO GERAL ---
URL_ICONE = "https://preview.redd.it/53zg1z70jxzg1.jpeg?width=640&crop=smart&auto=webp&s=57ad5ec9bee948b825fe8e208f951f6ffd2739ee"
LISTA_SERVICOS = [
    "📄 Xérox",
    "🖨️ Impressão em Papel Comum",
    "🖨️ Impressão em Papel Fotográfico",
    "🖨️ Impressão em Papel Adesivo",
    "🖨️ Impressão em Papel de Diploma",
    "📸 Foto 3x4",
    "📝 Currículo",
    "🃴 Venda de Figurinhas",
    "🍞 Pão",
    "🎬 Serviços de Edição",
    "🛡️ Plastificação",
    "⚙️ Outros"
]
CONFIG_GRAFICO_ESTATICO = {
    "staticPlot": True,
    "displayModeBar": False,
    "scrollZoom": False,
    "responsive": True,
}


def combinar_categorias(categorias):
    return " + ".join(categorias)


def separar_categorias(categoria):
    return [item.strip() for item in str(categoria).split(" + ") if item.strip()]


def data_atual_brasilia(agora_utc=None):
    agora_utc = agora_utc or datetime.now(timezone.utc)
    return agora_utc.astimezone(timezone(timedelta(hours=-3))).date()


def registrar_feedback_operacao(mensagem):
    st.session_state["feedback_operacao"] = mensagem


def exibir_feedback_operacao():
    mensagem = st.session_state.pop("feedback_operacao", None)
    if mensagem:
        st.success(mensagem)
        st.balloons()


def estilizar_grafico(fig):
    fig.update_layout(
        font=dict(color="#111827"),
        title_font=dict(color="#111827"),
        xaxis=dict(tickfont=dict(color="#111827"), title_font=dict(color="#111827")),
        yaxis=dict(tickfont=dict(color="#111827"), title_font=dict(color="#111827")),
        legend=dict(font=dict(color="#111827")),
    )
    return fig


def exibir_tabela_responsiva(df, colunas_sem_quebra=None):
    colunas_sem_quebra = colunas_sem_quebra or []
    tabela_id = f"tabela-{abs(hash(tuple(df.columns)))}"
    indices = [
        df.columns.get_loc(coluna) + 1
        for coluna in colunas_sem_quebra
        if coluna in df.columns
    ]
    regras = "".join(
        f".{tabela_id} th:nth-child({indice}), "
        f".{tabela_id} td:nth-child({indice}) {{ white-space: nowrap; }}"
        for indice in indices
    )
    html = df.to_html(
        index=False,
        escape=True,
        border=0,
        classes=["tabela-responsiva", tabela_id],
    )
    st.markdown(
        f"<style>{regras}</style><div class='tabela-scroll'>{html}</div>",
        unsafe_allow_html=True,
    )


def nome_tipo_duplicado(df_tipos, nome, tipo_id_atual=None):
    if df_tipos.empty:
        return False

    duplicados = df_tipos["nome"].fillna("").str.strip().str.upper() == nome.strip().upper()
    if tipo_id_atual is not None:
        ids = pd.to_numeric(df_tipos["id"], errors="coerce")
        duplicados &= ids != int(tipo_id_atual)
    return bool(duplicados.any())


def contar_despesas_tipo(df_despesas, tipo_id):
    if df_despesas.empty or "tipo_id" not in df_despesas.columns:
        return 0

    ids = pd.to_numeric(df_despesas["tipo_id"], errors="coerce")
    return int((ids == int(tipo_id)).sum())


def aplicar_estilo_customizado():
    st.markdown(f"""
    <style>
    /* Fundo principal branco */
    .stApp, .stMain, .stHeader, .stAppHeader, .block-container, [data-testid=\"stTabContent\"] {{
        background: linear-gradient(180deg, #fffdfd 0%, #fff8fb 100%) !important;
        color: #1f2937 !important;
    }}
    /* Forçar cor preta em textos e labels */
    html, body, [class*=\"st-b\"] {{ color: #1f2937 !important; }}
    .stMarkdown, .stText, [data-testid=\"stMetricValue\"], label, h1, h2, h3, p, span,
    [data-testid=\"stWidgetLabel\"] p, table, th, td, [data-testid=\"stTable\"] td,
    .stDataFrame, [data-testid=\"stMetricLabel\"] p {{
        color: #1f2937 !important;
    }}
    /* Fix para Calendário e Selectbox */
    div[data-baseweb=\"calendar\"] *, div[data-baseweb=\"popover\"] *,
    div[data-baseweb=\"select\"] *, .stSelectbox div[role=\"button\"] {{
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }}
    /* Estilo dos campos de entrada */
    input, textarea {{ color: #1f2937 !important; background-color: rgba(255, 255, 255, 0.96) !important; border-radius: 12px !important; }}
    div[data-baseweb=\"select\"] > div {{ background-color: #ffffff !important; border-radius: 12px !important; }}
    /* Botões */
    button[data-testid=\"baseButton-secondary\"],
    button[data-testid=\"baseButton-primary\"],
    button[data-testid=\"stBaseButton-secondary\"],
    button[data-testid=\"stBaseButton-primary\"],
    .stButton > button,
    [data-testid=\"stFormSubmitButton\"] > button {{
        background-color: #ffe4ef !important; color: #1f2937 !important; border-radius: 14px !important;
        width: 100% !important; border: 1px solid #f9a8d4 !important; font-weight: 600 !important; min-height: 2.8rem !important;
    }}
    button[data-testid=\"baseButton-secondary\"] p,
    button[data-testid=\"baseButton-primary\"] p,
    button[data-testid=\"stBaseButton-secondary\"] p,
    button[data-testid=\"stBaseButton-primary\"] p,
    .stButton > button p,
    [data-testid=\"stFormSubmitButton\"] > button p {{
        color: #1f2937 !important;
    }}
    /* IMAGEM DE FUNDO */
    .main-bg-container {{
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 0 !important;
        background-color: transparent;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        pointer-events: none !important;
    }}
    .bg-image {{
        width: 80vw !important;
        max-width: 500px !important;
        opacity: 0.08 !important;
    }}
    [data-testid=\"stVerticalBlock\"] {{ position: relative !important; z-index: 10 !important; }}
    .block-container {{ padding-top: 1.5rem !important; padding-bottom: 2.5rem !important; max-width: 1100px; }}
    h1, h2, h3 {{ letter-spacing: -0.02em; }}
    p, [data-testid=\"stCaptionContainer\"] {{ color: #374151 !important; }}
    [data-testid=\"stMetric\"] {{ background: rgba(255,255,255,0.9); border: 1px solid rgba(249,168,212,0.45); border-radius: 18px; padding: 0.8rem 1rem; box-shadow: 0 16px 30px rgba(15, 23, 42, 0.05); }}
    [data-testid=\"stMetricLabel\"] p {{ color: #6b7280 !important; font-weight: 600 !important; }}
    [data-testid=\"stMetricValue\"] {{ color: #1f2937 !important; font-weight: 700 !important; }}
    [data-testid=\"stTabs\"] {{ margin-top: 1rem; }}
    .hero-card, .login-card, .danger-card {{ background: rgba(255,255,255,0.9); border: 1px solid rgba(249,168,212,0.35); border-radius: 22px; padding: 1.15rem 1.2rem; box-shadow: 0 18px 36px rgba(15, 23, 42, 0.05); }}
    .login-card {{ margin-top: 1rem; padding: 1.4rem; }}
    .hero-card h1, .login-card h1 {{ margin-bottom: 0.25rem; }}
    .hero-card p, .login-card p {{ margin-bottom: 0; }}
    .danger-card {{ background: #fff1f2; border-color: #fda4af; margin-top: 0.8rem; }}
    .sheet-card {{ background: rgba(255,255,255,0.92); border: 1px solid rgba(209,213,219,0.8); border-radius: 16px; padding: 0.75rem; box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04); }}
    [data-testid=\"stDataFrame\"] {{ border-radius: 14px; overflow: hidden; border: 1px solid rgba(209,213,219,0.8); }}
    .tabela-scroll {{ width: 100%; overflow-x: auto; border: 1px solid #d1d5db; border-radius: 14px; background: #ffffff; }}
    .tabela-responsiva {{ width: 100%; min-width: 680px; border-collapse: collapse; color: #111827; }}
    .tabela-responsiva th, .tabela-responsiva td {{ padding: 0.72rem 0.8rem; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; color: #111827 !important; }}
    .tabela-responsiva th {{ background: #f9fafb; font-weight: 700; white-space: nowrap; }}
    .tabela-responsiva td {{ white-space: normal; overflow-wrap: break-word; word-break: normal; }}
    .tabela-responsiva tr:last-child td {{ border-bottom: 0; }}
    @media (max-width: 768px) {{ .block-container {{ padding-top: 1rem !important; }} .bg-image {{ width: 92vw !important; opacity: 0.05 !important; }} }}
    </style>
    <div class='main-bg-container'><img src='{URL_ICONE}' class='bg-image'></div>
    """, unsafe_allow_html=True)

st.set_page_config(page_title="Gestão de Serviços Pro", layout="wide")
aplicar_estilo_customizado()

# --- CONEXÃO EXCLUSIVA COM SUPABASE ---
@st.cache_resource
def get_connection():
    """Retorna a conexão com o Supabase via st.connection."""
    try:
        return st.connection("postgresql", type="sql")
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao Supabase: {e}")
        st.error("Verifique se as secrets do Streamlit estão configuradas corretamente.")
        st.stop()

def run_query(query, params=None, is_select=True):
    """Executa queries no Supabase (apenas PostgreSQL)."""
    conn = get_connection()
    with conn.session as s:
        if is_select:
            return pd.read_sql(text(query), s.bind, params=params)
        else:
            s.execute(text(query), params)
            s.commit()
            return None

def init_db():
    """Cria as tabelas necessárias no Supabase e adiciona a coluna 'id' se necessário."""
    run_query("CREATE TABLE IF NOT EXISTS usuarios (username TEXT PRIMARY KEY, password TEXT)", is_select=False)
    run_query("CREATE TABLE IF NOT EXISTS servicos (username TEXT, data TEXT, categoria TEXT, descricao TEXT, valor NUMERIC)", is_select=False)
    run_query("CREATE TABLE IF NOT EXISTS creditos (username TEXT, cliente TEXT, valor NUMERIC, data TEXT)", is_select=False)
    run_query("CREATE TABLE IF NOT EXISTS tipos_despesa (id SERIAL PRIMARY KEY, username TEXT, nome TEXT)", is_select=False)
    run_query("""CREATE TABLE IF NOT EXISTS despesas (
        id SERIAL PRIMARY KEY,
        username TEXT,
        data TEXT,
        tipo_id INTEGER,
        descricao TEXT,
        valor NUMERIC
    )""", is_select=False)
    run_query("""CREATE TABLE IF NOT EXISTS usuario_sessoes (
        id SERIAL PRIMARY KEY,
        username TEXT NOT NULL,
        token TEXT NOT NULL UNIQUE,
        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_expiracao TIMESTAMP NOT NULL,
        ativo BOOLEAN DEFAULT TRUE
    )""", is_select=False)

    # Adicionar coluna 'id' na tabela 'servicos' se não existir
    try:
        run_query("SELECT id FROM servicos LIMIT 0", is_select=True)
    except Exception:
        run_query("ALTER TABLE servicos ADD COLUMN id SERIAL PRIMARY KEY", is_select=False)
        st.info("✅ Coluna 'id' adicionada à tabela 'servicos'.")

init_db()

# --- FUNÇÕES DE AUTENTICAÇÃO COM JWT ---
def gerar_token_jwt(username: str) -> str:
    payload = {
        'username': username,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verificar_token_jwt(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get('username')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def salvar_sessao_supabase(username: str, token: str) -> bool:
    data_expiracao = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)
    try:
        run_query("""INSERT INTO usuario_sessoes (username, token, data_expiracao)
                    VALUES (:u, :t, :e)""",
                  {"u": username, "t": token, "e": data_expiracao},
                  is_select=False)
        return True
    except Exception:
        return False

def validar_sessao_supabase(username: str, token: str) -> bool:
    try:
        res = run_query("""SELECT ativo FROM usuario_sessoes
                          WHERE username = :u AND token = :t AND data_expiracao > CURRENT_TIMESTAMP""",
                        {"u": username, "t": token})
        return not res.empty and bool(res.iloc[0]['ativo'])
    except Exception:
        return False

def obter_usuario_por_token(token: str) -> Optional[str]:
    username = verificar_token_jwt(token)
    if username and validar_sessao_supabase(username, token):
        return username
    return None

def restaurar_sessao():
    token_url = st.query_params.get("token")
    if token_url:
        username = obter_usuario_por_token(token_url)
        if username:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.token_remember = token_url
            return True
    token_state = st.session_state.get('token_remember')
    if token_state:
        username = obter_usuario_por_token(token_state)
        if username:
            st.session_state.logged_in = True
            st.session_state.username = username
            return True
        else:
            st.session_state.token_remember = None
    return False

def logout_completo():
    if 'username' in st.session_state and 'token_remember' in st.session_state:
        try:
            run_query("""UPDATE usuario_sessoes SET ativo = FALSE
                        WHERE username = :u AND token = :t""",
                      {"u": st.session_state.username, "t": st.session_state.token_remember},
                      is_select=False)
        except Exception:
            pass
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.token_remember = None
    st.query_params.clear()
    st.rerun()

# --- INICIALIZAR SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'token_remember' not in st.session_state:
    st.session_state.token_remember = None

# --- TENTAR RESTAURAR SESSÃO AO CARREGAR ---
if not st.session_state.logged_in:
    if restaurar_sessao():
        st.rerun()

# --- TELA DE LOGIN ---
if not st.session_state.logged_in:
    st.markdown("""
    <div class='login-card'>
        <h1 style='text-align: center;'>Acesse sua conta</h1>
        <p style='text-align: center;'>Entre para registrar serviços, acompanhar resultados e controlar créditos.</p>
    </div>
    """, unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        user = st.text_input("Usuário", key="login_user", placeholder="Digite seu usuário")
        pw = st.text_input("Senha", type="password", key="login_pw", placeholder="Digite sua senha")
        remember = st.checkbox("🔐 Lembrar meu login por 30 dias", value=False)

        if st.button("Entrar"):
            if user:
                res = run_query("SELECT password FROM usuarios WHERE username = :u", {"u": user})
                if not res.empty and str(res.iloc[0]['password']) == str(pw):
                    st.session_state.logged_in = True
                    st.session_state.username = user

                    if remember:
                        token = gerar_token_jwt(user)
                        if salvar_sessao_supabase(user, token):
                            st.query_params["token"] = token
                            st.session_state.token_remember = token
                            st.success("✅ Login concluído com acesso automático ativo por 30 dias.")
                        else:
                            st.warning("⚠️ O login foi concluído, mas não foi possível ativar o acesso automático.")
                    else:
                        st.query_params.clear()
                        st.session_state.token_remember = None

                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos. Verifique os dados e tente novamente.")
            else:
                st.warning("Informe seu usuário para continuar.")

        if st.button("Criar conta"):
            if user and pw:
                check = run_query("SELECT username FROM usuarios WHERE username = :u", {"u": user})
                if check.empty:
                    run_query("INSERT INTO usuarios (username, password) VALUES (:u, :p)",
                              {"u": user, "p": pw}, is_select=False)
                    st.success("Conta criada com sucesso. Agora faça seu login.")
                else:
                    st.error("Esse usuário já está cadastrado.")
            else:
                st.warning("Preencha usuário e senha para criar sua conta.")
    st.stop()

# --- ÁREA DO PAINEL ---
st.markdown("""
<div class='hero-card'>
    <h1 style='text-align: center;'>Painel Financeiro</h1>
    <p style='text-align: center;'>Acompanhe seus registros, resultados do período e créditos de clientes em um só lugar.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([9, 1])
with col2:
    if st.button("🚪 Sair"):
        logout_completo()

exibir_feedback_operacao()

df_full = run_query("SELECT * FROM servicos WHERE username=:u", {"u": st.session_state.username})
df_creds = run_query("SELECT * FROM creditos WHERE username=:u", {"u": st.session_state.username})
df_expenses = run_query("""SELECT d.*, t.nome AS tipo_nome
                           FROM despesas d
                           LEFT JOIN tipos_despesa t ON d.tipo_id = t.id
                           WHERE d.username=:u""", {"u": st.session_state.username})
df_expense_types = run_query("SELECT * FROM tipos_despesa WHERE username=:u ORDER BY nome", {"u": st.session_state.username})

hoje = data_atual_brasilia()
inicio_mes = hoje.replace(day=1)

fat_dia = 0.0
fat_mes = 0.0
if not df_full.empty:
    df_full['data_dt'] = pd.to_datetime(df_full['data'])
    fat_dia = df_full[df_full['data_dt'].dt.date == hoje]['valor'].sum()
    fat_mes = df_full[df_full['data_dt'].dt.date >= inicio_mes]['valor'].sum()

m1, m2 = st.columns(2)
m1.metric("Faturamento Hoje", f"R$ {fat_dia:,.2f}")
m2.metric("Faturamento Mês", f"R$ {fat_mes:,.2f}")

if df_full.empty:
    st.info("Comece cadastrando seu primeiro serviço para acompanhar o faturamento do dia e do mês.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Novo serviço", "📊 Histórico", "📈 Análises", "💳 Créditos", "🧾 Despesas"])

with tab1:
    st.markdown("### Novo serviço")
    st.caption("Registre rapidamente um atendimento ou venda realizada hoje.")
    with st.form("form_novo_servico", clear_on_submit=True):
        data_serv = st.date_input("Data", value=hoje, format="DD/MM/YYYY")
        cat_servicos = st.multiselect(
            "Tipos de serviço",
            LISTA_SERVICOS,
            placeholder="Selecione um ou mais serviços",
        )
        desc_serv = st.text_input("Detalhes", placeholder="Ex: 20 cópias coloridas, currículo, plastificação...")
        valor_serv = st.number_input("Valor (R$)", min_value=0.0, step=1.0, value=None, format="%.2f")
        salvar_servico = st.form_submit_button("Salvar serviço", width="stretch")

    if salvar_servico:
        if not cat_servicos:
            st.warning("Selecione pelo menos um serviço ou produto.")
        elif valor_serv is None or valor_serv <= 0:
            st.warning("Informe um valor positivo para o serviço.")
        else:
            run_query("INSERT INTO servicos (username, data, categoria, descricao, valor) VALUES (:u, :d, :c, :de, :v)",
                      {"u": st.session_state.username, "d": data_serv.strftime('%Y-%m-%d'),
                       "c": combinar_categorias(cat_servicos), "de": desc_serv, "v": valor_serv}, is_select=False)
            registrar_feedback_operacao("Serviço salvo com sucesso.")
            st.rerun()

with tab2:
    st.markdown("### Histórico de serviços")
    st.caption("Consulte, ajuste ou exclua registros já lançados.")

    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        data_inicio = st.date_input("Data Inicial", value=inicio_mes, format="DD/MM/YYYY")
    with col_filtro2:
        data_fim = st.date_input("Data Final", value=hoje, format="DD/MM/YYYY")

    if data_inicio > data_fim:
        st.warning("A data inicial não pode ser maior que a data final.")
    else:
        df_full['data_dt'] = pd.to_datetime(df_full['data'])
        df_filtrado = df_full[
            (df_full['data_dt'].dt.date >= data_inicio) &
            (df_full['data_dt'].dt.date <= data_fim)
        ].sort_values('data_dt', ascending=False)

        if df_filtrado.empty:
            st.info("Nenhum serviço foi encontrado nesse período. Ajuste os filtros ou registre um novo serviço.")
        else:
            df_sheet = df_filtrado.copy()
            df_sheet['Data'] = df_sheet['data_dt'].dt.strftime('%d/%m/%Y')
            df_sheet['Tipo'] = df_sheet['categoria']
            df_sheet['Detalhes'] = df_sheet['descricao']
            df_sheet['Valor'] = df_sheet['valor'].apply(lambda x: f"R$ {x:,.2f}")
            exibir_tabela_responsiva(
                df_sheet[['Data', 'Tipo', 'Detalhes', 'Valor']],
                colunas_sem_quebra=["Data", "Valor"],
            )
            opcoes_servico = {
                int(row['id']): f"{pd.to_datetime(row['data']).strftime('%d/%m/%Y')} | {row['categoria']} | R$ {float(row['valor']):,.2f}"
                for _, row in df_filtrado.iterrows() if pd.notna(row.get('id'))
            }
            if not opcoes_servico:
                st.warning("Os registros encontrados não têm identificação suficiente para edição.")
            else:
                if st.session_state.pop("limpar_servico_gerenciar", False):
                    st.session_state.pop("servico_gerenciar", None)

                id_servico = st.selectbox(
                    "Selecione um registro para editar ou excluir",
                    options=list(opcoes_servico.keys()),
                    format_func=lambda servico_id: opcoes_servico[servico_id],
                    index=None,
                    placeholder="Escolha um serviço",
                    key="servico_gerenciar",
                )

                if id_servico is not None:
                    row = df_filtrado[df_filtrado['id'] == id_servico].iloc[0]
                    categoria = row['categoria']
                    descricao = row['descricao']
                    valor = row['valor']
                    nova_data = st.date_input("Data", value=pd.to_datetime(row['data']).date(), format="DD/MM/YYYY", key=f"data_{id_servico}")

                    categorias_atuais = separar_categorias(categoria)
                    opcoes_categoria = list(dict.fromkeys(LISTA_SERVICOS + categorias_atuais))
                    nova_cat = st.multiselect(
                        "Tipos de serviço",
                        opcoes_categoria,
                        default=categorias_atuais,
                        key=f"cat_{id_servico}",
                    )
                    nova_desc = st.text_input("Detalhes", value=descricao, key=f"desc_{id_servico}")
                    novo_valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0, value=float(valor), format="%.2f", key=f"valor_{id_servico}")

                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("💾 Salvar alterações", key=f"salvar_{id_servico}"):
                            if not nova_cat:
                                st.warning("Selecione pelo menos um serviço ou produto.")
                            else:
                                run_query("""UPDATE servicos SET data=:d, categoria=:c, descricao=:de, valor=:v
                                            WHERE id=:id AND username=:u""",
                                          {"d": nova_data.strftime('%Y-%m-%d'), "c": combinar_categorias(nova_cat), "de": nova_desc,
                                           "v": novo_valor, "id": id_servico, "u": st.session_state.username},
                                          is_select=False)
                                st.session_state["limpar_servico_gerenciar"] = True
                                registrar_feedback_operacao("Alterações salvas com sucesso.")
                                st.rerun()
                    with col_del:
                        if st.button("🗑️ Excluir serviço", key=f"excluir_{id_servico}"):
                            st.markdown("<div class='danger-card'><strong>Confirme a exclusão.</strong><br>Essa ação remove o registro permanentemente.</div>", unsafe_allow_html=True)
                            confirmar = st.checkbox("Confirmo que desejo excluir este serviço.", key=f"conf_{id_servico}")
                            if confirmar:
                                run_query("DELETE FROM servicos WHERE id=:id AND username=:u",
                                          {"id": id_servico, "u": st.session_state.username}, is_select=False)
                                st.session_state["limpar_servico_gerenciar"] = True
                                registrar_feedback_operacao("Serviço excluído com sucesso.")
                                st.rerun()

with tab3:
    st.markdown("### 📊 Análise de faturamento")
    st.caption("Use os filtros para visualizar o desempenho por categoria e por semana.")

    # --- Filtro de período para os gráficos ---
    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        data_inicio_graf = st.date_input("Período - Data Inicial", value=inicio_mes, format="DD/MM/YYYY", key="graf_inicio")
    with col_filtro2:
        data_fim_graf = st.date_input("Período - Data Final", value=hoje, format="DD/MM/YYYY", key="graf_fim")

    if data_inicio_graf > data_fim_graf:
        st.warning("Data inicial não pode ser maior que a data final.")
    else:
        # Filtrar o DataFrame principal pelo período escolhido
        df_periodo = df_full[
            (df_full['data_dt'].dt.date >= data_inicio_graf) &
            (df_full['data_dt'].dt.date <= data_fim_graf)
        ].copy()

        if df_periodo.empty:
            st.info("Ainda não há dados nesse período. Ajuste os filtros ou registre novos serviços para visualizar os gráficos.")
        else:
            # Total do período
            total_periodo = df_periodo['valor'].sum()
            st.metric("💰 Faturamento Total no Período", f"R$ {total_periodo:,.2f}")
            st.divider()

            # ======================================================
            # DASHBOARD FINANCEIRO - RECEITAS x DESPESAS x LUCRO
            # ======================================================

            st.markdown("## 📊 Dashboard Financeiro")

            # Buscar despesas do mesmo período do gráfico
            if not df_expenses.empty:
                df_expenses['data_dt'] = pd.to_datetime(df_expenses['data'])

                df_desp_periodo_graf = df_expenses[
                    (df_expenses['data_dt'].dt.date >= data_inicio_graf) &
                    (df_expenses['data_dt'].dt.date <= data_fim_graf)
                ].copy()

                total_despesas_periodo = df_desp_periodo_graf['valor'].sum()

            else:
                total_despesas_periodo = 0


            # Cálculo do lucro
            lucro_liquido = total_periodo - total_despesas_periodo


            # Cards financeiros
            col_fin1, col_fin2, col_fin3 = st.columns(3)

            with col_fin1:
                st.metric(
                    "💰 Receitas",
                    f"R$ {total_periodo:,.2f}"
                )

            with col_fin2:
                st.metric(
                    "📉 Despesas",
                    f"R$ {total_despesas_periodo:,.2f}"
                )

            with col_fin3:
                st.metric(
                    "📈 Lucro Líquido",
                    f"R$ {lucro_liquido:,.2f}",
                    delta=f"{(lucro_liquido / total_periodo * 100):.1f}% da receita" 
                    if total_periodo > 0 else None
                )


            st.divider()


            # Gráfico comparativo
            df_financeiro = pd.DataFrame({
                "Categoria": [
                    "Receitas",
                    "Despesas",
                    "Lucro Líquido"
                ],
                "Valor": [
                    total_periodo,
                    total_despesas_periodo,
                    lucro_liquido
                ]
            })


            fig_financeiro = px.bar(
                df_financeiro,
                x="Categoria",
                y="Valor",
                text="Valor",
                title="Resumo financeiro do período",
                labels={
                    "Categoria": "",
                    "Valor": "Valor (R$)"
                },
                color="Categoria"
            )


            fig_financeiro.update_traces(
                texttemplate="R$ %{y:,.2f}",
                textposition="outside",
                cliponaxis=False
            )


            fig_financeiro.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(
                    l=10,
                    r=10,
                    t=60,
                    b=10
                )
            )


            estilizar_grafico(fig_financeiro)

            st.plotly_chart(
                fig_financeiro,
                width="stretch",
                config=CONFIG_GRAFICO_ESTATICO
            )


            # Gráfico pizza distribuição financeira
            st.markdown("### Distribuição do dinheiro")


            df_pizza = pd.DataFrame({
                "Tipo": [
                    "Despesas",
                    "Lucro"
                ],
                "Valor": [
                    total_despesas_periodo,
                    max(lucro_liquido, 0)
                ]
            })


            fig_pizza = px.pie(
                df_pizza,
                values="Valor",
                names="Tipo",
                title="Destino da receita"
            )


            fig_pizza.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
            )


            st.plotly_chart(
                fig_pizza,
                width="stretch",
                config=CONFIG_GRAFICO_ESTATICO
            )

            st.divider()


            # --- Gráfico 1: Faturamento por Categoria ---
            st.markdown("### Faturamento por categoria")
            df_rank = df_periodo.groupby('categoria')['valor'].sum().reset_index().sort_values('valor', ascending=False)
            fig_rank = px.bar(
                df_rank,
                x='categoria',
                y='valor',
                text='valor',
                title="Serviços com maior faturamento no período",
                labels={'categoria': 'Tipo de Serviço', 'valor': 'Valor (R$)'},
                color_discrete_sequence=['#ffc4d8']
            )

            fig_rank.update_traces(
                texttemplate='R$ %{y:,.2f}',
                textposition='outside',
                cliponaxis=False
            )
            fig_rank.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=60, b=10))
            estilizar_grafico(fig_rank)
            st.plotly_chart(fig_rank, width="stretch", config=CONFIG_GRAFICO_ESTATICO)

            st.divider()

            # --- Gráfico 2: Faturamento Semanal (baseado no período filtrado) ---
            st.markdown("### Faturamento semanal")

            # Garantir que os dados estão ordenados por data
            df_periodo_semana = df_periodo.sort_values('data_dt')

            # Calcular a semana (segunda a domingo) para cada registro
            df_periodo_semana['segunda'] = df_periodo_semana['data_dt'] - df_periodo_semana['data_dt'].dt.weekday.map(lambda x: timedelta(days=x))
            df_periodo_semana['domingo'] = df_periodo_semana['segunda'] + timedelta(days=6)
            df_periodo_semana['periodo'] = df_periodo_semana['segunda'].dt.strftime('%d/%m') + " a " + df_periodo_semana['domingo'].dt.strftime('%d/%m')

            df_semana = df_periodo_semana.groupby(['segunda', 'periodo'])['valor'].sum().reset_index().sort_values('segunda')

            if df_semana.empty:
                st.info("Não há dados suficientes para montar o gráfico semanal nesse período.")
            else:
                fig_semanal = px.bar(
                    df_semana,
                    x='periodo',
                    y='valor',
                    text='valor',
                    title="Evolução semanal do faturamento",
                    labels={'periodo': 'Semana', 'valor': 'Valor (R$)'},
                    color_discrete_sequence=['#ffc4d8']
                )

                fig_semanal.update_traces(
                    texttemplate='R$ %{y:,.2f}',
                    textposition='outside',
                    cliponaxis=False
                )
                fig_semanal.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=60, b=10))
                estilizar_grafico(fig_semanal)
                st.plotly_chart(fig_semanal, width="stretch", config=CONFIG_GRAFICO_ESTATICO)

with tab4:
    st.markdown("### 💳 Gestão de créditos")
    st.caption("Acompanhe o saldo dos clientes e registre entradas ou débitos com facilidade.")

    # Inicializar estados de controle
    if "credito_atualizado" not in st.session_state:
        st.session_state.credito_atualizado = False

    # Recarregar dados se necessário
    if st.session_state.credito_atualizado:
        df_creds = run_query("SELECT * FROM creditos WHERE username=:u", {"u": st.session_state.username})
        st.session_state.credito_atualizado = False

    # --- Formulário de movimentação (estilo card) ---
    with st.container(border=True):
        st.markdown("#### Registrar crédito ou débito")
        with st.form("form_credito", clear_on_submit=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                cliente_nome = st.text_input("Nome do Cliente", key="cliente_cred", placeholder="Ex: João Silva")
            with col2:
                valor_mov = st.number_input("Valor (R$)", min_value=0.0, step=0.5, value=None, format="%.2f", key="valor_cred")

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                adicionar_credito = st.form_submit_button("➕ Adicionar Crédito", width="stretch", type="primary")
            with col_btn2:
                usar_credito = st.form_submit_button("🔻 Usar Crédito", width="stretch")

        if adicionar_credito:
            if cliente_nome and valor_mov is not None and valor_mov > 0:
                run_query("INSERT INTO creditos (username, cliente, valor, data) VALUES (:u, :cl, :v, :d)",
                          {"u": st.session_state.username, "cl": cliente_nome.upper(), "v": valor_mov,
                           "d": hoje.strftime('%Y-%m-%d')}, is_select=False)
                st.session_state.credito_atualizado = True
                registrar_feedback_operacao(
                    f"Crédito de R$ {valor_mov:.2f} registrado para {cliente_nome.upper()}."
                )
                st.rerun()
            else:
                st.warning("Preencha o nome do cliente e informe um valor positivo.")

        if usar_credito:
            if cliente_nome and valor_mov is not None and valor_mov > 0:
                saldo_atual = df_creds[df_creds['cliente'] == cliente_nome.upper()]['valor'].sum() if not df_creds.empty else 0
                if saldo_atual >= valor_mov:
                    run_query("INSERT INTO creditos (username, cliente, valor, data) VALUES (:u, :cl, :v, :d)",
                              {"u": st.session_state.username, "cl": cliente_nome.upper(), "v": -valor_mov,
                               "d": hoje.strftime('%Y-%m-%d')}, is_select=False)
                    st.session_state.credito_atualizado = True
                    registrar_feedback_operacao(
                        f"Débito de R$ {valor_mov:.2f} registrado para {cliente_nome.upper()}."
                    )
                    st.rerun()
                else:
                    st.error(f"❌ Saldo insuficiente para {cliente_nome.upper()}. Saldo atual: R$ {saldo_atual:.2f}")
            else:
                st.warning("Preencha o nome do cliente e informe um valor positivo.")

    st.divider()

    # --- Exibição de saldos (cards) ---
    if df_creds.empty:
        st.info("📭 Ainda não há movimentações de crédito registradas. Use o formulário acima para lançar a primeira.")
    else:
        # Calcular saldo por cliente
        df_saldo = df_creds.groupby('cliente')['valor'].sum().reset_index()
        df_saldo = df_saldo[df_saldo['valor'] != 0].sort_values('valor', ascending=False)

        st.markdown("#### 👥 Saldo por cliente")
        # Usar 3 colunas para os cards
        cols = st.columns(3)
        for idx, (_, row) in enumerate(df_saldo.iterrows()):
            with cols[idx % 3]:
                saldo = row['valor']
                cor = "#28a745" if saldo > 0 else "#dc3545"
                st.markdown(f"""
                <div style="background-color:#f8f9fa; border-radius:12px; padding:0.8rem; margin-bottom:0.8rem; text-align:center;">
                    <h4 style="margin:0;">{row['cliente']}</h4>
                    <p style="font-size:1.8rem; font-weight:bold; color:{cor}; margin:0;">R$ {saldo:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # --- Tabela de movimentações recentes ---
        st.markdown("#### 📋 Histórico de movimentações")
        df_hist = df_creds.copy()
        df_hist['data_fmt'] = pd.to_datetime(df_hist['data']).dt.strftime('%d/%m/%Y')
        df_hist['tipo'] = df_hist['valor'].apply(lambda x: "➕ Crédito" if x > 0 else "🔻 Débito")
        df_hist['valor_abs'] = df_hist['valor'].abs()
        df_hist = df_hist.sort_values('data', ascending=False)

        # Exibir apenas as 20 últimas
        df_display = df_hist[['data_fmt', 'cliente', 'tipo', 'valor_abs']].head(20)
        df_display = df_display.rename(columns={
            'data_fmt': 'Data',
            'cliente': 'Cliente',
            'tipo': 'Tipo',
            'valor_abs': 'Valor'
        })
        df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {x:,.2f}")

        exibir_tabela_responsiva(
            df_display,
            colunas_sem_quebra=["Data", "Valor"],
        )

with tab5:
    st.markdown("### 🧾 Gestão de despesas")
    st.caption("Cadastre categorias de gastos, registre despesas e acompanhe o resumo financeiro do período.")

    tipo_map = {
        int(row["id"]): row["nome"]
        for _, row in df_expense_types.iterrows()
    } if not df_expense_types.empty else {}

    col_tipo, col_lancamento = st.columns([1, 2])
    with col_tipo:
        st.markdown("#### Tipos de despesa")
        with st.form("form_tipo_despesa", clear_on_submit=True):
            novo_tipo = st.text_input("Novo tipo", placeholder="Ex: Papel, Energia, Limpeza", key="novo_tipo_despesa")
            adicionar_tipo = st.form_submit_button("Adicionar tipo", width="stretch")

        if adicionar_tipo:
            if novo_tipo.strip():
                if not nome_tipo_duplicado(df_expense_types, novo_tipo):
                    run_query("INSERT INTO tipos_despesa (username, nome) VALUES (:u, :n)",
                              {"u": st.session_state.username, "n": novo_tipo.strip().upper()}, is_select=False)
                    registrar_feedback_operacao("Tipo de despesa adicionado com sucesso.")
                    st.rerun()
                else:
                    st.warning("Esse tipo de despesa já está cadastrado.")
            else:
                st.warning("Informe um nome para o tipo de despesa.")
        if df_expense_types.empty:
            st.info("Cadastre pelo menos um tipo de despesa para começar os lançamentos.")
        else:
            exibir_tabela_responsiva(
                df_expense_types.rename(columns={"nome": "Tipo"})[["Tipo"]]
            )
            st.markdown("##### Editar ou excluir")
            if st.session_state.pop("limpar_tipo_gerenciar", False):
                st.session_state.pop("tipo_despesa_gerenciar", None)

            tipo_id_selecionado = st.selectbox(
                "Selecione um tipo",
                options=list(tipo_map.keys()),
                format_func=lambda tipo_id: tipo_map[tipo_id],
                index=None,
                placeholder="Escolha um tipo de despesa",
                key="tipo_despesa_gerenciar",
            )

            if tipo_id_selecionado is not None:
                with st.form(f"form_gerenciar_tipo_{tipo_id_selecionado}"):
                    nome_tipo_editado = st.text_input(
                        "Nome do tipo",
                        value=tipo_map[tipo_id_selecionado],
                    )
                    confirmar_exclusao_tipo = st.checkbox(
                        "Confirmo que desejo excluir este tipo."
                    )
                    col_salvar_tipo, col_excluir_tipo = st.columns(2)
                    with col_salvar_tipo:
                        salvar_tipo = st.form_submit_button(
                            "Salvar tipo",
                            width="stretch",
                            type="primary",
                        )
                    with col_excluir_tipo:
                        excluir_tipo = st.form_submit_button(
                            "Excluir tipo",
                            width="stretch",
                        )

                if salvar_tipo:
                    if not nome_tipo_editado.strip():
                        st.warning("Informe um nome para o tipo de despesa.")
                    elif nome_tipo_duplicado(
                        df_expense_types,
                        nome_tipo_editado,
                        tipo_id_selecionado,
                    ):
                        st.warning("Já existe outro tipo de despesa com esse nome.")
                    else:
                        run_query(
                            "UPDATE tipos_despesa SET nome=:n WHERE id=:id AND username=:u",
                            {
                                "n": nome_tipo_editado.strip().upper(),
                                "id": tipo_id_selecionado,
                                "u": st.session_state.username,
                            },
                            is_select=False,
                        )
                        st.session_state["limpar_tipo_gerenciar"] = True
                        registrar_feedback_operacao("Tipo de despesa atualizado com sucesso.")
                        st.rerun()

                if excluir_tipo:
                    despesas_vinculadas = contar_despesas_tipo(
                        df_expenses,
                        tipo_id_selecionado,
                    )
                    if despesas_vinculadas > 0:
                        st.warning(
                            f"Este tipo possui {despesas_vinculadas} despesa(s) vinculada(s). "
                            "Reclassifique esses registros antes de excluir."
                        )
                    elif not confirmar_exclusao_tipo:
                        st.warning("Marque a confirmação para excluir o tipo de despesa.")
                    else:
                        run_query(
                            "DELETE FROM tipos_despesa WHERE id=:id AND username=:u",
                            {
                                "id": tipo_id_selecionado,
                                "u": st.session_state.username,
                            },
                            is_select=False,
                        )
                        st.session_state["limpar_tipo_gerenciar"] = True
                        registrar_feedback_operacao("Tipo de despesa excluído com sucesso.")
                        st.rerun()

    with col_lancamento:
        st.markdown("#### Registrar despesa")
        if df_expense_types.empty:
            st.warning("Primeiro cadastre um tipo de despesa ao lado.")
        else:
            with st.form("form_nova_despesa", clear_on_submit=True):
                data_despesa = st.date_input("Data da despesa", value=hoje, format="DD/MM/YYYY", key="data_despesa")
                tipo_id_despesa = st.selectbox(
                    "Tipo de despesa",
                    options=list(tipo_map.keys()),
                    format_func=lambda tipo_id: tipo_map[tipo_id],
                    key="tipo_despesa",
                )
                desc_despesa = st.text_input("Descrição", placeholder="Ex: Compra de resma A4, reposição de tinta", key="desc_despesa")
                valor_despesa = st.number_input("Valor da despesa (R$)", min_value=0.0, step=1.0, value=None, format="%.2f", key="valor_despesa")
                salvar_despesa = st.form_submit_button(
                    "Salvar despesa",
                    width="stretch",
                    type="primary",
                )

            if salvar_despesa:
                if valor_despesa is not None and valor_despesa > 0:
                    run_query("""INSERT INTO despesas (username, data, tipo_id, descricao, valor)
                                 VALUES (:u, :d, :t, :de, :v)""",
                              {"u": st.session_state.username, "d": data_despesa.strftime('%Y-%m-%d'),
                               "t": tipo_id_despesa, "de": desc_despesa, "v": valor_despesa},
                              is_select=False)
                    registrar_feedback_operacao("Despesa registrada com sucesso.")
                    st.rerun()
                else:
                    st.warning("Informe um valor positivo para a despesa.")

    st.divider()
    st.markdown("#### Resumo de despesas por período")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        data_inicio_desp = st.date_input("Data inicial", value=inicio_mes, format="DD/MM/YYYY", key="desp_inicio")
    with col_d2:
        data_fim_desp = st.date_input("Data final", value=hoje, format="DD/MM/YYYY", key="desp_fim")

    if data_inicio_desp > data_fim_desp:
        st.warning("A data inicial não pode ser maior que a data final.")
    elif df_expenses.empty:
        st.info("Ainda não há despesas registradas para exibir.")
    else:
        df_expenses['data_dt'] = pd.to_datetime(df_expenses['data'])
        df_expenses_periodo = df_expenses[
            (df_expenses['data_dt'].dt.date >= data_inicio_desp) &
            (df_expenses['data_dt'].dt.date <= data_fim_desp)
        ].copy()
        if df_expenses_periodo.empty:
            st.info("Nenhuma despesa foi encontrada nesse período.")
        else:
            total_desp = df_expenses_periodo['valor'].sum()
            st.metric("Total de despesas no período", f"R$ {total_desp:,.2f}")
            df_tipo_desp = df_expenses_periodo.groupby('tipo_nome')['valor'].sum().reset_index().sort_values('valor', ascending=False)
            fig_desp = px.bar(
                df_tipo_desp,
                x='tipo_nome',
                y='valor',
                text='valor',
                title="Despesas por tipo",
                labels={'tipo_nome': 'Tipo', 'valor': 'Valor (R$)'},
                color_discrete_sequence=['#fda4af']
            )

            fig_desp.update_traces(
                texttemplate='R$ %{y:,.2f}',
                textposition='outside',
                cliponaxis=False
            )
            fig_desp.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=60, b=10))
            estilizar_grafico(fig_desp)
            st.plotly_chart(fig_desp, width="stretch", config=CONFIG_GRAFICO_ESTATICO)
            df_expenses_periodo['Data'] = df_expenses_periodo['data_dt'].dt.strftime('%d/%m/%Y')
            df_expenses_periodo['Tipo'] = df_expenses_periodo['tipo_nome']
            df_expenses_periodo['Descrição'] = df_expenses_periodo['descricao']
            df_expenses_periodo['Valor'] = df_expenses_periodo['valor'].apply(lambda x: f"R$ {x:,.2f}")
            exibir_tabela_responsiva(
                df_expenses_periodo[['Data', 'Tipo', 'Descrição', 'Valor']],
                colunas_sem_quebra=["Data", "Valor"],
            )

            st.markdown("#### Gerenciar registros")
            st.caption("Selecione uma despesa para editar, reclassificar ou excluir.")

            despesa_map = {
                int(row["id"]): (
                    f"{pd.to_datetime(row['data']).strftime('%d/%m/%Y')} | "
                    f"{row['tipo_nome'] if pd.notna(row['tipo_nome']) else 'SEM TIPO'} | "
                    f"R$ {float(row['valor']):,.2f}"
                )
                for _, row in df_expenses_periodo.sort_values(
                    "data_dt",
                    ascending=False,
                ).iterrows()
                if pd.notna(row.get("id"))
            }

            if not despesa_map:
                st.warning("Os registros encontrados não possuem identificação para edição.")
            else:
                if st.session_state.pop("limpar_despesa_gerenciar", False):
                    st.session_state.pop("despesa_gerenciar", None)

                despesa_id = st.selectbox(
                    "Selecione uma despesa",
                    options=list(despesa_map.keys()),
                    format_func=lambda registro_id: despesa_map[registro_id],
                    index=None,
                    placeholder="Escolha um registro",
                    key="despesa_gerenciar",
                )

                if despesa_id is not None and not tipo_map:
                    st.warning(
                        "Cadastre um tipo de despesa antes de editar este registro."
                    )

                if despesa_id is not None and tipo_map:
                    despesa_row = df_expenses_periodo[
                        df_expenses_periodo["id"] == despesa_id
                    ].iloc[0]
                    tipo_atual = (
                        int(despesa_row["tipo_id"])
                        if pd.notna(despesa_row["tipo_id"])
                        else None
                    )
                    tipo_ids = list(tipo_map.keys())
                    indice_tipo = (
                        tipo_ids.index(tipo_atual)
                        if tipo_atual in tipo_ids
                        else 0
                    )

                    with st.form(f"form_gerenciar_despesa_{despesa_id}"):
                        data_despesa_editada = st.date_input(
                            "Data",
                            value=pd.to_datetime(despesa_row["data"]).date(),
                            format="DD/MM/YYYY",
                        )
                        tipo_despesa_editado = st.selectbox(
                            "Tipo de despesa",
                            options=tipo_ids,
                            format_func=lambda tipo_id: tipo_map[tipo_id],
                            index=indice_tipo,
                        )
                        descricao_despesa_editada = st.text_input(
                            "Descrição",
                            value=(
                                ""
                                if pd.isna(despesa_row["descricao"])
                                else str(despesa_row["descricao"])
                            ),
                        )
                        valor_despesa_editado = st.number_input(
                            "Valor (R$)",
                            min_value=0.0,
                            step=1.0,
                            value=float(despesa_row["valor"]),
                            format="%.2f",
                        )
                        confirmar_exclusao_despesa = st.checkbox(
                            "Confirmo que desejo excluir esta despesa."
                        )
                        col_salvar_despesa, col_excluir_despesa = st.columns(2)
                        with col_salvar_despesa:
                            salvar_despesa_editada = st.form_submit_button(
                                "Salvar alterações",
                                width="stretch",
                                type="primary",
                            )
                        with col_excluir_despesa:
                            excluir_despesa = st.form_submit_button(
                                "Excluir despesa",
                                width="stretch",
                            )

                    if salvar_despesa_editada:
                        if valor_despesa_editado <= 0:
                            st.warning("Informe um valor positivo para a despesa.")
                        else:
                            run_query(
                                """UPDATE despesas SET data=:d, tipo_id=:t, descricao=:de, valor=:v
                                   WHERE id=:id AND username=:u""",
                                {
                                    "d": data_despesa_editada.strftime('%Y-%m-%d'),
                                    "t": tipo_despesa_editado,
                                    "de": descricao_despesa_editada,
                                    "v": valor_despesa_editado,
                                    "id": despesa_id,
                                    "u": st.session_state.username,
                                },
                                is_select=False,
                            )
                            st.session_state["limpar_despesa_gerenciar"] = True
                            registrar_feedback_operacao("Despesa atualizada com sucesso.")
                            st.rerun()

                    if excluir_despesa:
                        if not confirmar_exclusao_despesa:
                            st.warning("Marque a confirmação para excluir a despesa.")
                        else:
                            run_query(
                                "DELETE FROM despesas WHERE id=:id AND username=:u",
                                {
                                    "id": despesa_id,
                                    "u": st.session_state.username,
                                },
                                is_select=False,
                            )
                            st.session_state["limpar_despesa_gerenciar"] = True
                            registrar_feedback_operacao("Despesa excluída com sucesso.")
                            st.rerun()
