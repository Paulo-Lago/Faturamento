import os
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_DAYS = 30
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
    "⚙️ Outros",
]


def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


def get_engine():
    database_url = get_required_env("DATABASE_URL")
    return create_engine(database_url, pool_pre_ping=True)


engine = get_engine()


def data_atual_brasilia():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3))).date()


def json_error(message, status_code=400):
    return JSONResponse({"error": message}, status_code=status_code)


async def read_json(request):
    try:
        return await request.json()
    except Exception:
        return {}


def gerar_token(username):
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS),
    }
    return jwt.encode(payload, get_required_env("JWT_SECRET"), algorithm=JWT_ALGORITHM)


def validar_token(request):
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, get_required_env("JWT_SECRET"), algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except jwt.PyJWTError:
        return None


def row_to_dict(row):
    data = dict(row._mapping)
    for key, value in list(data.items()):
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
    return data


def fetch_all(query, params=None):
    with engine.begin() as conn:
        return [row_to_dict(row) for row in conn.execute(text(query), params or {})]


def execute(query, params=None):
    with engine.begin() as conn:
        result = conn.execute(text(query), params or {})
        return result.rowcount


async def health(_request):
    return JSONResponse({"ok": True, "date": data_atual_brasilia().isoformat()})


async def config(_request):
    return JSONResponse({"servicos": LISTA_SERVICOS})


async def login(request):
    body = await read_json(request)
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))
    if not username or not password:
        return json_error("Informe usuário e senha.")

    try:
        rows = fetch_all("SELECT password FROM usuarios WHERE username = :u", {"u": username})
    except SQLAlchemyError:
        return json_error("Não foi possível conectar ao banco.", 500)

    if not rows or str(rows[0]["password"]) != password:
        return json_error("Usuário ou senha inválidos.", 401)

    return JSONResponse({"token": gerar_token(username), "username": username})


async def signup(request):
    body = await read_json(request)
    username = str(body.get("username", "")).strip()
    password = str(body.get("password", ""))
    if not username or not password:
        return json_error("Preencha usuário e senha.")

    rows = fetch_all("SELECT username FROM usuarios WHERE username = :u", {"u": username})
    if rows:
        return json_error("Esse usuário já está cadastrado.", 409)

    execute(
        "INSERT INTO usuarios (username, password) VALUES (:u, :p)",
        {"u": username, "p": password},
    )
    return JSONResponse({"token": gerar_token(username), "username": username}, status_code=201)


def require_user(request):
    username = validar_token(request)
    if not username:
        return None, json_error("Sessão expirada. Faça login novamente.", 401)
    return username, None


async def dashboard(request):
    username, error = require_user(request)
    if error:
        return error

    hoje = data_atual_brasilia()
    inicio_mes = hoje.replace(day=1)
    rows = fetch_all(
        "SELECT data, valor FROM servicos WHERE username = :u",
        {"u": username},
    )
    fat_dia = sum(float(row["valor"] or 0) for row in rows if str(row["data"])[:10] == hoje.isoformat())
    fat_mes = sum(float(row["valor"] or 0) for row in rows if str(row["data"])[:10] >= inicio_mes.isoformat())
    return JSONResponse({"faturamentoHoje": fat_dia, "faturamentoMes": fat_mes})


async def list_services(request):
    username, error = require_user(request)
    if error:
        return error

    rows = fetch_all(
        "SELECT id, data, categoria, descricao, valor FROM servicos WHERE username = :u ORDER BY data DESC, id DESC",
        {"u": username},
    )
    return JSONResponse({"items": rows})


async def create_service(request):
    username, error = require_user(request)
    if error:
        return error

    body = await read_json(request)
    categorias = body.get("categorias") or []
    valor = float(body.get("valor") or 0)
    if not categorias or valor <= 0:
        return json_error("Selecione serviço/produto e informe um valor positivo.")

    data = body.get("data") or data_atual_brasilia().isoformat()
    descricao = str(body.get("descricao", "")).strip()
    execute(
        "INSERT INTO servicos (username, data, categoria, descricao, valor) VALUES (:u, :d, :c, :de, :v)",
        {"u": username, "d": data, "c": " + ".join(categorias), "de": descricao, "v": valor},
    )
    return JSONResponse({"ok": True}, status_code=201)


