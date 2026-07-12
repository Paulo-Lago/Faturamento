import ast
import unittest
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def carregar_funcoes_categorias():
    arvore = ast.parse(APP_PATH.read_text(encoding="utf-8"), filename=str(APP_PATH))
    nomes = {"combinar_categorias", "separar_categorias"}
    definicoes = [
        no for no in arvore.body
        if isinstance(no, ast.FunctionDef) and no.name in nomes
    ]
    modulo = ast.Module(body=definicoes, type_ignores=[])
    namespace = {}
    exec(compile(modulo, str(APP_PATH), "exec"), namespace)
    return namespace


class CategoriasDeServicoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.funcoes = carregar_funcoes_categorias()

    def test_combina_varios_servicos_em_uma_categoria(self):
        self.assertIn("combinar_categorias", self.funcoes)
        resultado = self.funcoes["combinar_categorias"](
            ["Impressao", "Edicao", "Plastificacao"]
        )
        self.assertEqual(resultado, "Impressao + Edicao + Plastificacao")

    def test_separa_categoria_combinada(self):
        self.assertIn("separar_categorias", self.funcoes)
        resultado = self.funcoes["separar_categorias"]("Impressao + Edicao")
        self.assertEqual(resultado, ["Impressao", "Edicao"])

    def test_mantem_compatibilidade_com_categoria_unica(self):
        self.assertIn("separar_categorias", self.funcoes)
        resultado = self.funcoes["separar_categorias"]("Impressao")
        self.assertEqual(resultado, ["Impressao"])


class FormulariosDeServicoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codigo = APP_PATH.read_text(encoding="utf-8")

    def test_cadastro_e_edicao_usam_multiselect(self):
        self.assertGreaterEqual(self.codigo.count("st.multiselect("), 2)

    def test_cadastro_exige_ao_menos_um_servico(self):
        self.assertIn("if not cat_servicos:", self.codigo)

    def test_cadastro_e_edicao_combinam_as_categorias(self):
        self.assertGreaterEqual(self.codigo.count("combinar_categorias("), 3)

    def test_edicao_preserva_categoria_antiga(self):
        self.assertIn(
            "list(dict.fromkeys(LISTA_SERVICOS + categorias_atuais))",
            self.codigo,
        )


class InterfaceMobileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codigo = APP_PATH.read_text(encoding="utf-8")
        cls.arvore = ast.parse(cls.codigo, filename=str(APP_PATH))

    def test_configuracao_desativa_interacao_dos_graficos(self):
        configuracao = None
        for no in self.arvore.body:
            if not isinstance(no, ast.Assign):
                continue
            if any(
                isinstance(alvo, ast.Name)
                and alvo.id == "CONFIG_GRAFICO_ESTATICO"
                for alvo in no.targets
            ):
                configuracao = ast.literal_eval(no.value)
                break

        self.assertIsNotNone(configuracao)
        self.assertIs(configuracao["staticPlot"], True)
        self.assertIs(configuracao["displayModeBar"], False)
        self.assertIs(configuracao["scrollZoom"], False)

    def test_todos_os_graficos_usam_configuracao_estatica(self):
        chamadas = [
            no for no in ast.walk(self.arvore)
            if isinstance(no, ast.Call)
            and isinstance(no.func, ast.Attribute)
            and no.func.attr == "plotly_chart"
        ]
        self.assertGreater(len(chamadas), 0)
        for chamada in chamadas:
            argumentos = {item.arg: item.value for item in chamada.keywords}
            self.assertIn("config", argumentos)
            self.assertIsInstance(argumentos["config"], ast.Name)
            self.assertEqual(argumentos["config"].id, "CONFIG_GRAFICO_ESTATICO")

    def test_css_define_contraste_para_botao_de_formulario(self):
        self.assertIn("stFormSubmitButton", self.codigo)
        self.assertIn("baseButton-primary", self.codigo)
        self.assertIn("color: #1f2937 !important", self.codigo)

    def test_nao_usa_components_html_depreciado(self):
        self.assertNotIn("streamlit.components.v1", self.codigo)
        self.assertNotIn("components.html(", self.codigo)

    def test_campos_de_novo_valor_iniciam_vazios(self):
        self.assertIn(
            'st.number_input("Valor (R$)", min_value=0.0, step=1.0, value=None',
            self.codigo,
        )
        self.assertIn(
            'st.number_input("Valor (R$)", min_value=0.0, step=0.5, value=None',
            self.codigo,
        )
        self.assertIn(
            'st.number_input("Valor da despesa (R$)", min_value=0.0, step=1.0, value=None',
            self.codigo,
        )


if __name__ == "__main__":
    unittest.main()
