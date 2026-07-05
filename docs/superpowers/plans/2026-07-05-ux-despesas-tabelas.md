# UX, Tabelas e Despesas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar gráficos e tabelas legíveis, limpar formulários após sucesso e permitir editar/excluir tipos e registros de despesas.

**Architecture:** Toda a implementação permanece em `app.py`. Helpers locais centralizam feedback, estilo de gráficos e renderização segura de tabelas; as operações de despesas reutilizam `run_query()` e as tabelas existentes, sempre filtrando por `username`.

**Tech Stack:** Python, Streamlit, Pandas, Plotly, SQLAlchemy/PostgreSQL.

---

### Task 1: Helpers visuais e feedback persistente

**Files:**
- Modify: `app.py:37-132`
- Test: comando Python com inspeção AST de `app.py`

- [ ] **Step 1: Escrever o teste falhando**

```python
from pathlib import Path

source = Path("app.py").read_text(encoding="utf-8")
assert "def exibir_feedback_operacao():" in source
assert "def estilizar_grafico(fig):" in source
assert "def exibir_tabela_responsiva(df, colunas_sem_quebra=None):" in source
assert "escape=True" in source
assert "font=dict(color="#111827")" in source
```

- [ ] **Step 2: Executar e confirmar RED**

Run: bloco acima via `python -`

Expected: FAIL porque os três helpers ainda não existem.

- [ ] **Step 3: Implementar os helpers mínimos**

```python
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
    html = df.to_html(index=False, escape=True, border=0, classes=["tabela-responsiva", tabela_id])
    st.markdown(f"<style>{regras}</style><div class='tabela-scroll'>{html}</div>", unsafe_allow_html=True)
```

Adicionar CSS para `.tabela-scroll`, `.tabela-responsiva`, células com quebra e `.sem-quebra`. Aplicar `exibir_feedback_operacao()` uma vez após a autenticação e antes dos cards.

- [ ] **Step 4: Aplicar o estilo aos três gráficos**

Após cada `update_layout` existente, chamar:

```python
estilizar_grafico(fig_rank)
estilizar_grafico(fig_semanal)
estilizar_grafico(fig_desp)
```

- [ ] **Step 5: Executar GREEN**

Run: teste do Step 1 e `python -m py_compile app.py`

Expected: PASS.

### Task 2: Formulários limpos e feedback de serviços/créditos

**Files:**
- Modify: `app.py:370-576`
- Test: comando Python com inspeção AST/textual de `app.py`

- [ ] **Step 1: Escrever o teste falhando**

```python
from pathlib import Path

source = Path("app.py").read_text(encoding="utf-8")
for key in ("form_novo_servico", "form_credito"):
    assert f'st.form("{key}", clear_on_submit=True)' in source
assert 'registrar_feedback_operacao("Serviço salvo com sucesso.")' in source
assert 'registrar_feedback_operacao("Alterações salvas com sucesso.")' in source
```

- [ ] **Step 2: Executar e confirmar RED**

Run: bloco acima via `python -`

Expected: FAIL porque os formulários atuais usam `st.button`.

- [ ] **Step 3: Converter cadastro de serviço**

Agrupar data, tipo, detalhes, valor e submit em:

```python
with st.form("form_novo_servico", clear_on_submit=True):
    data_serv = st.date_input("Data", value=hoje, format="DD/MM/YYYY")
    cat_serv = st.selectbox("Tipo", LISTA_SERVICOS)
    desc_serv = st.text_input("Detalhes", placeholder="Ex: 20 cópias coloridas, currículo, plastificação...")
    valor_serv = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
    salvar_servico = st.form_submit_button("Salvar serviço", use_container_width=True)
```

Após o `INSERT`, chamar `registrar_feedback_operacao("Serviço salvo com sucesso.")` e `st.rerun()`.

- [ ] **Step 4: Converter movimentação de créditos**

Usar `st.form("form_credito", clear_on_submit=True)` com dois `st.form_submit_button`: adicionar e usar crédito. Nos dois caminhos válidos, registrar feedback e executar `st.rerun()`. Manter as validações e o cálculo de saldo atuais.

- [ ] **Step 5: Atualizar edição/exclusão de serviços**

Substituir `st.success` anterior ao rerun por `registrar_feedback_operacao`. Manter confirmação de exclusão e as consultas atuais.

- [ ] **Step 6: Executar GREEN**

