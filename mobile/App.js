import { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  KeyboardAvoidingView,
  Platform,
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
const todayBR = () => formatDateBR(today());
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

const formatDateBR = (value) => {
  const text = String(value || "").trim();
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return text;
  return `${match[3]}/${match[2]}/${match[1]}`;
};

const parseDateBR = (value) => {
  const text = String(value || "").trim();
  const br = text.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (br) return `${br[3]}-${br[2]}-${br[1]}`;
  if (/^\d{4}-\d{2}-\d{2}$/.test(text)) return text;
  return null;
};

const formatDateLabel = (data, descricao) => `${formatDateBR(data)} · ${descricao || "Sem detalhes"}`;

const monthKey = () => today().slice(0, 7);

const sortRows = (rows) => rows.filter((row) => Number(row.value) !== 0).sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

const somarPorCategoria = (servicos) => {
  const totais = {};
  servicos.forEach((item) => {
    splitCategorias(item.categoria).forEach((categoria) => {
      totais[categoria] = (totais[categoria] || 0) + Number(item.valor || 0);
    });
  });
  return sortRows(Object.entries(totais).map(([label, value]) => ({ label, value })));
};

const somarPorTipoDespesa = (despesas) => {
  const totais = {};
  despesas.forEach((item) => {
    const tipo = item.tipo_nome || "Sem tipo";
    totais[tipo] = (totais[tipo] || 0) + Number(item.valor || 0);
  });
  return sortRows(Object.entries(totais).map(([label, value]) => ({ label, value })));
};

const somarPorSemana = (servicos) => {
  const totais = {};
  servicos.forEach((item) => {
    const base = new Date(`${item.data}T12:00:00`);
    if (Number.isNaN(base.getTime())) return;
    const segunda = new Date(base);
    segunda.setDate(base.getDate() - ((base.getDay() + 6) % 7));
    const domingo = new Date(segunda);
    domingo.setDate(segunda.getDate() + 6);
    const key = segunda.toISOString().slice(0, 10);
    const label = `${formatDateBR(key).slice(0, 5)} a ${formatDateBR(domingo.toISOString().slice(0, 10)).slice(0, 5)}`;
    totais[key] = {
      label,
      value: (totais[key]?.value || 0) + Number(item.valor || 0)
    };
  });
  return Object.entries(totais)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([, row]) => row);
};

export default function App() {
  const [db, setDb] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("venda");
  const [servicos, setServicos] = useState([]);
  const [creditos, setCreditos] = useState([]);
  const [tiposDespesa, setTiposDespesa] = useState([]);
  const [despesas, setDespesas] = useState([]);
  const [toast, setToast] = useState("");
  const [balloonRun, setBalloonRun] = useState(0);

  const avisar = (message) => {
    setToast(message);
    setBalloonRun((current) => current + 1);
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
      <KeyboardAvoidingView
        style={styles.keyboard}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
      <ScrollView
        contentContainerStyle={styles.page}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="interactive"
        automaticallyAdjustKeyboardInsets
      >
        <View style={styles.hero}>
          <Text style={styles.heroTitle}>Painel Financeiro</Text>
          <Text style={styles.heroText}>Registre vendas, despesas e créditos direto no celular, mesmo sem internet.</Text>
        </View>

        {!!toast && <Text style={styles.toast}>{toast}</Text>}
        <Balloons run={balloonRun} />

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
        {tab === "analises" && <Analises servicos={servicos} despesas={despesas} resumo={resumo} />}
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
      </KeyboardAvoidingView>
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

function Balloons({ run }) {
  const progress = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!run) return;
    progress.setValue(0);
    Animated.timing(progress, {
      toValue: 1,
      duration: 1800,
      useNativeDriver: true
    }).start();
  }, [progress, run]);

  if (!run) return null;

  const translateY = progress.interpolate({
    inputRange: [0, 1],
    outputRange: [60, -190]
  });
  const opacity = progress.interpolate({
    inputRange: [0, 0.75, 1],
    outputRange: [0, 1, 0]
  });

  return (
    <Animated.View pointerEvents="none" style={[styles.balloons, { opacity, transform: [{ translateY }] }]}>
      {["#e11d48", "#06b6d4", "#facc15", "#2563eb", "#ec4899"].map((color, index) => (
        <View key={color} style={[styles.balloon, { backgroundColor: color, left: `${10 + index * 18}%` }]} />
      ))}
    </Animated.View>
  );
}

