import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
import re
import jwt  # pyright: ignore[reportMissingImports]
from typing import Optional

# --- CONFIGURAÃ‡ÃƒO JWT ---
JWT_SECRET = st.secrets["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_DAYS = 30

# --- CONFIGURAÃ‡ÃƒO GERAL ---
URL_ICONE = "https://preview.redd.it/53zg1z70jxzg1.jpeg?width=640&crop=smart&auto=webp&s=57ad5ec9bee948b825fe8e208f951f6ffd2739ee"
LISTA_SERVICOS = [
    "ðŸ“„ XÃ©rox",
    "ðŸ–¨ï¸ ImpressÃ£o em Papel Comum",
    "ðŸ–¨ï¸ ImpressÃ£o em Papel FotogrÃ¡fico",
    "ðŸ–¨ï¸ ImpressÃ£o em Papel Adesivo",
    "ðŸ–¨ï¸ ImpressÃ£o em Papel de Diploma",
    "ðŸ“¸ Foto 3x4",
    "ðŸ“ CurrÃ­culo",
    "ðŸƒ´ Venda de Figurinhas",
    "ðŸž PÃ£o",
    "ðŸŽ¬ ServiÃ§os de EdiÃ§Ã£o",
    "ðŸ›¡ï¸ PlastificaÃ§Ã£o",
    "âš™ï¸ Outros"
]

def aplicar_estilo_customizado():
    st.markdown(f"""
    <style>
    /* Fundo principal branco */
    .stApp, .stMain, .stHeader, .stAppHeader, .block-container, [data-testid=\"stTabContent\"] {{
        background: linear-gradient(180deg, #fffdfd 0%, #fff8fb 100%) !important;
        color: #1f2937 !important;
    }}
    /* ForÃ§ar cor preta em textos e labels */
    html, body, [class*=\"st-b\"] {{ color: #1f2937 !important; }}
    .stMarkdown, .stText, [data-testid=\"stMetricValue\"], label, h1, h2, h3, p, span,
    [data-testid=\"stWidgetLabel\"] p, table, th, td, [data-testid=\"stTable\"] td,
    .stDataFrame, [data-testid=\"stMetricLabel\"] p {{
        color: #1f2937 !important;
    }}
    /* Fix para CalendÃ¡rio e Selectbox */
    div[data-baseweb=\"calendar\"] *, div[data-baseweb=\"popover\"] *,
    div[data-baseweb=\"select\"] *, .stSelectbox div[role=\"button\"] {{
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }}
    /* Estilo dos campos de entrada */
    input, textarea {{ color: #1f2937 !important; background-color: rgba(255, 255, 255, 0.96) !important; border-radius: 12px !important; }}
    div[data-baseweb=\"select\"] > div {{ background-color: #ffffff !important; border-radius: 12px !important; }}
    /* BotÃµes */
    button[data-testid=\"baseButton-secondary\"], .stButton > button {{
        background-color: #ffe4ef !important; color: #1f2937 !important; border-radius: 14px !important;
        width: 100% !important; border: 1px solid #f9a8d4 !important; font-weight: 600 !important; min-height: 2.8rem !important;
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
    @media (max-width: 768px) {{ .block-container {{ padding-top: 1rem !important; }} .bg-image {{ width: 92vw !important; opacity: 0.05 !important; }} }}
    </style>
    <div class='main-bg-container'><img src='{URL_ICONE}' class='bg-image'></div>
    """, unsafe_allow_html=True)

def aplicar_comportamento_inputs():
    components.html(
        """
        <script>
        const setupNumericFocus = () => {
          const inputs = window.parent.document.querySelectorAll('input[type="number"]');
          inputs.forEach((input) => {
            if (input.dataset.autoSelectReady === "1") return;
            input.dataset.autoSelectReady = "1";
            input.addEventListener('focus', () => {
              requestAnimationFrame(() => input.select());
            });
            input.addEventListener('mouseup', (event) => {
              event.preventDefault();
            });
          });
        };
        setupNumericFocus();
        const observer = new MutationObserver(setupNumericFocus);
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
        </script>
        """,
        height=0,
    )

st.set_page_config(page_title="GestÃ£o de ServiÃ§os Pro", layout="wide")
aplicar_estilo_customizado()
aplicar_comportamento_inputs()

# --- CONEXÃƒO EXCLUSIVA COM SUPABASE ---
@st.cache_resource
def get_connection():
    """Retorna a conexÃ£o com o Supabase via st.connection."""
    try:
        return st.connection("postgresql", type="sql")
    except Exception as e:
        st.error(f"âŒ Erro ao conectar ao Supabase: {e}")
        st.error("Verifique se as secrets do Streamlit estÃ£o configuradas corretamente.")
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
    """Cria as tabelas necessÃ¡rias no Supabase e adiciona a coluna 'id' se necessÃ¡rio."""
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

    # Adicionar coluna 'id' na tabela 'servicos' se nÃ£o existir
    try:
        run_query("SELECT id FROM servicos LIMIT 0", is_select=True)
    except Exception:
        run_query("ALTER TABLE servicos ADD COLUMN id SERIAL PRIMARY KEY", is_select=False)
        st.info("âœ… Coluna 'id' adicionada Ã  tabela 'servicos'.")

init_db()

# --- FUNÃ‡Ã•ES DE AUTENTICAÃ‡ÃƒO COM JWT ---
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

# --- TENTAR RESTAURAR SESSÃƒO AO CARREGAR ---
if not st.session_state.logged_in:
    if restaurar_sessao():
        st.rerun()

# --- TELA DE LOGIN ---
if not st.session_state.logged_in:
    st.markdown("""
    <div class='login-card'>
        <h1 style='text-align: center;'>Acesse sua conta</h1>
        <p style='text-align: center;'>Entre para registrar serviÃ§os, acompanhar resultados e controlar crÃ©ditos.</p>
    </div>
    """, unsafe_allow_html=True)
    _, col_center, _ = st.columns([1, 2, 1])
    with col_center:
        user = st.text_input("UsuÃ¡rio", key="login_user", placeholder="Digite seu usuÃ¡rio")
        pw = st.text_input("Senha", type="password", key="login_pw", placeholder="Digite sua senha")
        remember = st.checkbox("ðŸ” Lembrar meu login por 30 dias", value=False)

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
                            st.success("âœ… Login concluÃ­do com acesso automÃ¡tico ativo por 30 dias.")
                        else:
                            st.warning("âš ï¸ O login foi concluÃ­do, mas nÃ£o foi possÃ­vel ativar o acesso automÃ¡tico.")
                    else:
                        st.query_params.clear()
                        st.session_state.token_remember = None

                    st.rerun()
                else:
                    st.error("UsuÃ¡rio ou senha invÃ¡lidos. Verifique os dados e tente novamente.")
            else:
                st.warning("Informe seu usuÃ¡rio para continuar.")

        if st.button("Criar conta"):
            if user and pw:
                check = run_query("SELECT username FROM usuarios WHERE username = :u", {"u": user})
                if check.empty:
                    run_query("INSERT INTO usuarios (username, password) VALUES (:u, :p)",
                              {"u": user, "p": pw}, is_select=False)
                    st.success("Conta criada com sucesso. Agora faÃ§a seu login.")
                else:
                    st.error("Esse usuÃ¡rio jÃ¡ estÃ¡ cadastrado.")
            else:
                st.warning("Preencha usuÃ¡rio e senha para criar sua conta.")
    st.stop()

# --- ÃREA DO PAINEL ---
st.markdown("""
<div class='hero-card'>
    <h1 style='text-align: center;'>Painel Financeiro</h1>
    <p style='text-align: center;'>Acompanhe seus registros, resultados do perÃ­odo e crÃ©ditos de clientes em um sÃ³ lugar.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([9, 1])
with col2:
    if st.button("ðŸšª Sair"):
        logout_completo()

df_full = run_query("SELECT * FROM servicos WHERE username=:u", {"u": st.session_state.username})
df_creds = run_query("SELECT * FROM creditos WHERE username=:u", {"u": st.session_state.username})
df_expenses = run_query("""SELECT d.*, t.nome AS tipo_nome
                           FROM despesas d
                           LEFT JOIN tipos_despesa t ON d.tipo_id = t.id
                           WHERE d.username=:u""", {"u": st.session_state.username})
df_expense_types = run_query("SELECT * FROM tipos_despesa WHERE username=:u ORDER BY nome", {"u": st.session_state.username})

hoje = datetime.now().date()
inicio_mes = hoje.replace(day=1)

if not df_full.empty:
    df_full['data_dt'] = pd.to_datetime(df_full['data'])
    fat_dia = df_full[df_full['data_dt'].dt.date == hoje]['valor'].sum()
    fat_mes = df_full[df_full['data_dt'].dt.date >= inicio_mes]['valor'].sum()
    m1, m2 = st.columns(2)
    m1.metric("Faturamento Hoje", f"R$ {fat_dia:,.2f}")
    m2.metric("Faturamento MÃªs", f"R$ {fat_mes:,.2f}")
else:
    st.info("Comece cadastrando seu primeiro serviÃ§o para acompanhar o faturamento do dia e do mÃªs.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["âž• Novo serviÃ§o", "ðŸ“Š HistÃ³rico", "ðŸ“ˆ AnÃ¡lises", "ðŸ’³ CrÃ©ditos", "ðŸ§¾ Despesas"])

with tab1:
    st.markdown("### Novo serviÃ§o")
    st.caption("Registre rapidamente um atendimento ou venda realizada hoje.")
    data_serv = st.date_input("Data", value=hoje, format="DD/MM/YYYY")
    cat_serv = st.selectbox("Tipo", LISTA_SERVICOS)
    desc_serv = st.text_input("Detalhes", placeholder="Ex: 20 cÃ³pias coloridas, currÃ­culo, plastificaÃ§Ã£o...")
    valor_serv = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
    if st.button("Salvar serviÃ§o"):
        run_query("INSERT INTO servicos (username, data, categoria, descricao, valor) VALUES (:u, :d, :c, :de, :v)",
                  {"u": st.session_state.username, "d": data_serv.strftime('%Y-%m-%d'),
                   "c": cat_serv, "de": desc_serv, "v": valor_serv}, is_select=False)
        st.success("ServiÃ§o salvo com sucesso.")
        st.rerun()

with tab2:
    st.markdown("### HistÃ³rico de serviÃ§os")
    st.caption("Consulte, ajuste ou exclua registros jÃ¡ lanÃ§ados.")

    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        data_inicio = st.date_input("Data Inicial", value=inicio_mes, format="DD/MM/YYYY")
    with col_filtro2:
        data_fim = st.date_input("Data Final", value=hoje, format="DD/MM/YYYY")

    if data_inicio > data_fim:
        st.warning("A data inicial nÃ£o pode ser maior que a data final.")
    else:
        df_full['data_dt'] = pd.to_datetime(df_full['data'])
        df_filtrado = df_full[
            (df_full['data_dt'].dt.date >= data_inicio) &
            (df_full['data_dt'].dt.date <= data_fim)
        ].sort_values('data_dt', ascending=False)

        if df_filtrado.empty:
            st.info("Nenhum serviÃ§o foi encontrado nesse perÃ­odo. Ajuste os filtros ou registre um novo serviÃ§o.")
        else:
            df_sheet = df_filtrado.copy()
            df_sheet['Data'] = df_sheet['data_dt'].dt.strftime('%d/%m/%Y')
            df_sheet['Tipo'] = df_sheet['categoria']
            df_sheet['Detalhes'] = df_sheet['descricao']
            df_sheet['Valor'] = df_sheet['valor'].apply(lambda x: f"R$ {x:,.2f}")
            st.markdown("<div class='sheet-card'>", unsafe_allow_html=True)
            st.dataframe(df_sheet[['Data', 'Tipo', 'Detalhes', 'Valor']], use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
            opcoes_servico = {
                f"{pd.to_datetime(row['data']).strftime('%d/%m/%Y')} | {row['categoria']} | R$ {float(row['valor']):,.2f}": int(row['id'])
                for _, row in df_filtrado.iterrows() if pd.notna(row.get('id'))
            }
            if not opcoes_servico:
                st.warning("Os registros encontrados nÃ£o tÃªm identificaÃ§Ã£o suficiente para ediÃ§Ã£o.")
            else:
                servico_label = st.selectbox("Selecione um registro para editar ou excluir", list(opcoes_servico.keys()))
                id_servico = opcoes_servico[servico_label]
                row = df_filtrado[df_filtrado['id'] == id_servico].iloc[0]
                categoria = row['categoria']
                descricao = row['descricao']
                valor = row['valor']
                nova_data = st.date_input("Data", value=pd.to_datetime(row['data']).date(), format="DD/MM/YYYY", key=f"data_{id_servico}")

                try:
                    indice_categoria = LISTA_SERVICOS.index(categoria)
                except ValueError:
                    indice_categoria = 0
                    st.warning(f"âš ï¸ A categoria original '{categoria}' nÃ£o estÃ¡ mais disponÃ­vel. Escolha a opÃ§Ã£o correta abaixo.")

                nova_cat = st.selectbox("Tipo", LISTA_SERVICOS, index=indice_categoria, key=f"cat_{id_servico}")
                nova_desc = st.text_input("Detalhes", value=descricao, key=f"desc_{id_servico}")
                novo_valor = st.number_input("Valor (R$)", min_value=0.0, step=1.0, value=float(valor), format="%.2f", key=f"valor_{id_servico}")

                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("ðŸ’¾ Salvar alteraÃ§Ãµes", key=f"salvar_{id_servico}"):
                        run_query("""UPDATE servicos SET data=:d, categoria=:c, descricao=:de, valor=:v
                                    WHERE id=:id AND username=:u""",
                                  {"d": nova_data.strftime('%Y-%m-%d'), "c": nova_cat, "de": nova_desc,
                                   "v": novo_valor, "id": id_servico, "u": st.session_state.username},
                                  is_select=False)
                        st.success("AlteraÃ§Ãµes salvas com sucesso.")
                        st.rerun()
                with col_del:
                    if st.button("ðŸ—‘ï¸ Excluir serviÃ§o", key=f"excluir_{id_servico}"):
                        st.markdown("<div class='danger-card'><strong>Confirme a exclusÃ£o.</strong><br>Essa aÃ§Ã£o remove o registro permanentemente.</div>", unsafe_allow_html=True)
                        confirmar = st.checkbox("Confirmo que desejo excluir este serviÃ§o.", key=f"conf_{id_servico}")
                        if confirmar:
                            run_query("DELETE FROM servicos WHERE id=:id AND username=:u",
                                      {"id": id_servico, "u": st.session_state.username}, is_select=False)
                            st.success("ServiÃ§o excluÃ­do com sucesso.")
                            st.rerun()

with tab3:
    st.markdown("### ðŸ“Š AnÃ¡lise de faturamento")
    st.caption("Use os filtros para visualizar o desempenho por categoria e por semana.")

    # --- Filtro de perÃ­odo para os grÃ¡ficos ---
    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        data_inicio_graf = st.date_input("PerÃ­odo - Data Inicial", value=inicio_mes, format="DD/MM/YYYY", key="graf_inicio")
    with col_filtro2:
        data_fim_graf = st.date_input("PerÃ­odo - Data Final", value=hoje, format="DD/MM/YYYY", key="graf_fim")

    if data_inicio_graf > data_fim_graf:
        st.warning("Data inicial nÃ£o pode ser maior que a data final.")
    else:
        # Filtrar o DataFrame principal pelo perÃ­odo escolhido
        df_periodo = df_full[
            (df_full['data_dt'].dt.date >= data_inicio_graf) &
            (df_full['data_dt'].dt.date <= data_fim_graf)
        ].copy()

        if df_periodo.empty:
            st.info("Ainda nÃ£o hÃ¡ dados nesse perÃ­odo. Ajuste os filtros ou registre novos serviÃ§os para visualizar os grÃ¡ficos.")
        else:
            # Total do perÃ­odo
            total_periodo = df_periodo['valor'].sum()
            st.metric("ðŸ’° Faturamento Total no PerÃ­odo", f"R$ {total_periodo:,.2f}")
            st.divider()

            # --- GrÃ¡fico 1: Faturamento por Categoria ---
            st.markdown("### Faturamento por categoria")
            df_rank = df_periodo.groupby('categoria')['valor'].sum().reset_index().sort_values('valor', ascending=False)
            fig_rank = px.bar(df_rank, x='categoria', y='valor',
                             title="ServiÃ§os com maior faturamento no perÃ­odo",
                             labels={'categoria': 'Tipo de ServiÃ§o', 'valor': 'Valor (R$)'},
                             color_discrete_sequence=['#ffc4d8'])
            fig_rank.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=60, b=10))
            st.plotly_chart(fig_rank, use_container_width=True)

            st.divider()

            # --- GrÃ¡fico 2: Faturamento Semanal (baseado no perÃ­odo filtrado) ---
            st.markdown("### Faturamento semanal")

            # Garantir que os dados estÃ£o ordenados por data
            df_periodo_semana = df_periodo.sort_values('data_dt')

            # Calcular a semana (segunda a domingo) para cada registro
            df_periodo_semana['segunda'] = df_periodo_semana['data_dt'] - df_periodo_semana['data_dt'].dt.weekday.map(lambda x: timedelta(days=x))
            df_periodo_semana['domingo'] = df_periodo_semana['segunda'] + timedelta(days=6)
            df_periodo_semana['periodo'] = df_periodo_semana['segunda'].dt.strftime('%d/%m') + " a " + df_periodo_semana['domingo'].dt.strftime('%d/%m')

            df_semana = df_periodo_semana.groupby(['segunda', 'periodo'])['valor'].sum().reset_index().sort_values('segunda')

            if df_semana.empty:
                st.info("NÃ£o hÃ¡ dados suficientes para montar o grÃ¡fico semanal nesse perÃ­odo.")
            else:
                fig_semanal = px.bar(df_semana, x='periodo', y='valor',
                                    title="EvoluÃ§Ã£o semanal do faturamento",
                                    labels={'periodo': 'Semana', 'valor': 'Valor (R$)'},
                                    color_discrete_sequence=['#ffc4d8'])
                fig_semanal.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=60, b=10))
                st.plotly_chart(fig_semanal, use_container_width=True)

with tab4:
    st.markdown("### ðŸ’³ GestÃ£o de crÃ©ditos")
    st.caption("Acompanhe o saldo dos clientes e registre entradas ou dÃ©bitos com facilidade.")

    # Inicializar estados de controle
    if "credito_atualizado" not in st.session_state:
        st.session_state.credito_atualizado = False

    # Recarregar dados se necessÃ¡rio
    if st.session_state.credito_atualizado:
        df_creds = run_query("SELECT * FROM creditos WHERE username=:u", {"u": st.session_state.username})
        st.session_state.credito_atualizado = False

    # --- FormulÃ¡rio de movimentaÃ§Ã£o (estilo card) ---
    with st.container(border=True):
        st.markdown("#### Registrar crÃ©dito ou dÃ©bito")
        col1, col2 = st.columns([2, 1])
        with col1:
            cliente_nome = st.text_input("Nome do Cliente", key="cliente_cred", placeholder="Ex: JoÃ£o Silva")
        with col2:
            valor_mov = st.number_input("Valor (R$)", min_value=0.0, step=0.5, format="%.2f", key="valor_cred")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("âž• Adicionar CrÃ©dito", use_container_width=True, type="primary"):
                if cliente_nome and valor_mov > 0:
                    run_query("INSERT INTO creditos (username, cliente, valor, data) VALUES (:u, :cl, :v, :d)",
                              {"u": st.session_state.username, "cl": cliente_nome.upper(), "v": valor_mov,
                               "d": hoje.strftime('%Y-%m-%d')}, is_select=False)
                    st.session_state.credito_atualizado = True
                    st.success(f"âœ… CrÃ©dito de R$ {valor_mov:.2f} registrado para {cliente_nome.upper()}.")
                    st.balloons()
                    st.rerun()
                else:
                    st.warning("Preencha o nome do cliente e informe um valor positivo.")

        with col_btn2:
            if st.button("ðŸ”» Usar CrÃ©dito", use_container_width=True):
                if cliente_nome and valor_mov > 0:
                    # Verificar se cliente tem saldo suficiente
                    saldo_atual = df_creds[df_creds['cliente'] == cliente_nome.upper()]['valor'].sum() if not df_creds.empty else 0
                    if saldo_atual >= valor_mov:
                        run_query("INSERT INTO creditos (username, cliente, valor, data) VALUES (:u, :cl, :v, :d)",
                                  {"u": st.session_state.username, "cl": cliente_nome.upper(), "v": -valor_mov,
                                   "d": hoje.strftime('%Y-%m-%d')}, is_select=False)
                        st.session_state.credito_atualizado = True
                        st.success(f"âœ… DÃ©bito de R$ {valor_mov:.2f} registrado para {cliente_nome.upper()}.")
                        st.rerun()
                    else:
                        st.error(f"âŒ Saldo insuficiente para {cliente_nome.upper()}. Saldo atual: R$ {saldo_atual:.2f}")
                else:
                    st.warning("Preencha o nome do cliente e informe um valor positivo.")

    st.divider()

    # --- ExibiÃ§Ã£o de saldos (cards) ---
    if df_creds.empty:
        st.info("ðŸ“­ Ainda nÃ£o hÃ¡ movimentaÃ§Ãµes de crÃ©dito registradas. Use o formulÃ¡rio acima para lanÃ§ar a primeira.")
    else:
        # Calcular saldo por cliente
        df_saldo = df_creds.groupby('cliente')['valor'].sum().reset_index()
        df_saldo = df_saldo[df_saldo['valor'] != 0].sort_values('valor', ascending=False)

        st.markdown("#### ðŸ‘¥ Saldo por cliente")
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

        # --- Tabela de movimentaÃ§Ãµes recentes ---
        st.markdown("#### ðŸ“‹ HistÃ³rico de movimentaÃ§Ãµes")
        df_hist = df_creds.copy()
        df_hist['data_fmt'] = pd.to_datetime(df_hist['data']).dt.strftime('%d/%m/%Y')
        df_hist['tipo'] = df_hist['valor'].apply(lambda x: "âž• CrÃ©dito" if x > 0 else "ðŸ”» DÃ©bito")
        df_hist['valor_abs'] = df_hist['valor'].abs()
        df_hist = df_hist.sort_values('data', ascending=False)

        # Exibir apenas as 20 Ãºltimas
        df_display = df_hist[['data_fmt', 'cliente', 'tipo', 'valor_abs']].head(20)
        df_display = df_display.rename(columns={
            'data_fmt': 'Data',
            'cliente': 'Cliente',
            'tipo': 'Tipo',
            'valor_abs': 'Valor'
        })
        df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {x:,.2f}")

        st.dataframe(df_display, use_container_width=True, hide_index=True)

with tab5:
    st.markdown("### ðŸ§¾ GestÃ£o de despesas")
    st.caption("Cadastre categorias de gastos, registre despesas e acompanhe o resumo financeiro do perÃ­odo.")

    col_tipo, col_lancamento = st.columns([1, 2])
    with col_tipo:
        st.markdown("#### Tipos de despesa")
        novo_tipo = st.text_input("Novo tipo", placeholder="Ex: Papel, Energia, Limpeza", key="novo_tipo_despesa")
        if st.button("Adicionar tipo", use_container_width=True):
            if novo_tipo.strip():
                existente = df_expense_types[df_expense_types['nome'].str.upper() == novo_tipo.strip().upper()] if not df_expense_types.empty else pd.DataFrame()
                if existente.empty:
                    run_query("INSERT INTO tipos_despesa (username, nome) VALUES (:u, :n)",
                              {"u": st.session_state.username, "n": novo_tipo.strip().upper()}, is_select=False)
                    st.success("Tipo de despesa adicionado com sucesso.")
                    st.rerun()
                else:
                    st.warning("Esse tipo de despesa jÃ¡ estÃ¡ cadastrado.")
            else:
                st.warning("Informe um nome para o tipo de despesa.")
        if df_expense_types.empty:
            st.info("Cadastre pelo menos um tipo de despesa para comeÃ§ar os lanÃ§amentos.")
        else:
            st.dataframe(df_expense_types.rename(columns={"nome": "Tipo"})[["Tipo"]], use_container_width=True, hide_index=True)

    with col_lancamento:
        st.markdown("#### Registrar despesa")
        if df_expense_types.empty:
            st.warning("Primeiro cadastre um tipo de despesa ao lado.")
        else:
            data_despesa = st.date_input("Data da despesa", value=hoje, format="DD/MM/YYYY", key="data_despesa")
            tipo_map = {row['nome']: int(row['id']) for _, row in df_expense_types.iterrows()}
            tipo_nome = st.selectbox("Tipo de despesa", list(tipo_map.keys()), key="tipo_despesa")
            desc_despesa = st.text_input("DescriÃ§Ã£o", placeholder="Ex: Compra de resma A4, reposiÃ§Ã£o de tinta", key="desc_despesa")
            valor_despesa = st.number_input("Valor da despesa (R$)", min_value=0.0, step=1.0, format="%.2f", key="valor_despesa")
            if st.button("Salvar despesa", use_container_width=True, type="primary"):
                if valor_despesa > 0:
                    run_query("""INSERT INTO despesas (username, data, tipo_id, descricao, valor)
                                 VALUES (:u, :d, :t, :de, :v)""",
                              {"u": st.session_state.username, "d": data_despesa.strftime('%Y-%m-%d'),
                               "t": tipo_map[tipo_nome], "de": desc_despesa, "v": valor_despesa},
                              is_select=False)
                    st.success("Despesa registrada com sucesso.")
                    st.rerun()
                else:
                    st.warning("Informe um valor positivo para a despesa.")

    st.divider()
    st.markdown("#### Resumo de despesas por perÃ­odo")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        data_inicio_desp = st.date_input("Data inicial", value=inicio_mes, format="DD/MM/YYYY", key="desp_inicio")
    with col_d2:
        data_fim_desp = st.date_input("Data final", value=hoje, format="DD/MM/YYYY", key="desp_fim")

    if data_inicio_desp > data_fim_desp:
        st.warning("A data inicial nÃ£o pode ser maior que a data final.")
    elif df_expenses.empty:
        st.info("Ainda nÃ£o hÃ¡ despesas registradas para exibir.")
    else:
        df_expenses['data_dt'] = pd.to_datetime(df_expenses['data'])
        df_expenses_periodo = df_expenses[
            (df_expenses['data_dt'].dt.date >= data_inicio_desp) &
            (df_expenses['data_dt'].dt.date <= data_fim_desp)
        ].copy()
        if df_expenses_periodo.empty:
            st.info("Nenhuma despesa foi encontrada nesse perÃ­odo.")
        else:
            total_desp = df_expenses_periodo['valor'].sum()
            st.metric("Total de despesas no perÃ­odo", f"R$ {total_desp:,.2f}")
            df_tipo_desp = df_expenses_periodo.groupby('tipo_nome')['valor'].sum().reset_index().sort_values('valor', ascending=False)
            fig_desp = px.bar(df_tipo_desp, x='tipo_nome', y='valor',
                              title="Despesas por tipo",
                              labels={'tipo_nome': 'Tipo', 'valor': 'Valor (R$)'},
                              color_discrete_sequence=['#fda4af'])
            fig_desp.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=60, b=10))
            st.plotly_chart(fig_desp, use_container_width=True)
            df_expenses_periodo['Data'] = df_expenses_periodo['data_dt'].dt.strftime('%d/%m/%Y')
            df_expenses_periodo['Tipo'] = df_expenses_periodo['tipo_nome']
            df_expenses_periodo['DescriÃ§Ã£o'] = df_expenses_periodo['descricao']
            df_expenses_periodo['Valor'] = df_expenses_periodo['valor'].apply(lambda x: f"R$ {x:,.2f}")
            st.dataframe(df_expenses_periodo[['Data', 'Tipo', 'DescriÃ§Ã£o', 'Valor']], use_container_width=True, hide_index=True)