Run: teste do Step 1 e `python -m py_compile app.py`

Expected: PASS.

### Task 3: Gestão de tipos e cadastro de despesas

**Files:**
- Modify: `app.py:621-674`
- Test: comando Python com inspeção das consultas e regras

- [ ] **Step 1: Escrever o teste falhando**

```python
from pathlib import Path

source = Path("app.py").read_text(encoding="utf-8")
assert 'st.form("form_tipo_despesa", clear_on_submit=True)' in source
assert 'st.form("form_nova_despesa", clear_on_submit=True)' in source
assert "UPDATE tipos_despesa SET nome=:n WHERE id=:id AND username=:u" in source
assert "DELETE FROM tipos_despesa WHERE id=:id AND username=:u" in source
assert "despesas_vinculadas" in source
```

- [ ] **Step 2: Executar e confirmar RED**

Run: bloco acima via `python -`

Expected: FAIL porque edição e exclusão de tipos ainda não existem.

- [ ] **Step 3: Converter cadastro de tipos e despesas**

Usar forms com `clear_on_submit=True`. Preservar validações atuais, trocar sucesso direto por feedback persistente e fazer rerun.

- [ ] **Step 4: Adicionar gestão de tipos**

Exibir selectbox com `index=None`, campo de nome, confirmação de exclusão e botões Salvar/Excluir. Ao salvar, rejeitar vazio e duplicado excluindo o próprio `id` da comparação.

Calcular vínculos sem nova consulta:

```python
despesas_vinculadas = (
    int((df_expenses["tipo_id"] == tipo_id_selecionado).sum())
    if not df_expenses.empty else 0
)
```

Se `despesas_vinculadas > 0`, bloquear e informar a quantidade. Caso contrário, com confirmação marcada, executar:

```python
run_query(
    "DELETE FROM tipos_despesa WHERE id=:id AND username=:u",
    {"id": tipo_id_selecionado, "u": st.session_state.username},
    is_select=False,
)
```

- [ ] **Step 5: Executar GREEN**

Run: teste do Step 1 e `python -m py_compile app.py`

Expected: PASS.

### Task 4: Gestão dos registros de despesas e tabelas responsivas

**Files:**
- Modify: `app.py:398-710`
- Test: comando Python com inspeção das consultas e renderizações

- [ ] **Step 1: Escrever o teste falhando**

```python
from pathlib import Path

source = Path("app.py").read_text(encoding="utf-8")
assert "UPDATE despesas SET data=:d, tipo_id=:t, descricao=:de, valor=:v" in source
assert "DELETE FROM despesas WHERE id=:id AND username=:u" in source
assert source.count("exibir_tabela_responsiva(") >= 5
for sql in (
    "UPDATE tipos_despesa SET nome=:n WHERE id=:id AND username=:u",
    "DELETE FROM tipos_despesa WHERE id=:id AND username=:u",
    "DELETE FROM despesas WHERE id=:id AND username=:u",
):
    assert sql in source
```

- [ ] **Step 2: Executar e confirmar RED**

Run: bloco acima via `python -`

Expected: FAIL porque a gestão de registros e o helper ainda não são usados em todas as tabelas.

- [ ] **Step 3: Adicionar edição/exclusão de despesas**

Sob a tabela do período, exibir selectbox com `index=None`. Ao selecionar, carregar o registro por `id` e mostrar data, tipo, descrição e valor. Validar valor positivo antes de:

```python
run_query(
    """UPDATE despesas SET data=:d, tipo_id=:t, descricao=:de, valor=:v
       WHERE id=:id AND username=:u""",
    params,
    is_select=False,
)
```

Para exclusão confirmada:

```python
run_query(
    "DELETE FROM despesas WHERE id=:id AND username=:u",
    {"id": despesa_id, "u": st.session_state.username},
    is_select=False,
)
```

- [ ] **Step 4: Substituir todas as tabelas**

Trocar os quatro `st.dataframe` atuais por `exibir_tabela_responsiva`, marcando Data e Valor como colunas sem quebra. Manter a ordem e os nomes visíveis das colunas. A contagem mínima de cinco usos inclui a própria definição do helper.

- [ ] **Step 5: Executar GREEN e verificação final**

Run:

```powershell
python -m py_compile app.py
git diff --check -- app.py
git diff -- app.py
```

Expected: compilação e diff check com exit code 0; diff restrito a `app.py`.