function Analises({ servicos, despesas, resumo }) {
  const mesAtual = monthKey();
  const servicosMes = servicos.filter((item) => String(item.data || "").startsWith(mesAtual));
  const despesasMes = despesas.filter((item) => String(item.data || "").startsWith(mesAtual));
  const lucroMes = resumo.faturamentoMes - resumo.despesasMes;
  const distribuicao = [
    { label: "Despesas pagas", value: resumo.despesasMes, color: "#f97316" },
    { label: "Lucro líquido", value: Math.max(lucroMes, 0), color: "#16a34a" }
  ];

  return (
    <>
      <Section title="Análises">
        <Text style={styles.caption}>
          Gráficos otimizados para celular, com valores exatos ao lado de cada indicador.
        </Text>
      </Section>
      <BarChart
        title="Financeiro do mês"
        rows={[
          { label: "Faturamento", value: resumo.faturamentoMes, color: "#e11d48" },
          { label: "Despesas", value: resumo.despesasMes, color: "#f97316" },
          { label: "Lucro líquido", value: lucroMes, color: lucroMes >= 0 ? "#16a34a" : "#dc2626" }
        ]}
        emptyText="Ainda não há dados financeiros neste mês."
      />
      <BarChart
        title="Distribuição da receita"
        rows={distribuicao}
        emptyText="Registre faturamento e despesas para ver a distribuição."
      />
      <BarChart
        title="Faturamento por serviço/produto"
        rows={somarPorCategoria(servicosMes)}
        emptyText="Nenhum serviço registrado neste mês."
      />
      <BarChart
        title="Faturamento semanal"
        rows={somarPorSemana(servicosMes)}
        emptyText="Nenhum faturamento semanal disponível."
      />
      <BarChart
        title="Despesas por tipo"
        rows={somarPorTipoDespesa(despesasMes)}
        emptyText="Nenhuma despesa registrada neste mês."
      />
    </>
  );
}

function BarChart({ title, rows, emptyText }) {
  const visibleRows = rows.filter((row) => Number(row.value) !== 0);
  const max = Math.max(...visibleRows.map((row) => Math.abs(row.value)), 1);

  return (
    <View style={styles.chartCard}>
      <Text style={styles.chartTitle}>{title}</Text>
      {visibleRows.length === 0 ? (
        <Text style={styles.chartEmpty}>{emptyText}</Text>
      ) : (
        visibleRows.map((row) => (
          <View key={row.label} style={styles.chartRow}>
            <View style={styles.chartHeader}>
              <Text style={styles.chartLabel} numberOfLines={2}>
                {row.label}
              </Text>
              <Text style={[styles.chartValue, row.value < 0 && styles.chartValueDanger]}>{money(row.value)}</Text>
            </View>
            <View style={styles.chartTrack}>
              <View
                style={[
                  styles.chartBar,
                  row.value < 0 && styles.chartBarDanger,
                  {
                    backgroundColor: row.color || "#e11d48",
                    width: `${Math.max(6, (Math.abs(row.value) / max) * 100)}%`
                  }
                ]}
              />
            </View>
          </View>
        ))
      )}
    </View>
  );
}