async def update_service(request):
    username, error = require_user(request)
    if error:
        return error

    service_id = request.path_params["service_id"]
    body = await read_json(request)
    categorias = body.get("categorias") or []
    valor = float(body.get("valor") or 0)
    if not categorias or valor <= 0:
        return json_error("Selecione serviço/produto e informe um valor positivo.")

    execute(
        """UPDATE servicos SET data = :d, categoria = :c, descricao = :de, valor = :v
           WHERE id = :id AND username = :u""",
        {
            "d": body.get("data") or data_atual_brasilia().isoformat(),
            "c": " + ".join(categorias),
            "de": str(body.get("descricao", "")).strip(),
            "v": valor,
            "id": service_id,
            "u": username,
        },
    )
    return JSONResponse({"ok": True})


async def delete_service(request):
    username, error = require_user(request)
    if error:
        return error

    execute(
        "DELETE FROM servicos WHERE id = :id AND username = :u",
        {"id": request.path_params["service_id"], "u": username},
    )
    return JSONResponse({"ok": True})


async def list_expense_types(request):
    username, error = require_user(request)
    if error:
        return error

    rows = fetch_all(
        "SELECT id, nome FROM tipos_despesa WHERE username = :u ORDER BY nome",
        {"u": username},
    )
    return JSONResponse({"items": rows})


async def create_expense_type(request):
    username, error = require_user(request)
    if error:
        return error

    body = await read_json(request)
    nome = str(body.get("nome", "")).strip()
    if not nome:
        return json_error("Informe o nome do tipo de despesa.")

    execute(
        "INSERT INTO tipos_despesa (username, nome) VALUES (:u, :n)",
        {"u": username, "n": nome},
    )
    return JSONResponse({"ok": True}, status_code=201)


async def update_expense_type(request):
    username, error = require_user(request)
    if error:
        return error

    body = await read_json(request)
    nome = str(body.get("nome", "")).strip()
    if not nome:
        return json_error("Informe o nome do tipo de despesa.")

    execute(
        "UPDATE tipos_despesa SET nome = :n WHERE id = :id AND username = :u",
        {"n": nome, "id": request.path_params["type_id"], "u": username},
    )
    return JSONResponse({"ok": True})


async def delete_expense_type(request):
    username, error = require_user(request)
    if error:
        return error

    type_id = request.path_params["type_id"]
    linked = fetch_all(
        "SELECT COUNT(*) AS total FROM despesas WHERE username = :u AND tipo_id = :id",
        {"u": username, "id": type_id},
    )
    if linked and int(linked[0]["total"] or 0) > 0:
        return json_error("Esse tipo possui despesas vinculadas e não pode ser excluído.", 409)

    execute(
        "DELETE FROM tipos_despesa WHERE id = :id AND username = :u",
        {"id": type_id, "u": username},
    )
    return JSONResponse({"ok": True})


async def list_expenses(request):
    username, error = require_user(request)
    if error:
        return error

    rows = fetch_all(
        """SELECT d.id, d.data, d.tipo_id, d.descricao, d.valor, t.nome AS tipo_nome
           FROM despesas d
           LEFT JOIN tipos_despesa t ON d.tipo_id = t.id
           WHERE d.username = :u
           ORDER BY d.data DESC, d.id DESC""",
        {"u": username},
    )
    return JSONResponse({"items": rows})


