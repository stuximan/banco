from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import re

app = Flask(__name__)
CORS(app)
DATABASE = "individuos.db"

# ---------------------------
# Função para conexão
# ---------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------
# Criar tabela (1ª execução)
# ---------------------------
def criar_tabela():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS individuos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            saldo REAL NOT NULL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

# ---------------------------
# Função para validar CPF
# ---------------------------
def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i + 1) - num) for num in range(i))
        digito = ((soma * 10) % 11) % 10
        if digito != int(cpf[i]):
            return False

    return True

# ---------------------------
# GET - listar individuos
# ---------------------------
@app.route("/individuos", methods=["GET"])
def listar_individuos():
    conn = get_db_connection()
    individuos = conn.execute("SELECT * FROM individuos").fetchall()
    conn.close()
    return jsonify([dict(i) for i in individuos])

# ---------------------------
# GET - buscar individuo por id
# ---------------------------
@app.route("/individuos/<int:id>", methods=["GET"])
def buscar_individuo(id):
    conn = get_db_connection()
    individuo = conn.execute(
        "SELECT * FROM individuos WHERE id = ?", (id,)
    ).fetchone()
    conn.close()

    if individuo is None:
        return jsonify({"erro": "Individuo não encontrado"}), 404

    return jsonify(dict(individuo))

# ---------------------------
# POST - cadastrar individuo
# ---------------------------
@app.route("/individuos", methods=["POST"])
def cadastrar_individuo():
    dados = request.get_json(silent=True)

    if not dados:
        return jsonify({"erro": "JSON inválido"}), 400

    nome = dados.get("nome")
    cpf = dados.get("cpf")

    if not nome or not cpf:
        return jsonify({"erro": "Nome e CPF são obrigatórios"}), 400

    if not validar_cpf(cpf):
        return jsonify({"erro": "CPF inválido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO individuos (nome, cpf) VALUES (?, ?)",
            (nome, cpf)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"erro": "CPF já cadastrado"}), 409

    conn.close()

    return jsonify({
        "mensagem": "Indivíduo cadastrado com sucesso",
        "nome": nome,
        "cpf": cpf,
        "saldo": 0
    }), 201

# ---------------------------
# PUT - atualizar individuo
# ---------------------------
@app.route("/individuos/<int:id>", methods=["PUT"])
def atualizar_individuo(id):
    dados = request.get_json(silent=True)

    if not dados:
        return jsonify({"erro": "JSON inválido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    individuo = cursor.execute(
        "SELECT * FROM individuos WHERE id = ?", (id,)
    ).fetchone()

    if individuo is None:
        conn.close()
        return jsonify({"erro": "Individuo não encontrado"}), 404

    nome = dados.get("nome", individuo["nome"])
    cpf = dados.get("cpf", individuo["cpf"])

    if cpf != individuo["cpf"] and not validar_cpf(cpf):
        conn.close()
        return jsonify({"erro": "CPF inválido"}), 400

    try:
        cursor.execute(
            "UPDATE individuos SET nome = ?, cpf = ? WHERE id = ?",
            (nome, cpf, id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"erro": "CPF já cadastrado"}), 409

    conn.close()

    return jsonify({
        "id": id,
        "nome": nome,
        "cpf": cpf,
        "saldo": individuo["saldo"]
    })

# ---------------------------
# PUT - depósito
# ---------------------------
@app.route("/individuos/<int:id>/deposito", methods=["PUT"])
def depositar(id):
    dados = request.get_json(silent=True)

    if not dados or "valor" not in dados:
        return jsonify({"erro": "Valor é obrigatório"}), 400

    valor = dados["valor"]

    if not isinstance(valor, (int, float)) or valor <= 0:
        return jsonify({"erro": "Valor de depósito inválido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    individuo = cursor.execute(
        "SELECT * FROM individuos WHERE id = ?", (id,)
    ).fetchone()

    if individuo is None:
        conn.close()
        return jsonify({"erro": "Individuo não encontrado"}), 404

    novo_saldo = individuo["saldo"] + valor

    cursor.execute(
        "UPDATE individuos SET saldo = ? WHERE id = ?",
        (novo_saldo, id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "mensagem": "Depósito realizado com sucesso",
        "saldo_atual": novo_saldo
    })

# ---------------------------
# PUT - saque
# ---------------------------
@app.route("/individuos/<int:id>/saque", methods=["PUT"])
def sacar(id):
    dados = request.get_json(silent=True)

    if not dados or "valor" not in dados:
        return jsonify({"erro": "Valor é obrigatório"}), 400

    valor = dados["valor"]

    if not isinstance(valor, (int, float)) or valor <= 0:
        return jsonify({"erro": "Valor de saque inválido"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    individuo = cursor.execute(
        "SELECT * FROM individuos WHERE id = ?", (id,)
    ).fetchone()

    if individuo is None:
        conn.close()
        return jsonify({"erro": "Individuo não encontrado"}), 404

    if valor > individuo["saldo"]:
        conn.close()
        return jsonify({"erro": "Saldo insuficiente"}), 400

    novo_saldo = individuo["saldo"] - valor

    cursor.execute(
        "UPDATE individuos SET saldo = ? WHERE id = ?",
        (novo_saldo, id)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "mensagem": "Saque realizado com sucesso",
        "saldo_atual": novo_saldo
    })

# ---------------------------
# Inicialização
# ---------------------------
if __name__ == "__main__":
    criar_tabela()
    app.run(debug=True)
