# Multiplos Servicos e Graficos Mobile - Design

## Objetivo

Permitir que uma venda registre varios servicos ou produtos com um unico valor total, melhorar o uso dos graficos no celular e corrigir o contraste do botao de cadastro, sem alterar banco, autenticacao ou regras financeiras.

## Cadastro e persistencia

- O campo `Tipo` do formulario de novo servico sera um `st.multiselect` baseado em `LISTA_SERVICOS`.
- O usuario podera escolher um ou varios itens e informar um unico valor total para a venda.
- O envio sem nenhum item selecionado exibira um aviso e nao executara o `INSERT`.
- Os itens selecionados serao unidos por ` + ` e gravados na coluna `categoria` da mesma linha ja usada hoje.
- O formulario continuara usando `clear_on_submit=True`, preservando a limpeza apos o cadastro bem-sucedido.
- Nenhuma tabela, coluna, consulta SQL ou calculo sera alterado.

## Edicao e compatibilidade

- A edicao no historico tambem usara `st.multiselect`.
- Categorias combinadas serao separadas por ` + ` para preencher a selecao atual.
- Registros antigos com uma unica categoria continuarao funcionando.
- Categorias antigas que nao estejam mais em `LISTA_SERVICOS` serao mantidas como opcao durante a edicao, evitando perda silenciosa de dados.
- O salvamento continuara atualizando uma unica linha e um unico valor total.

## Analises

- Uma combinacao sera apresentada como uma categoria unica nos agrupamentos atuais, por exemplo `Impressao + Edicao`.
- O faturamento nao sera dividido entre os itens, evitando duplicacao ou rateio inventado.
- Os graficos Plotly receberao uma configuracao comum com `staticPlot=True`, barra de ferramentas oculta e zoom por rolagem desativado.
- No celular, toques e movimentos sobre o grafico nao alterarao zoom, pan ou tamanho; o gesto ficara disponivel para a rolagem da pagina.

## Aparencia dos botoes

- O CSS cobrira explicitamente botoes de envio de formulario e seus textos internos.
- A cor do texto sera escura e contrastante, inclusive no botao de salvar um novo servico.
- A logica e o comportamento dos botoes nao serao modificados.

## Validacao

- Testes automatizados verificarao combinacao, separacao e compatibilidade com categorias antigas.
- Verificacoes estaticas confirmarao o uso do multiselect, a configuracao estatica dos graficos e o seletor CSS do botao.
- A validacao final incluira os testes do projeto, `python -m py_compile app.py`, `git diff --check` e `graphify update .`.

## Fora de escopo

- Mudancas de schema, migracoes ou novas tabelas.
- Alteracoes em SQL, login, JWT, sessao, `init_db()` ou regras de negocio.
- Rateio do valor entre servicos e alteracao do calculo de faturamento.
- Modularizacao ou criacao de dependencias novas.
