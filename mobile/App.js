import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";
import * as SQLite from "expo-sqlite";

const LISTA_SERVICOS = [
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
];

const today = () => new Date().toISOString().slice(0, 10);
const toNumber = (value) => Number(String(value || "0").replace(",", ".")) || 0;
const money = (value) =>
  Number(value || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
  });

const splitCategorias = (value) =>
  String(value || "")
    .split(" + ")
    .map((item) => item.trim())
    .filter(Boolean);

export default function App() {
  const [db, setDb] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("venda");
  const [servicos, setServicos] = useState([]);
  const [creditos, setCreditos] = useState([]);
  const [tiposDespesa, setTiposDespesa] = useState([]);
  const [despesas, setDespesas] = useState([]);
  const [toast, setToast] = useState("");

  const avisar = (message) => {
    setToast(message);
    setTimeout(() => setToast(""), 3200);
  };

  const carregar = async (database) => {
    const [servicosRows, creditosRows, tiposRows, despesasRows] = await Promise.all([
      database.getAllAsync("SELECT * FROM servicos ORDER BY data DESC, id DESC"),
      database.getAllAsync("SELECT * FROM creditos ORDER BY data DESC, id DESC"),
      database.getAllAsync("SELECT * FROM tipos_despesa ORDER BY nome"),
      database.getAllAsync(`
        SELECT d.*, t.nome AS tipo_nome
        FROM despesas d
        LEFT JOIN tipos_despesa t ON t.id = d.tipo_id
        ORDER BY d.data DESC, d.id DESC
      `)
    ]);
    setServicos(servicosRows);
    setCreditos(creditosRows);
    setTiposDespesa(tiposRows);
    setDespesas(despesasRows);
  };

  useEffect(() => {
    const iniciar = async () => {
      const database = await SQLite.openDatabaseAsync("grafica_rapida.db");
      await database.execAsync(`
        PRAGMA journal_mode = WAL;
        CREATE TABLE IF NOT EXISTS servicos (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          data TEXT NOT NULL,
          categoria TEXT NOT NULL,
          descricao TEXT,
          valor REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS creditos (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          cliente TEXT NOT NULL,
          tipo TEXT NOT NULL,
          valor REAL NOT NULL,
          data TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tipos_despesa (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          nome TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS despesas (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          data TEXT NOT NULL,
          tipo_id INTEGER NOT NULL,
          descricao TEXT,
          valor REAL NOT NULL,
          FOREIGN KEY (tipo_id) REFERENCES tipos_despesa(id)
        );
      `);
      setDb(database);
      await carregar(database);
      setLoading(false);
    };
    iniciar().catch((error) => {
      setLoading(false);
      Alert.alert("Erro ao iniciar", error.message);
    });
  }, []);

  const resumo = useMemo(() => {
    const hoje = today();
    const mes = hoje.slice(0, 7);
    const faturamentoHoje = servicos
      .filter((item) => item.data === hoje)
      .reduce((sum, item) => sum + Number(item.valor || 0), 0);
    const faturamentoMes = servicos
      .filter((item) => String(item.data).startsWith(mes))
      .reduce((sum, item) => sum + Number(item.valor || 0), 0);
    const despesasMes = despesas
      .filter((item) => String(item.data).startsWith(mes))
      .reduce((sum, item) => sum + Number(item.valor || 0), 0);
    const saldoCreditos = creditos.reduce((sum, item) => {
      const valor = Number(item.valor || 0);
      return sum + (item.tipo === "Crédito" ? valor : -valor);
    }, 0);
    return { faturamentoHoje, faturamentoMes, despesasMes, saldoCreditos };
  }, [servicos, creditos, despesas]);

  if (loading) {
    return (
      <SafeAreaView style={styles.safe}>
        <StatusBar barStyle="dark-content" backgroundColor="#fff8fb" />
        <View style={styles.center}>
          <ActivityIndicator color="#111827" size="large" />
          <Text style={styles.loadingText}>Abrindo Gráfica Rápida...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor="#fff8fb" />
      <ScrollView contentContainerStyle={styles.page} keyboardShouldPersistTaps="handled">
        <View style={styles.hero}>
          <Text style={styles.heroTitle}>Painel Financeiro</Text>
          <Text style={styles.heroText}>Registre vendas, despesas e créditos direto no celular, mesmo sem internet.</Text>
        </View>

        {!!toast && <Text style={styles.toast}>{toast}</Text>}

        <View style={styles.metricGrid}>
          <Metric label="Faturamento Hoje" value={money(resumo.faturamentoHoje)} />
          <Metric label="Faturamento Mês" value={money(resumo.faturamentoMes)} />
          <Metric label="Despesas Mês" value={money(resumo.despesasMes)} />
          <Metric label="Saldo Créditos" value={money(resumo.saldoCreditos)} />
        </View>

        <Tabs value={tab} onChange={setTab} />

        {tab === "venda" && (
          <Venda
            db={db}
            onDone={async () => {
              await carregar(db);
              avisar("Serviço salvo com sucesso.");
            }}
          />
        )}
        {tab === "historico" && (
          <Historico
            db={db}
            items={servicos}
            onDone={async (msg) => {
              await carregar(db);
              avisar(msg);
            }}
          />
        )}
        {tab === "creditos" && (
          <Creditos
            db={db}
            items={creditos}
            onDone={async () => {
              await carregar(db);
              avisar("Movimentação registrada.");
            }}
          />
        )}
        {tab === "despesas" && (
          <Despesas
            db={db}
            tipos={tiposDespesa}
            despesas={despesas}
            onDone={async (msg) => {
              await carregar(db);
              avisar(msg);
            }}
          />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function Metric({ label, value }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </View>
  );
}

function Tabs({ value, onChange }) {
  const tabs = [
    ["venda", "Novo serviço"],
    ["historico", "Histórico"],
    ["creditos", "Créditos"],
    ["despesas", "Despesas"]
  ];
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabs}>
      {tabs.map(([key, label]) => (
        <Pressable key={key} style={[styles.tab, value === key && styles.tabActive]} onPress={() => onChange(key)}>
          <Text style={[styles.tabText, value === key && styles.tabTextActive]}>{label}</Text>
        </Pressable>
      ))}
    </ScrollView>
  );
}

function Venda({ db, onDone }) {
  const [data, setData] = useState(today());
  const [categorias, setCategorias] = useState([]);
  const [descricao, setDescricao] = useState("");
  const [valor, setValor] = useState("");

  const toggle = (item) => {
    setCategorias((current) =>
      current.includes(item) ? current.filter((value) => value !== item) : [...current, item]
    );
  };

  const salvar = async () => {
    const total = toNumber(valor);
    if (!categorias.length) {
      Alert.alert("Atenção", "Selecione pelo menos um serviço ou produto.");
      return;
    }
    if (total <= 0) {
      Alert.alert("Atenção", "Informe um valor positivo.");
      return;
    }
    await db.runAsync(
      "INSERT INTO servicos (data, categoria, descricao, valor) VALUES (?, ?, ?, ?)",
      [data, categorias.join(" + "), descricao.trim(), total]
    );
    setData(today());
    setCategorias([]);
    setDescricao("");
    setValor("");
    onDone();
  };

  return (
    <Section title="Novo serviço">
      <Text style={styles.caption}>Registre uma venda com um ou mais serviços/produtos e um valor total.</Text>
      <Input label="Data" value={data} onChangeText={setData} placeholder="AAAA-MM-DD" />
      <Text style={styles.label}>Tipos de serviço</Text>
      <View style={styles.chipGrid}>
        {LISTA_SERVICOS.map((item) => (
          <Chip key={item} label={item} active={categorias.includes(item)} onPress={() => toggle(item)} />
        ))}
      </View>
      <Input label="Detalhes" value={descricao} onChangeText={setDescricao} placeholder="Ex: 20 cópias, plastificação..." />
      <Input label="Valor (R$)" value={valor} onChangeText={setValor} keyboardType="decimal-pad" placeholder="0,00" />
      <PrimaryButton label="Salvar serviço" onPress={salvar} />
    </Section>
  );
}

function Historico({ db, items, onDone }) {
  const [editId, setEditId] = useState(null);
  if (!items.length) {
    return <Empty text="Nenhum serviço foi registrado ainda." />;
  }
  return (
    <Section title="Histórico de serviços">
      {items.map((item) => (
        <View key={item.id} style={styles.record}>
          {editId === item.id ? (
            <EditarServico
              item={item}
              db={db}
              onCancel={() => setEditId(null)}
              onDone={async () => {
                setEditId(null);
                onDone("Alterações salvas com sucesso.");
              }}
            />
          ) : (
            <>
              <View style={styles.recordHeader}>
                <View style={styles.recordText}>
                  <Text style={styles.recordTitle}>{item.categoria}</Text>
                  <Text style={styles.recordMeta}>{item.data} · {item.descricao || "Sem detalhes"}</Text>
                </View>
                <Text style={styles.recordValue}>{money(item.valor)}</Text>
              </View>
              <View style={styles.actions}>
                <SmallButton label="Editar" onPress={() => setEditId(item.id)} />
                <SmallButton
                  label="Excluir"
                  danger
                  onPress={() =>
                    Alert.alert("Excluir serviço", "Essa ação remove o registro permanentemente.", [
                      { text: "Cancelar", style: "cancel" },
                      {
                        text: "Excluir",
                        style: "destructive",
                        onPress: async () => {
                          await db.runAsync("DELETE FROM servicos WHERE id = ?", [item.id]);
                          onDone("Serviço excluído com sucesso.");
                        }
                      }
                    ])
                  }
                />
              </View>
            </>
          )}
        </View>
      ))}
    </Section>
  );
}

function EditarServico({ item, db, onCancel, onDone }) {
  const [data, setData] = useState(item.data);
  const [categorias, setCategorias] = useState(splitCategorias(item.categoria));
  const [descricao, setDescricao] = useState(item.descricao || "");
  const [valor, setValor] = useState(String(item.valor || ""));
  const opcoes = Array.from(new Set([...LISTA_SERVICOS, ...categorias]));

  const toggle = (option) => {
    setCategorias((current) =>
      current.includes(option) ? current.filter((value) => value !== option) : [...current, option]
    );
  };

  const salvar = async () => {
    if (!categorias.length || toNumber(valor) <= 0) {
      Alert.alert("Atenção", "Selecione serviço/produto e informe um valor positivo.");
      return;
    }
    await db.runAsync(
      "UPDATE servicos SET data = ?, categoria = ?, descricao = ?, valor = ? WHERE id = ?",
      [data, categorias.join(" + "), descricao.trim(), toNumber(valor), item.id]
    );
    onDone();
  };

  return (
    <View>
      <Input label="Data" value={data} onChangeText={setData} />
      <View style={styles.chipGrid}>
        {opcoes.map((option) => (
          <Chip key={option} label={option} active={categorias.includes(option)} onPress={() => toggle(option)} />
        ))}
      </View>
      <Input label="Detalhes" value={descricao} onChangeText={setDescricao} />
      <Input label="Valor (R$)" value={valor} onChangeText={setValor} keyboardType="decimal-pad" />
      <View style={styles.actions}>
        <SmallButton label="Cancelar" onPress={onCancel} />
        <SmallButton label="Salvar" onPress={salvar} />
      </View>
    </View>
  );
}

function Creditos({ db, items, onDone }) {
  const [cliente, setCliente] = useState("");
  const [tipo, setTipo] = useState("Crédito");
  const [valor, setValor] = useState("");
  const saldos = items.reduce((acc, item) => {
    const atual = acc[item.cliente] || 0;
    acc[item.cliente] = atual + (item.tipo === "Crédito" ? Number(item.valor || 0) : -Number(item.valor || 0));
    return acc;
  }, {});

  const salvar = async () => {
    const total = toNumber(valor);
    if (!cliente.trim() || total <= 0) {
      Alert.alert("Atenção", "Preencha o nome do cliente e informe um valor positivo.");
      return;
    }
    await db.runAsync("INSERT INTO creditos (cliente, tipo, valor, data) VALUES (?, ?, ?, ?)", [
      cliente.trim(),
      tipo,
      total,
      today()
    ]);
    setCliente("");
    setValor("");
    onDone();
  };

  return (
    <>
      <Section title="Gestão de créditos">
        <Input label="Cliente" value={cliente} onChangeText={setCliente} placeholder="Nome do cliente" />
        <View style={styles.actions}>
          <SmallButton label="Crédito" active={tipo === "Crédito"} onPress={() => setTipo("Crédito")} />
          <SmallButton label="Débito" active={tipo === "Débito"} onPress={() => setTipo("Débito")} />
        </View>
        <Input label="Valor (R$)" value={valor} onChangeText={setValor} keyboardType="decimal-pad" placeholder="0,00" />
        <PrimaryButton label="Salvar movimentação" onPress={salvar} />
      </Section>
      <Section title="Saldo por cliente">
        {Object.keys(saldos).length ? (
          Object.entries(saldos).map(([nome, saldo]) => (
            <View key={nome} style={styles.line}>
              <Text style={styles.lineTitle}>{nome}</Text>
              <Text style={styles.lineValue}>{money(saldo)}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.caption}>Ainda não há movimentações de crédito.</Text>
        )}
      </Section>
    </>
  );
}

function Despesas({ db, tipos, despesas, onDone }) {
  const [nomeTipo, setNomeTipo] = useState("");
  const [tipoId, setTipoId] = useState(null);
  const [data, setData] = useState(today());
  const [descricao, setDescricao] = useState("");
  const [valor, setValor] = useState("");

  const criarTipo = async () => {
    if (!nomeTipo.trim()) {
      Alert.alert("Atenção", "Informe um nome para o tipo de despesa.");
      return;
    }
    try {
      await db.runAsync("INSERT INTO tipos_despesa (nome) VALUES (?)", [nomeTipo.trim()]);
      setNomeTipo("");
      onDone("Tipo de despesa cadastrado.");
    } catch (_error) {
      Alert.alert("Atenção", "Esse tipo de despesa já existe.");
    }
  };

  const salvarDespesa = async () => {
    const total = toNumber(valor);
    if (!tipoId || total <= 0) {
      Alert.alert("Atenção", "Selecione um tipo e informe um valor positivo.");
      return;
    }
    await db.runAsync("INSERT INTO despesas (data, tipo_id, descricao, valor) VALUES (?, ?, ?, ?)", [
      data,
      tipoId,
      descricao.trim(),
      total
    ]);
    setData(today());
    setDescricao("");
    setValor("");
    onDone("Despesa registrada.");
  };

  const total = despesas.reduce((sum, item) => sum + Number(item.valor || 0), 0);

  return (
    <>
      <Section title="Tipos de despesa">
        <Input label="Novo tipo" value={nomeTipo} onChangeText={setNomeTipo} placeholder="Ex: papel, tinta, manutenção" />
        <PrimaryButton label="Adicionar tipo" onPress={criarTipo} />
      </Section>

      <Section title="Registrar despesa">
        <Text style={styles.label}>Tipo</Text>
        <View style={styles.chipGrid}>
          {tipos.map((item) => (
            <Chip key={item.id} label={item.nome} active={tipoId === item.id} onPress={() => setTipoId(item.id)} />
          ))}
        </View>
        {!tipos.length && <Text style={styles.caption}>Cadastre um tipo de despesa antes de registrar gastos.</Text>}
        <Input label="Data" value={data} onChangeText={setData} />
        <Input label="Descrição" value={descricao} onChangeText={setDescricao} placeholder="Ex: resma A4" />
        <Input label="Valor (R$)" value={valor} onChangeText={setValor} keyboardType="decimal-pad" />
        <PrimaryButton label="Salvar despesa" onPress={salvarDespesa} />
      </Section>

      <Section title={`Resumo de despesas: ${money(total)}`}>
        {despesas.length ? (
          despesas.map((item) => (
            <View key={item.id} style={styles.line}>
              <View style={styles.lineText}>
                <Text style={styles.lineTitle}>{item.tipo_nome || "Sem tipo"}</Text>
                <Text style={styles.recordMeta}>{item.data} · {item.descricao || "Sem descrição"}</Text>
              </View>
              <Text style={styles.lineValue}>{money(item.valor)}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.caption}>Nenhuma despesa registrada.</Text>
        )}
      </Section>
    </>
  );
}

function Section({ title, children }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

function Input({ label, ...props }) {
  return (
    <View style={styles.inputGroup}>
      <Text style={styles.label}>{label}</Text>
      <TextInput style={styles.input} placeholderTextColor="#9ca3af" {...props} />
    </View>
  );
}

function Chip({ label, active, onPress }) {
  return (
    <Pressable style={[styles.chip, active && styles.chipActive]} onPress={onPress}>
      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
    </Pressable>
  );
}

function PrimaryButton({ label, onPress }) {
  return (
    <Pressable style={styles.primaryButton} onPress={onPress}>
      <Text style={styles.primaryButtonText}>{label}</Text>
    </Pressable>
  );
}

function SmallButton({ label, onPress, danger, active }) {
  return (
    <Pressable
      style={[styles.smallButton, danger && styles.smallButtonDanger, active && styles.smallButtonActive]}
      onPress={onPress}
    >
      <Text style={[styles.smallButtonText, danger && styles.smallButtonDangerText]}>{label}</Text>
    </Pressable>
  );
}

function Empty({ text }) {
  return (
    <Section title="Nada por aqui ainda">
      <Text style={styles.caption}>{text}</Text>
    </Section>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: "#fff8fb"
  },
  page: {
    padding: 16,
    paddingBottom: 34,
    backgroundColor: "#fff8fb"
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#fff8fb"
  },
  loadingText: {
    marginTop: 12,
    color: "#111827",
    fontSize: 16,
    fontWeight: "700"
  },
  hero: {
    backgroundColor: "rgba(255,255,255,0.96)",
    borderWidth: 1,
    borderColor: "rgba(249,168,212,0.45)",
    borderRadius: 22,
    padding: 18,
    marginBottom: 14,
    shadowColor: "#0f172a",
    shadowOpacity: 0.06,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 10 },
    elevation: 2
  },
  heroTitle: {
    color: "#111827",
    fontSize: 28,
    fontWeight: "900",
    textAlign: "center",
    marginBottom: 6
  },
  heroText: {
    color: "#374151",
    fontSize: 15,
    lineHeight: 22,
    textAlign: "center"
  },
  toast: {
    backgroundColor: "#dcfce7",
    color: "#166534",
    borderRadius: 14,
    padding: 12,
    fontWeight: "800",
    marginBottom: 12
  },
  metricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginBottom: 12
  },
  metric: {
    flexBasis: "47%",
    flexGrow: 1,
    backgroundColor: "rgba(255,255,255,0.96)",
    borderWidth: 1,
    borderColor: "rgba(249,168,212,0.45)",
    borderRadius: 18,
    padding: 14
  },
  metricLabel: {
    color: "#4b5563",
    fontSize: 13,
    fontWeight: "800",
    marginBottom: 7
  },
  metricValue: {
    color: "#111827",
    fontSize: 19,
    fontWeight: "900"
  },
  tabs: {
    marginBottom: 14
  },
  tab: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#f9a8d4",
    borderRadius: 999,
    paddingVertical: 10,
    paddingHorizontal: 14,
    marginRight: 8
  },
  tabActive: {
    backgroundColor: "#ffe4ef"
  },
  tabText: {
    color: "#374151",
    fontWeight: "800"
  },
  tabTextActive: {
    color: "#111827"
  },
  section: {
    backgroundColor: "rgba(255,255,255,0.96)",
    borderWidth: 1,
    borderColor: "rgba(249,168,212,0.35)",
    borderRadius: 18,
    padding: 15,
    marginBottom: 14,
    shadowColor: "#0f172a",
    shadowOpacity: 0.04,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 8 },
    elevation: 1
  },
  sectionTitle: {
    color: "#111827",
    fontSize: 20,
    fontWeight: "900",
    marginBottom: 10
  },
  caption: {
    color: "#4b5563",
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 10
  },
  inputGroup: {
    marginBottom: 10
  },
  label: {
    color: "#111827",
    fontSize: 14,
    fontWeight: "800",
    marginBottom: 6
  },
  input: {
    minHeight: 48,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 13,
    paddingHorizontal: 13,
    color: "#111827",
    fontSize: 16
  },
  chipGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 10
  },
  chip: {
    borderWidth: 1,
    borderColor: "#e5e7eb",
    backgroundColor: "#ffffff",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 9
  },
  chipActive: {
    backgroundColor: "#111827",
    borderColor: "#111827"
  },
  chipText: {
    color: "#374151",
    fontWeight: "800"
  },
  chipTextActive: {
    color: "#ffffff"
  },
  primaryButton: {
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#ffe4ef",
    borderWidth: 1,
    borderColor: "#f9a8d4",
    borderRadius: 14,
    marginTop: 4
  },
  primaryButtonText: {
    color: "#111827",
    fontWeight: "900",
    fontSize: 16
  },
  record: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 14,
    padding: 12,
    marginBottom: 10
  },
  recordHeader: {
    flexDirection: "row",
    gap: 10,
    justifyContent: "space-between"
  },
  recordText: {
    flex: 1
  },
  recordTitle: {
    color: "#111827",
    fontSize: 15,
    lineHeight: 21,
    fontWeight: "900"
  },
  recordMeta: {
    color: "#6b7280",
    fontSize: 13,
    lineHeight: 19,
    marginTop: 3
  },
  recordValue: {
    color: "#111827",
    fontWeight: "900"
  },
  actions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 10
  },
  smallButton: {
    flexGrow: 1,
    minHeight: 42,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f9fafb",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 12,
    paddingHorizontal: 12
  },
  smallButtonActive: {
    backgroundColor: "#ffe4ef",
    borderColor: "#f9a8d4"
  },
  smallButtonDanger: {
    backgroundColor: "#fff1f2",
    borderColor: "#fda4af"
  },
  smallButtonText: {
    color: "#111827",
    fontWeight: "900"
  },
  smallButtonDangerText: {
    color: "#9f1239"
  },
  line: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#e5e7eb",
    paddingVertical: 10
  },
  lineText: {
    flex: 1
  },
  lineTitle: {
    color: "#111827",
    fontWeight: "900"
  },
  lineValue: {
    color: "#111827",
    fontWeight: "900"
  }
});
