from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)
database = "usuarios.db"

def get_db_connection():
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabela():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome VALID TEXT,
            idade INTEGER NOT NULL,
            cpf   INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()

    print("portfólio criado com sucesso!")

    def inserir_novo_usuario():

        conn = get_db_connection()
        cursor = conn.cursor()

        nome = input("digite o nome de usuario:")
        idade = int(input("digite a idade do usuario:"))
        cpf = int(input("digite o codigo de pessoa fisica do usuario"))

        cursor.execute("""
        INSERT INTO USUARIOS (NOME,IDADE,CPF)VALUES (?, ?)
        """,(nome,idade,cpf))
        conn.commit()
        conn.close()

        print("dados inseridos com sucesso!")

    def listar_usuarios():

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM usuarios")
        usuarios = cursor.fetchall()

        for usuario in usuarios:
         print(f"ID: {usuario[0]} | NOME: {usuario[1]} | IDADE: {usuario[2]} | CPF: {usuario[3]}")

        conn.close()