function ServiceSelector({ selected, onToggle, options = LISTA_SERVICOS }) {
  const [open, setOpen] = useState(false);
  const summary = selected.length ? selected.join(" + ") : "Toque para selecionar serviços/produtos";

  return (
    <View style={styles.selectorWrap}>
      <Text style={styles.label}>Tipos de serviço</Text>
      <Pressable style={[styles.selectorBox, open && styles.selectorBoxOpen]} onPress={() => setOpen((value) => !value)}>
        <Text style={[styles.selectorText, !selected.length && styles.selectorPlaceholder]}>{summary}</Text>
        <Text style={styles.selectorArrow}>{open ? "▲" : "▼"}</Text>
      </Pressable>
      {open && (
        <View style={styles.selectorPanel}>
          {options.map((item) => (
            <Pressable
              key={item}
              style={[styles.serviceOption, selected.includes(item) && styles.serviceOptionActive]}
              onPress={() => onToggle(item)}
            >
              <Text style={[styles.serviceOptionText, selected.includes(item) && styles.serviceOptionTextActive]}>
                {item}
              </Text>
              <Text style={[styles.serviceCheck, selected.includes(item) && styles.serviceCheckActive]}>
                {selected.includes(item) ? "✓" : ""}
              </Text>
            </Pressable>
          ))}
        </View>
      )}
    </View>
  );
}

