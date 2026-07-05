# Multiplos Servicos e Graficos Mobile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir varios servicos em uma unica venda, impedir interacao por toque nos graficos e garantir contraste no botao de cadastro.

**Architecture:** Toda a producao permanece em `app.py`. Duas funcoes puras convertem entre lista e texto combinado; os formularios usam essas funcoes sem mudar as queries, e uma configuracao Plotly compartilhada torna os graficos estaticos.

**Tech Stack:** Python, Streamlit, Plotly, unittest.

---

### Task 1: Categorias combinadas

**Files:**
- Create: `tests/test_app_servicos.py`
- Modify: `app.py:18-55`

- [ ] **Step 1: Write the failing tests**

Criar um carregador AST que execute apenas `combinar_categorias` e `separar_categorias` de `app.py`, sem inicializar Streamlit nem acessar secrets. Verificar estes resultados:

```python
assert combinar_categorias(["Impressao", "Edicao", "Plastificacao"]) == "Impressao + Edicao + Plastificacao"
assert separar_categorias("Impressao + Edicao") == ["Impressao", "Edicao"]
assert separar_categorias("Impressao") == ["Impressao"]
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_app_servicos -v`

Expected: FAIL porque as duas funcoes ainda nao existem.

- [ ] **Step 3: Implement the minimal helpers**

```python
def combinar_categorias(categorias):
    return " + ".join(categorias)


def separar_categorias(categoria):
    return [item.strip() for item in str(categoria).split(" + ") if item.strip()]
```

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m unittest tests.test_app_servicos -v`

Expected: PASS.

### Task 2: Formularios com varios servicos

**Files:**
- Modify: `tests/test_app_servicos.py`
- Modify: `app.py:445-539`

- [ ] **Step 1: Add a failing source-level UI test**

Verificar que `app.py` contem dois usos de `st.multiselect`, validacao de selecao vazia e conversao por `combinar_categorias` no cadastro e na edicao.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_app_servicos -v`

Expected: FAIL porque os formularios ainda usam `selectbox`.

- [ ] **Step 3: Implement the form changes**

No cadastro, trocar `Tipo` por `Tipos de servico`, exigir ao menos uma selecao e passar `combinar_categorias(cat_servicos)` no parametro `c` do `INSERT`. Na edicao, preencher o multiselect com `separar_categorias(categoria)`, acrescentar categorias antigas as opcoes e passar a combinacao no mesmo parametro `c` do `UPDATE`.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m unittest tests.test_app_servicos -v`

Expected: PASS.

### Task 3: Graficos estaticos e contraste

**Files:**
- Modify: `tests/test_app_servicos.py`
- Modify: `app.py:31-132,580-614,895-903`

- [ ] **Step 1: Add failing source-level tests**

Verificar que a configuracao compartilhada contem `staticPlot=True`, `displayModeBar=False` e `scrollZoom=False`, que todos os `st.plotly_chart` recebem essa configuracao e que o CSS contem o seletor `stFormSubmitButton` com texto `#1f2937`.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests.test_app_servicos -v`

Expected: FAIL porque configuracao e seletor ainda nao existem.

- [ ] **Step 3: Implement the minimal UI changes**

Adicionar `CONFIG_GRAFICO_ESTATICO`, passa-lo em todos os `st.plotly_chart` e ampliar o seletor CSS de botoes para cobrir o botao e seu paragrafo interno.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m unittest tests.test_app_servicos -v`

Expected: PASS.

### Task 4: Final verification

**Files:**
- Modify: `graphify-out/*` somente pelo atualizador AST do Graphify.

- [ ] **Step 1: Run syntax and unit checks**

Run: `python -m py_compile app.py`

Run: `python -m unittest tests.test_app_servicos -v`

Expected: ambos terminam com codigo 0.

- [ ] **Step 2: Check patch integrity**

Run: `git diff --check`

Expected: nenhuma saida.

- [ ] **Step 3: Refresh Graphify**

Run: `graphify update .`

Expected: atualizacao incremental concluida sem rebuild semantico.

- [ ] **Step 4: Review scope**

Confirmar no diff que SQL, login, JWT, sessao, `init_db()` e calculos financeiros nao foram alterados.