async def create_expense(request):
    username, error = require_user(request)
    if error:
        return error

    body = await read_json(request)
    valor = float(body.get("valor") or 0)
    tipo_id = body.get("tipo_id")
    if not tipo_id or valor <= 0:
        return json_error("Informe tipo de despesa e valor positivo.")

    execute(
        """INSERT INTO despesas (username, data, tipo_id, descricao, valor)
           VALUES (:u, :d, :t, :de, :v)""",
        {
            "u": username,
            "d": body.get("data") or data_atual_brasilia().isoformat(),
            "t": tipo_id,
            "de": str(body.get("descricao", "")).strip(),
            "v": valor,
        },
    )
    return JSONResponse({"ok": True}, status_code=201)


async def update_expense(request):
    username, error = require_user(request)
    if error:
        return error

    body = await read_json(request)
    valor = float(body.get("valor") or 0)
    tipo_id = body.get("tipo_id")
    if not tipo_id or valor <= 0:
        return json_error("Informe tipo de despesa e valor positivo.")

    execute(
        """UPDATE despesas SET data = :d, tipo_id = :t, descricao = :de, valor = :v
           WHERE id = :id AND username = :u""",
        {
            "d": body.get("data") or data_atual_brasilia().isoformat(),
            "t": tipo_id,
            "de": str(body.get("descricao", "")).strip(),
            "v": valor,
            "id": request.path_params["expense_id"],
            "u": username,
        },
    )
    return JSONResponse({"ok": True})


async def delete_expense(request):
    username, error = require_user(request)
    if error:
        return error

    execute(
        "DELETE FROM despesas WHERE id = :id AND username = :u",
        {"id": request.path_params["expense_id"], "u": username},
    )
    return JSONResponse({"ok": True})


async def credits(request):
    username, error = require_user(request)
    if error:
        return error

    rows = fetch_all(
        "SELECT id, cliente, tipo, valor, data FROM creditos WHERE username = :u ORDER BY data DESC, id DESC",
        {"u": username},
    )
    saldos = {}
    for row in rows:
        cliente = row.get("cliente") or "Sem cliente"
        valor = float(row.get("valor") or 0)
        saldos[cliente] = saldos.get(cliente, 0) + (valor if row.get("tipo") == "Crédito" else -valor)
    return JSONResponse({"items": rows, "saldos": saldos})


async def create_credit(request):
    username, error = require_user(request)
    if error:
        return error

    body = await read_json(request)
    cliente = str(body.get("cliente", "")).strip()
    tipo = body.get("tipo")
    valor = float(body.get("valor") or 0)
    if not cliente or tipo not in {"Crédito", "Débito"} or valor <= 0:
        return json_error("Informe cliente, tipo e valor positivo.")

    execute(
        "INSERT INTO creditos (username, cliente, tipo, valor, data) VALUES (:u, :c, :t, :v, :d)",
        {"u": username, "c": cliente, "t": tipo, "v": valor, "d": data_atual_brasilia().isoformat()},
    )
    return JSONResponse({"ok": True}, status_code=201)


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/config", config, methods=["GET"]),
    Route("/auth/login", login, methods=["POST"]),
    Route("/auth/signup", signup, methods=["POST"]),
    Route("/dashboard", dashboard, methods=["GET"]),
    Route("/services", list_services, methods=["GET"]),
    Route("/services", create_service, methods=["POST"]),
    Route("/services/{service_id:int}", update_service, methods=["PUT"]),
    Route("/services/{service_id:int}", delete_service, methods=["DELETE"]),
    Route("/expense-types", list_expense_types, methods=["GET"]),
    Route("/expense-types", create_expense_type, methods=["POST"]),
    Route("/expense-types/{type_id:int}", update_expense_type, methods=["PUT"]),
    Route("/expense-types/{type_id:int}", delete_expense_type, methods=["DELETE"]),
    Route("/expenses", list_expenses, methods=["GET"]),
    Route("/expenses", create_expense, methods=["POST"]),
    Route("/expenses/{expense_id:int}", update_expense, methods=["PUT"]),
    Route("/expenses/{expense_id:int}", delete_expense, methods=["DELETE"]),
    Route("/credits", credits, methods=["GET"]),
    Route("/credits", create_credit, methods=["POST"]),
]

app = Starlette(debug=False, routes=routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("MOBILE_ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
