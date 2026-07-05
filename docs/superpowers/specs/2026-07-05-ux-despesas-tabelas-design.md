# Melhorias de UX, tabelas e despesas

## Objetivo

Melhorar a legibilidade dos gráficos e tabelas, limpar os formulários após operações bem-sucedidas e completar a gestão de tipos e registros de despesas, preservando a arquitetura atual em `app.py`.

## Escopo

- Manter todo o código em `app.py`, sem módulos novos e sem dependências adicionais.
- Não alterar autenticação, sessão, JWT, schema ou regras existentes de faturamento e créditos.
- Usar somente as tabelas existentes `tipos_despesa` e `despesas`.
- Manter todas as consultas limitadas por `username`.

## Interface

### Gráficos

Os três gráficos Plotly usarão fonte `#111827` em títulos, eixos, marcas, legendas e rótulos. Fundo e séries atuais serão preservados.

### Feedback e limpeza

Os cadastros de serviço, crédito/débito, tipo de despesa e despesa usarão `st.form(clear_on_submit=True)`. Após uma gravação ou edição válida, o app registrará uma mensagem temporária em `st.session_state`, atualizará os dados com `st.rerun()` e exibirá uma única mensagem de sucesso acompanhada de `st.balloons()`.

As seleções de edição serão limpas após salvar ou excluir. Falhas de validação manterão os valores preenchidos para correção.

### Tabelas responsivas

As tabelas de serviços, saldos, movimentações, tipos e despesas serão renderizadas por um helper local que:

- converte o DataFrame para HTML com `escape=True`;
- permite quebra de linha em textos longos;
- mantém datas e valores monetários sem quebra;
- usa largura total em desktop;
- oferece rolagem horizontal em telas pequenas;
- não usa truncamento com reticências.

## Aba Despesas

O layout seguirá a opção B:

1. Gestão de tipos e cadastro de despesa em duas colunas no topo.
2. Resumo por período e gráfico no bloco intermediário.
3. Tabela responsiva e gestão de registros no bloco inferior.

### Tipos de despesa

O usuário poderá cadastrar, selecionar e renomear tipos. Nomes vazios ou duplicados para o mesmo usuário serão rejeitados.

Antes da exclusão, o app contará despesas vinculadas ao `tipo_id`. Se houver vínculos, bloqueará a operação e informará quantos registros precisam ser reclassificados. Sem vínculos, exigirá confirmação explícita antes do `DELETE`.

### Registros de despesas

O usuário poderá selecionar uma despesa existente e alterar data, tipo, descrição e valor. O valor deverá ser positivo. A exclusão exigirá confirmação explícita.

As operações usarão o `id` do registro e o `username` da sessão no `WHERE`, evitando modificar dados de outro usuário.

## Consultas

Serão adicionadas apenas consultas parametrizadas:

- `UPDATE tipos_despesa ... WHERE id=:id AND username=:u`;
- `DELETE FROM tipos_despesa WHERE id=:id AND username=:u`;
- `UPDATE despesas ... WHERE id=:id AND username=:u`;
- `DELETE FROM despesas WHERE id=:id AND username=:u`.

Não haverá migração nem alteração de schema.

## Validação

- Testes estáticos de regressão confirmarão fontes escuras nos gráficos, formulários com limpeza e consultas sempre limitadas por usuário.
- Testes de regras confirmarão bloqueio de exclusão de tipos vinculados e rejeição de nomes duplicados.
- `python -m py_compile app.py` e `git diff --check` deverão passar.
- O app não será iniciado localmente para evitar acionar `init_db()` ou o banco durante a validação.
