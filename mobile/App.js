import AsyncStorage from "@react-native-async-storage/async-storage";
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
  useWindowDimensions,
  View
} from "react-native";

const API_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "faturamento.token";
const USER_KEY = "faturamento.username";
const TODAY = new Date().toISOString().slice(0, 10);

const money = (value) =>
  Number(value || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
  });

const splitCategories = (category) =>
  String(category || "")
    .split(" + ")
    .map((item) => item.trim())
    .filter(Boolean);

export default function App() {
  const { width } = useWindowDimensions();
  const isTablet = width >= 760;
  const [booting, setBooting] = useState(true);
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState(null);
  const [username, setUsername] = useState("");
  const [screen, setScreen] = useState("inicio");
  const [message, setMessage] = useState("");
  const [config, setConfig] = useState({ servicos: [] });
  const [dashboard, setDashboard] = useState({ faturamentoHoje: 0, faturamentoMes: 0 });
  const [services, setServices] = useState([]);
  const [expenseTypes, setExpenseTypes] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [credits, setCredits] = useState({ items: [], saldos: {} });

  const api = async (path, options = {}) => {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.headers || {})
      }
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || "Não foi possível concluir a operação.");
    }
    return payload;
  };

  const notify = (text) => {
    setMessage(text);
    setTimeout(() => setMessage(""), 3500);
  };

  const refresh = async () => {
    if (!token) return;
    const [dash, serviceData, typeData, expenseData, creditData] = await Promise.all([
      api("/dashboard"),
      api("/services"),
      api("/expense-types"),
      api("/expenses"),
      api("/credits")
    ]);
    setDashboard(dash);
    setServices(serviceData.items || []);
    setExpenseTypes(typeData.items || []);
    setExpenses(expenseData.items || []);
    setCredits(creditData || { items: [], saldos: {} });
  };

  useEffect(() => {
    const load = async () => {
      try {
        const [savedToken, savedUser] = await Promise.all([
          AsyncStorage.getItem(TOKEN_KEY),
          AsyncStorage.getItem(USER_KEY)
        ]);
        const cfg = await fetch(`${API_URL}/config`).then((res) => res.json());
        setConfig(cfg);
        if (savedToken) {
          setToken(savedToken);
          setUsername(savedUser || "");
        }
      } catch (_error) {
        setMessage("Configure a URL da API para conectar o app mobile.");
      } finally {
        setBooting(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    refresh()
      .catch((error) => setMessage(error.message))
      .finally(() => setLoading(false));
  }, [token]);

  const login = async (form, mode) => {
    setLoading(true);
    try {
      const payload = await api(mode === "signup" ? "/auth/signup" : "/auth/login", {
        method: "POST",
        body: JSON.stringify(form)
      });
      setToken(payload.token);
      setUsername(payload.username);
      await AsyncStorage.multiSet([
        [TOKEN_KEY, payload.token],
        [USER_KEY, payload.username]
      ]);
      notify(mode === "signup" ? "Conta criada e login realizado." : "Login realizado com sucesso.");
    } catch (error) {
      Alert.alert("Atenção", error.message);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setToken(null);
    setUsername("");
    await AsyncStorage.multiRemove([TOKEN_KEY, USER_KEY]);
  };

  const contentStyle = useMemo(
    () => [styles.content, isTablet && styles.contentTablet],
    [isTablet]
  );

  if (booting) {
    return (
      <SafeAreaView style={styles.safe}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.center}>
          <ActivityIndicator color="#111827" />
          <Text style={styles.muted}>Carregando app mobile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!token) {
    return (
      <SafeAreaView style={styles.safe}>
        <StatusBar barStyle="dark-content" />
        <ScrollView contentContainerStyle={contentStyle}>
          <LoginScreen loading={loading} onSubmit={login} />
          <Text style={styles.apiHint}>API: {API_URL}</Text>
        </ScrollView>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentContainerStyle={contentStyle} keyboardShouldPersistTaps="handled">
        <Header username={username} onLogout={logout} />
        {!!message && <Text style={styles.toast}>{message}</Text>}
        {loading && <ActivityIndicator color="#111827" style={styles.loading} />}
        <Tabs value={screen} onChange={setScreen} />
        {screen === "inicio" && (
          <HomeScreen dashboard={dashboard} services={services} expenses={expenses} credits={credits} />
        )}
        {screen === "venda" && (
          <SaleScreen
            services={config.servicos}
            onSubmit={async (payload) => {
              await api("/services", { method: "POST", body: JSON.stringify(payload) });
              await refresh();
              notify("Venda registrada com sucesso.");
            }}
          />
        )}
        {screen === "historico" && (
          <HistoryScreen
            items={services}
            serviceOptions={config.servicos}
            onDelete={async (id) => {
              await api(`/services/${id}`, { method: "DELETE" });
              await refresh();
              notify("Registro excluído com sucesso.");
            }}
            onUpdate={async (id, payload) => {
              await api(`/services/${id}`, { method: "PUT", body: JSON.stringify(payload) });
              await refresh();
              notify("Registro atualizado com sucesso.");
            }}
          />
        )}
        {screen === "creditos" && (
          <CreditsScreen
            credits={credits}
            onSubmit={async (payload) => {
              await api("/credits", { method: "POST", body: JSON.stringify(payload) });
              await refresh();
              notify("Movimentação registrada.");
            }}
          />
        )}
        {screen === "despesas" && (
          <ExpensesScreen
            types={expenseTypes}
            expenses={expenses}
            onCreateType={async (payload) => {
              await api("/expense-types", { method: "POST", body: JSON.stringify(payload) });
              await refresh();
              notify("Tipo de despesa cadastrado.");
            }}
            onUpdateType={async (id, payload) => {
              await api(`/expense-types/${id}`, { method: "PUT", body: JSON.stringify(payload) });
              await refresh();
              notify("Tipo de despesa atualizado.");
            }}
            onDeleteType={async (id) => {
              await api(`/expense-types/${id}`, { method: "DELETE" });
              await refresh();
              notify("Tipo de despesa excluído.");
            }}
            onCreateExpense={async (payload) => {
              await api("/expenses", { method: "POST", body: JSON.stringify(payload) });
              await refresh();
              notify("Despesa registrada.");
            }}
            onUpdateExpense={async (id, payload) => {
              await api(`/expenses/${id}`, { method: "PUT", body: JSON.stringify(payload) });
              await refresh();
              notify("Despesa atualizada.");
            }}
            onDeleteExpense={async (id) => {
              await api(`/expenses/${id}`, { method: "DELETE" });
              await refresh();
              notify("Despesa excluída.");
            }}
          />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function LoginScreen({ loading, onSubmit }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const submit = (mode) => {
    if (!username.trim() || !password) {
      Alert.alert("Atenção", "Informe usuário e senha.");
      return;
    }
    onSubmit({ username: username.trim(), password }, mode);
  };

  return (
    <View style={styles.loginPanel}>
      <Text style={styles.brand}>Faturamento</Text>
      <Text style={styles.title}>Acesse sua conta</Text>
      <Text style={styles.subtitle}>Registre vendas, acompanhe resultados e controle créditos pelo celular.</Text>
      <TextInput
        style={styles.input}
        placeholder="Usuário"
        value={username}
        onChangeText={setUsername}
        autoCapitalize="none"
      />
      <TextInput
        style={styles.input}
        placeholder="Senha"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      <Pressable style={styles.primaryButton} onPress={() => submit("login")} disabled={loading}>
        <Text style={styles.primaryButtonText}>{loading ? "Entrando..." : "Entrar"}</Text>
      </Pressable>
      <Pressable style={styles.secondaryButton} onPress={() => submit("signup")} disabled={loading}>
        <Text style={styles.secondaryButtonText}>Criar conta</Text>
      </Pressable>
    </View>
  );
}

function Header({ username, onLogout }) {
  return (
    <View style={styles.header}>
      <View>
        <Text style={styles.kicker}>Painel mobile</Text>
        <Text style={styles.headerTitle}>Olá, {username}</Text>
      </View>
      <Pressable style={styles.logoutButton} onPress={onLogout}>
        <Text style={styles.logoutText}>Sair</Text>
      </Pressable>
    </View>
  );
}

function Tabs({ value, onChange }) {
  const tabs = [
    ["inicio", "Início"],
    ["venda", "Venda"],
    ["historico", "Histórico"],
    ["creditos", "Créditos"],
    ["despesas", "Despesas"]
  ];
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabs}>
      {tabs.map(([key, label]) => (
        <Pressable
          key={key}
          style={[styles.tab, value === key && styles.tabActive]}
          onPress={() => onChange(key)}
        >
          <Text style={[styles.tabText, value === key && styles.tabTextActive]}>{label}</Text>
        </Pressable>
      ))}
    </ScrollView>
  );
}

function HomeScreen({ dashboard, services, expenses, credits }) {
  const totalDespesas = expenses.reduce((sum, item) => sum + Number(item.valor || 0), 0);
  const totalCreditos = Object.values(credits.saldos || {}).reduce((sum, item) => sum + Number(item || 0), 0);
  return (
    <View>
      <View style={styles.metricGrid}>
        <Metric label="Hoje" value={money(dashboard.faturamentoHoje)} />
        <Metric label="Mês" value={money(dashboard.faturamentoMes)} />
        <Metric label="Despesas" value={money(totalDespesas)} tone="danger" />
        <Metric label="Saldo créditos" value={money(totalCreditos)} tone="success" />
      </View>
      <Section title="Resumo rápido">
        <Text style={styles.bodyText}>Serviços registrados: {services.length}</Text>
        <Text style={styles.bodyText}>Despesas registradas: {expenses.length}</Text>
        <Text style={styles.bodyText}>Clientes com saldo: {Object.keys(credits.saldos || {}).length}</Text>
      </Section>
    </View>
  );
}

function Metric({ label, value, tone }) {
  return (
    <View style={[styles.metric, tone === "danger" && styles.metricDanger, tone === "success" && styles.metricSuccess]}>
      <Text style={styles.metricLabel}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
    </View>
  );
}

function SaleScreen({ services, onSubmit }) {
  const [date, setDate] = useState(TODAY);
  const [selected, setSelected] = useState([]);
  const [description, setDescription] = useState("");
  const [value, setValue] = useState("");

  const toggle = (item) => {
    setSelected((current) =>
      current.includes(item) ? current.filter((value) => value !== item) : [...current, item]
    );
  };

  const submit = async () => {
    if (!selected.length || Number(value.replace(",", ".")) <= 0) {
      Alert.alert("Atenção", "Selecione ao menos um serviço/produto e informe o valor.");
      return;
    }
    await onSubmit({
      data: date,
      categorias: selected,
      descricao: description,
      valor: Number(value.replace(",", "."))
    });
    setSelected([]);
    setDescription("");
    setValue("");
  };

  return (
    <Section title="Nova venda ou serviço">
      <TextInput style={styles.input} value={date} onChangeText={setDate} placeholder="Data AAAA-MM-DD" />
      <Text style={styles.label}>Serviços/produtos</Text>
      <View style={styles.chipGrid}>
        {services.map((item) => (
          <Pressable
            key={item}
            style={[styles.chip, selected.includes(item) && styles.chipActive]}
            onPress={() => toggle(item)}
          >
            <Text style={[styles.chipText, selected.includes(item) && styles.chipTextActive]}>{item}</Text>
          </Pressable>
        ))}
      </View>
      <TextInput
        style={styles.input}
        value={description}
        onChangeText={setDescription}
        placeholder="Detalhes do atendimento"
      />
      <TextInput
        style={styles.input}
        value={value}
        onChangeText={setValue}
        placeholder="Valor total"
        keyboardType="decimal-pad"
      />
      <Pressable style={styles.primaryButton} onPress={submit}>
        <Text style={styles.primaryButtonText}>Registrar venda</Text>
      </Pressable>
    </Section>
  );
}

function HistoryScreen({ items, serviceOptions, onDelete, onUpdate }) {
  const [editing, setEditing] = useState(null);
  if (!items.length) {
    return <EmptyState text="Nenhum serviço registrado ainda." />;
  }
  return (
    <View>
      {items.map((item) => (
        <RecordCard key={item.id} item={item}>
          {editing === item.id ? (
            <EditServiceForm
              item={item}
              serviceOptions={serviceOptions}
              onCancel={() => setEditing(null)}
              onSave={async (payload) => {
                await onUpdate(item.id, payload);
                setEditing(null);
              }}
            />
          ) : (
            <View style={styles.actions}>
              <Pressable style={styles.smallButton} onPress={() => setEditing(item.id)}>
                <Text style={styles.smallButtonText}>Editar</Text>
              </Pressable>
              <Pressable
                style={[styles.smallButton, styles.dangerButton]}
                onPress={() =>
                  Alert.alert("Excluir registro", "Essa ação remove o serviço permanentemente.", [
                    { text: "Cancelar", style: "cancel" },
                    { text: "Excluir", style: "destructive", onPress: () => onDelete(item.id) }
                  ])
                }
              >
                <Text style={styles.dangerButtonText}>Excluir</Text>
              </Pressable>
            </View>
          )}
        </RecordCard>
      ))}
    </View>
  );
}

function EditServiceForm({ item, serviceOptions, onCancel, onSave }) {
  const [date, setDate] = useState(String(item.data || "").slice(0, 10));
  const [selected, setSelected] = useState(splitCategories(item.categoria));
  const [description, setDescription] = useState(item.descricao || "");
  const [value, setValue] = useState(String(item.valor || ""));
  const options = Array.from(new Set([...serviceOptions, ...selected]));

  const toggle = (option) => {
    setSelected((current) =>
      current.includes(option) ? current.filter((value) => value !== option) : [...current, option]
    );
  };

  return (
    <View style={styles.editBox}>
      <TextInput style={styles.input} value={date} onChangeText={setDate} placeholder="Data AAAA-MM-DD" />
      <View style={styles.chipGrid}>
        {options.map((option) => (
          <Pressable
            key={option}
            style={[styles.chip, selected.includes(option) && styles.chipActive]}
            onPress={() => toggle(option)}
          >
            <Text style={[styles.chipText, selected.includes(option) && styles.chipTextActive]}>{option}</Text>
          </Pressable>
        ))}
      </View>
      <TextInput style={styles.input} value={description} onChangeText={setDescription} />
      <TextInput style={styles.input} value={value} onChangeText={setValue} keyboardType="decimal-pad" />
      <View style={styles.actions}>
        <Pressable style={styles.smallButton} onPress={onCancel}>
          <Text style={styles.smallButtonText}>Cancelar</Text>
        </Pressable>
        <Pressable
          style={styles.smallButton}
          onPress={() =>
            onSave({
              data: date,
              categorias: selected,
              descricao: description,
              valor: Number(value.replace(",", "."))
            })
          }
        >
          <Text style={styles.smallButtonText}>Salvar</Text>
        </Pressable>
      </View>
    </View>
  );
}

function CreditsScreen({ credits, onSubmit }) {
  const [cliente, setCliente] = useState("");
  const [tipo, setTipo] = useState("Crédito");
  const [valor, setValor] = useState("");

  const submit = async () => {
    await onSubmit({ cliente, tipo, valor: Number(valor.replace(",", ".")) });
    setCliente("");
    setValor("");
  };

  return (
    <View>
      <Section title="Registrar crédito ou débito">
        <TextInput style={styles.input} value={cliente} onChangeText={setCliente} placeholder="Nome do cliente" />
        <View style={styles.actions}>
          {["Crédito", "Débito"].map((item) => (
            <Pressable
              key={item}
              style={[styles.smallButton, tipo === item && styles.smallButtonActive]}
              onPress={() => setTipo(item)}
            >
              <Text style={styles.smallButtonText}>{item}</Text>
            </Pressable>
          ))}
        </View>
        <TextInput style={styles.input} value={valor} onChangeText={setValor} placeholder="Valor" keyboardType="decimal-pad" />
        <Pressable style={styles.primaryButton} onPress={submit}>
          <Text style={styles.primaryButtonText}>Salvar movimentação</Text>
        </Pressable>
      </Section>
      <Section title="Saldos por cliente">
        {Object.entries(credits.saldos || {}).length ? (
          Object.entries(credits.saldos).map(([name, saldo]) => (
            <View key={name} style={styles.row}>
              <Text style={styles.bodyText}>{name}</Text>
              <Text style={styles.rowValue}>{money(saldo)}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.muted}>Nenhum crédito registrado.</Text>
        )}
      </Section>
    </View>
  );
}

function ExpensesScreen({ types, expenses, onCreateType, onCreateExpense }) {
  const [typeName, setTypeName] = useState("");
  const [typeId, setTypeId] = useState(null);
  const [date, setDate] = useState(TODAY);
  const [description, setDescription] = useState("");
  const [value, setValue] = useState("");
  const total = expenses.reduce((sum, item) => sum + Number(item.valor || 0), 0);

  const createType = async () => {
    await onCreateType({ nome: typeName });
    setTypeName("");
  };

  const createExpense = async () => {
    await onCreateExpense({
      data: date,
      tipo_id: typeId,
      descricao: description,
      valor: Number(value.replace(",", "."))
    });
    setDescription("");
    setValue("");
  };

  return (
    <View>
      <Section title="Tipos de despesa">
        <TextInput style={styles.input} value={typeName} onChangeText={setTypeName} placeholder="Ex: papel, tinta, manutenção" />
        <Pressable style={styles.secondaryButton} onPress={createType}>
          <Text style={styles.secondaryButtonText}>Adicionar tipo</Text>
        </Pressable>
        <View style={styles.chipGrid}>
          {types.map((item) => (
            <Pressable
              key={item.id}
              style={[styles.chip, typeId === item.id && styles.chipActive]}
              onPress={() => setTypeId(item.id)}
            >
              <Text style={[styles.chipText, typeId === item.id && styles.chipTextActive]}>{item.nome}</Text>
            </Pressable>
          ))}
        </View>
      </Section>
      <Section title="Registrar despesa">
        <TextInput style={styles.input} value={date} onChangeText={setDate} placeholder="Data AAAA-MM-DD" />
        <TextInput style={styles.input} value={description} onChangeText={setDescription} placeholder="Descrição" />
        <TextInput style={styles.input} value={value} onChangeText={setValue} placeholder="Valor" keyboardType="decimal-pad" />
        <Pressable style={styles.primaryButton} onPress={createExpense}>
          <Text style={styles.primaryButtonText}>Salvar despesa</Text>
        </Pressable>
      </Section>
      <Section title={`Resumo de despesas: ${money(total)}`}>
        {expenses.length ? (
          expenses.map((item) => (
            <View key={item.id} style={styles.row}>
              <View style={styles.rowText}>
                <Text style={styles.bodyText}>{item.tipo_nome || "Sem tipo"}</Text>
                <Text style={styles.muted}>{String(item.data).slice(0, 10)} · {item.descricao || "Sem descrição"}</Text>
              </View>
              <Text style={styles.rowValue}>{money(item.valor)}</Text>
            </View>
          ))
        ) : (
          <Text style={styles.muted}>Nenhuma despesa registrada.</Text>
        )}
      </Section>
    </View>
  );
}

function RecordCard({ item, children }) {
  return (
    <View style={styles.record}>
      <View style={styles.row}>
        <View style={styles.rowText}>
          <Text style={styles.recordTitle}>{item.categoria}</Text>
          <Text style={styles.muted}>{String(item.data).slice(0, 10)} · {item.descricao || "Sem detalhes"}</Text>
        </View>
        <Text style={styles.recordValue}>{money(item.valor)}</Text>
      </View>
      {children}
    </View>
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

function EmptyState({ text }) {
  return (
    <View style={styles.empty}>
      <Text style={styles.emptyTitle}>Nada por aqui ainda</Text>
      <Text style={styles.muted}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: "#f8fafc"
  },
  content: {
    padding: 18,
    paddingBottom: 36
  },
  contentTablet: {
    width: 720,
    alignSelf: "center"
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12
  },
  loginPanel: {
    marginTop: 36,
    padding: 22,
    borderRadius: 18,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    shadowColor: "#0f172a",
    shadowOpacity: 0.08,
    shadowRadius: 18,
    shadowOffset: { width: 0, height: 10 },
    elevation: 2
  },
  brand: {
    color: "#0f766e",
    fontSize: 15,
    fontWeight: "800",
    textTransform: "uppercase",
    marginBottom: 8
  },
  title: {
    color: "#111827",
    fontSize: 30,
    fontWeight: "900",
    marginBottom: 8
  },
  subtitle: {
    color: "#4b5563",
    fontSize: 16,
    lineHeight: 23,
    marginBottom: 22
  },
  apiHint: {
    color: "#64748b",
    marginTop: 16,
    fontSize: 12,
    textAlign: "center"
  },
  header: {
    gap: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 18
  },
  kicker: {
    color: "#0f766e",
    fontWeight: "800",
    textTransform: "uppercase"
  },
  headerTitle: {
    color: "#111827",
    fontSize: 26,
    fontWeight: "900"
  },
  logoutButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: "#fee2e2"
  },
  logoutText: {
    color: "#991b1b",
    fontWeight: "800"
  },
  toast: {
    padding: 12,
    borderRadius: 12,
    color: "#065f46",
    backgroundColor: "#d1fae5",
    marginBottom: 12,
    fontWeight: "700"
  },
  loading: {
    marginBottom: 12
  },
  tabs: {
    marginBottom: 18
  },
  tab: {
    paddingVertical: 11,
    paddingHorizontal: 16,
    borderRadius: 999,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    marginRight: 8
  },
  tabActive: {
    backgroundColor: "#111827",
    borderColor: "#111827"
  },
  tabText: {
    color: "#374151",
    fontWeight: "800"
  },
  tabTextActive: {
    color: "#ffffff"
  },
  metricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginBottom: 8
  },
  metric: {
    flexGrow: 1,
    flexBasis: "47%",
    padding: 16,
    borderRadius: 16,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb"
  },
  metricDanger: {
    backgroundColor: "#fff7ed"
  },
  metricSuccess: {
    backgroundColor: "#ecfdf5"
  },
  metricLabel: {
    color: "#64748b",
    fontWeight: "800",
    marginBottom: 8
  },
  metricValue: {
    color: "#111827",
    fontSize: 21,
    fontWeight: "900"
  },
  section: {
    padding: 16,
    borderRadius: 16,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    marginTop: 12
  },
  sectionTitle: {
    color: "#111827",
    fontSize: 18,
    fontWeight: "900",
    marginBottom: 14
  },
  bodyText: {
    color: "#1f2937",
    fontSize: 15,
    fontWeight: "600"
  },
  muted: {
    color: "#64748b",
    fontSize: 14,
    lineHeight: 20
  },
  input: {
    minHeight: 48,
    color: "#111827",
    backgroundColor: "#f8fafc",
    borderWidth: 1,
    borderColor: "#d1d5db",
    borderRadius: 13,
    paddingHorizontal: 14,
    marginBottom: 12,
    fontSize: 16
  },
  label: {
    color: "#111827",
    fontWeight: "800",
    marginBottom: 8
  },
  primaryButton: {
    minHeight: 50,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 14,
    backgroundColor: "#0f766e",
    marginTop: 4
  },
  primaryButtonText: {
    color: "#ffffff",
    fontWeight: "900",
    fontSize: 16
  },
  secondaryButton: {
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 14,
    backgroundColor: "#ccfbf1",
    marginBottom: 10
  },
  secondaryButtonText: {
    color: "#115e59",
    fontWeight: "900"
  },
  chipGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 12
  },
  chip: {
    paddingVertical: 9,
    paddingHorizontal: 12,
    borderRadius: 999,
    backgroundColor: "#f1f5f9",
    borderWidth: 1,
    borderColor: "#e2e8f0"
  },
  chipActive: {
    backgroundColor: "#111827",
    borderColor: "#111827"
  },
  chipText: {
    color: "#334155",
    fontWeight: "800"
  },
  chipTextActive: {
    color: "#ffffff"
  },
  record: {
    padding: 14,
    borderRadius: 16,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    marginBottom: 10
  },
  row: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 12,
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#e5e7eb"
  },
  rowText: {
    flex: 1
  },
  rowValue: {
    color: "#111827",
    fontWeight: "900"
  },
  recordTitle: {
    color: "#111827",
    fontWeight: "900",
    fontSize: 15,
    lineHeight: 21
  },
  recordValue: {
    color: "#0f766e",
    fontWeight: "900"
  },
  actions: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 12
  },
  smallButton: {
    flexGrow: 1,
    minHeight: 42,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 12,
    backgroundColor: "#e0f2fe",
    paddingHorizontal: 12
  },
  smallButtonActive: {
    backgroundColor: "#bae6fd"
  },
  smallButtonText: {
    color: "#075985",
    fontWeight: "900"
  },
  dangerButton: {
    backgroundColor: "#fee2e2"
  },
  dangerButtonText: {
    color: "#991b1b",
    fontWeight: "900"
  },
  editBox: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb"
  },
  empty: {
    padding: 22,
    borderRadius: 16,
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e5e7eb"
  },
  emptyTitle: {
    color: "#111827",
    fontSize: 18,
    fontWeight: "900",
    marginBottom: 6
  }
});