function Tabs({ value, onChange }) {
  const tabs = [
    ["venda", "Novo serviço"],
    ["historico", "Histórico"],
    ["analises", "Análises"],
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
  const [data, setData] = useState(todayBR());
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
    const dataISO = parseDateBR(data);
    if (!categorias.length) {
      Alert.alert("Atenção", "Selecione pelo menos um serviço ou produto.");
      return;
    }
    if (!dataISO) {
      Alert.alert("Atenção", "Informe a data no formato DD/MM/AAAA.");
      return;
    }
    if (total <= 0) {
      Alert.alert("Atenção", "Informe um valor positivo.");
      return;
    }
    await db.runAsync(
      "INSERT INTO servicos (data, categoria, descricao, valor) VALUES (?, ?, ?, ?)",
      [dataISO, categorias.join(" + "), descricao.trim(), total]
    );
    setData(todayBR());
    setCategorias([]);
    setDescricao("");
    setValor("");
    onDone();
  };

  return (
    <Section title="Novo serviço">
      <Text style={styles.caption}>Registre uma venda com um ou mais serviços/produtos e um valor total.</Text>
      <Input label="Data" value={data} onChangeText={setData} placeholder="DD/MM/AAAA" keyboardType="numbers-and-punctuation" />
      <ServiceSelector selected={categorias} onToggle={toggle} />
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
                  <Text style={styles.recordMeta}>{formatDateLabel(item.data, item.descricao)}</Text>
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
  const [data, setData] = useState(formatDateBR(item.data));
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
    const dataISO = parseDateBR(data);
    if (!categorias.length || toNumber(valor) <= 0) {
      Alert.alert("Atenção", "Selecione serviço/produto e informe um valor positivo.");
      return;
    }
    if (!dataISO) {
      Alert.alert("Atenção", "Informe a data no formato DD/MM/AAAA.");
      return;
    }
    await db.runAsync(
      "UPDATE servicos SET data = ?, categoria = ?, descricao = ?, valor = ? WHERE id = ?",
      [dataISO, categorias.join(" + "), descricao.trim(), toNumber(valor), item.id]
    );
    onDone();
  };

  return (
    <View>
      <Input label="Data" value={data} onChangeText={setData} keyboardType="numbers-and-punctuation" />
      <ServiceSelector selected={categorias} onToggle={toggle} options={opcoes} />
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
  const [data, setData] = useState(todayBR());
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
    const dataISO = parseDateBR(data);
    if (!tipoId || total <= 0) {
      Alert.alert("Atenção", "Selecione um tipo e informe um valor positivo.");
      return;
    }
    if (!dataISO) {
      Alert.alert("Atenção", "Informe a data no formato DD/MM/AAAA.");
      return;
    }
    await db.runAsync("INSERT INTO despesas (data, tipo_id, descricao, valor) VALUES (?, ?, ?, ?)", [
      dataISO,
      tipoId,
      descricao.trim(),
      total
    ]);
    setData(todayBR());
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
        <Input label="Data" value={data} onChangeText={setData} keyboardType="numbers-and-punctuation" />
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
                <Text style={styles.recordMeta}>{formatDateBR(item.data)} · {item.descricao || "Sem descrição"}</Text>
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
  keyboard: {
    flex: 1
  },
  page: {
    padding: 16,
    paddingTop: 34,
    paddingBottom: 140,
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
  balloons: {
    position: "absolute",
    left: 0,
    right: 0,
    top: 155,
    height: 120,
    zIndex: 20
  },
  balloon: {
    position: "absolute",
    bottom: 0,
    width: 24,
    height: 32,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: "rgba(255,255,255,0.85)"
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
  chartCard: {
    backgroundColor: "rgba(255,255,255,0.96)",
    borderWidth: 1,
    borderColor: "rgba(249,168,212,0.35)",
    borderRadius: 18,
    padding: 15,
    marginBottom: 14
  },
  chartTitle: {
    color: "#111827",
    fontSize: 18,
    fontWeight: "900",
    marginBottom: 10
  },
  chartRow: {
    marginBottom: 12
  },
  chartHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 10,
    marginBottom: 6
  },
  chartLabel: {
    flex: 1,
    color: "#374151",
    fontWeight: "900",
    lineHeight: 20
  },
  chartValue: {
    color: "#111827",
    fontWeight: "900",
    textAlign: "right"
  },
  chartValueDanger: {
    color: "#dc2626"
  },
  chartTrack: {
    height: 16,
    backgroundColor: "#f3f4f6",
    borderRadius: 999,
    overflow: "hidden"
  },
  chartBar: {
    height: "100%",
    borderRadius: 999
  },
  chartBarDanger: {
    backgroundColor: "#dc2626"
  },
  chartEmpty: {
    color: "#6b7280",
    fontSize: 14,
    lineHeight: 20,
    fontWeight: "700"
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
  selectorWrap: {
    marginBottom: 12
  },
  selectorBox: {
    minHeight: 52,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 14,
    paddingHorizontal: 13,
    paddingVertical: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10
  },
  selectorBoxOpen: {
    borderColor: "#e11d48",
    backgroundColor: "#fff1f2"
  },
  selectorText: {
    flex: 1,
    color: "#111827",
    fontSize: 15,
    lineHeight: 21,
    fontWeight: "800"
  },
  selectorPlaceholder: {
    color: "#6b7280",
    fontWeight: "700"
  },
  selectorArrow: {
    color: "#9f1239",
    fontSize: 14,
    fontWeight: "900"
  },
  selectorPanel: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderTopWidth: 0,
    borderColor: "#fecdd3",
    borderBottomLeftRadius: 14,
    borderBottomRightRadius: 14,
    padding: 8
  },
  serviceOption: {
    minHeight: 46,
    borderRadius: 11,
    paddingHorizontal: 11,
    paddingVertical: 9,
    marginBottom: 6,
    backgroundColor: "#f9fafb",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 8
  },
  serviceOptionActive: {
    backgroundColor: "#e11d48"
  },
  serviceOptionText: {
    flex: 1,
    color: "#374151",
    fontWeight: "800"
  },
  serviceOptionTextActive: {
    color: "#ffffff"
  },
  serviceCheck: {
    width: 22,
    color: "#ffffff",
    fontWeight: "900",
    textAlign: "center"
  },
  serviceCheckActive: {
    color: "#ffffff"
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
    backgroundColor: "#e11d48",
    borderColor: "#9f1239",
    shadowColor: "#9f1239",
    shadowOpacity: 0.24,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 4 },
    elevation: 3
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
