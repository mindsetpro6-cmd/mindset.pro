import sqlite3
from pathlib import Path
import hashlib

BASE_DIR = Path(__file__).resolve().parent
DATABASE_FILE = BASE_DIR / "mindset.db"


def conectar():
    return sqlite3.connect(DATABASE_FILE)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilizadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'ALUNO',
            classe TEXT,
            disciplina TEXT,
            ativo INTEGER NOT NULL DEFAULT 1,
            email_confirmado INTEGER NOT NULL DEFAULT 0,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def criar_utilizador(
    nome,
    email,
    password,
    tipo="ALUNO",
    classe=None,
    disciplina=None,
    email_confirmado=False
):
    criar_tabelas()

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO utilizadores (
                nome,
                email,
                password_hash,
                tipo,
                classe,
                disciplina,
                email_confirmado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            nome.strip(),
            email.strip().lower(),
            hash_password(password),
            tipo,
            classe,
            disciplina,
            1 if email_confirmado else 0
        ))

        conn.commit()
        return cursor.lastrowid

    except sqlite3.IntegrityError:
        return None

    finally:
        conn.close()


def obter_utilizador_por_email(email):
    criar_tabelas()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            nome,
            email,
            tipo,
            classe,
            disciplina,
            ativo,
            email_confirmado,
            criado_em
        FROM utilizadores
        WHERE email = ?
    """, (
        email.strip().lower(),
    ))

    utilizador = cursor.fetchone()
    conn.close()

    if not utilizador:
        return None

    return {
        "id": utilizador[0],
        "nome": utilizador[1],
        "email": utilizador[2],
        "tipo": utilizador[3],
        "classe": utilizador[4],
        "disciplina": utilizador[5],
        "ativo": utilizador[6],
        "email_confirmado": utilizador[7],
        "criado_em": utilizador[8]
    }


def autenticar_utilizador(email, password):
    criar_tabelas()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            nome,
            email,
            tipo,
            classe,
            disciplina,
            ativo,
            email_confirmado,
            criado_em
        FROM utilizadores
        WHERE email = ?
        AND password_hash = ?
        AND ativo = 1
    """, (
        email.strip().lower(),
        hash_password(password)
    ))

    utilizador = cursor.fetchone()
    conn.close()

    if not utilizador:
        return None

    return {
        "id": utilizador[0],
        "nome": utilizador[1],
        "email": utilizador[2],
        "tipo": utilizador[3],
        "classe": utilizador[4],
        "disciplina": utilizador[5],
        "ativo": utilizador[6],
        "email_confirmado": utilizador[7],
        "criado_em": utilizador[8]
    }


def confirmar_email(email):
    criar_tabelas()

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE utilizadores
        SET email_confirmado = 1
        WHERE email = ?
    """, (
        email.strip().lower(),
    ))

    conn.commit()
    alterados = cursor.rowcount
    conn.close()

    return alterados > 0


if __name__ == "__main__":
    criar_tabelas()
    print("BASE DE DADOS MINDSET PRO CRIADA COM SUCESSO")
    print(DATABASE_FILE)
