# create_db.py
import os
import getpass
import sqlite3
from datetime import datetime
import hashlib, os as _os, binascii

DB_PATH = os.path.join("data", "estoque.db")

def ensure_data_dir():
    os.makedirs("data", exist_ok=True)

def hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = _os.urandom(16)
    pwd = password.encode("utf-8")
    dk = hashlib.pbkdf2_hmac("sha256", pwd, salt, 200_000)
    return binascii.hexlify(dk).decode(), binascii.hexlify(salt).decode()

def create_tables(conn):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        created_by INTEGER,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(created_by) REFERENCES users(id)
    );
    """)
    conn.commit()

def create_admin(conn, username, password):
    cur = conn.cursor()
    pwd_hash, salt = hash_password(password)
    try:
        cur.execute("INSERT INTO users (username, password_hash, salt, role, created_at) VALUES (?, ?, ?, ?, ?)",
                    (username, pwd_hash, salt, "admin", datetime.utcnow().isoformat()))
        conn.commit()
        print(f"Usuário admin '{username}' criado com sucesso.")
    except sqlite3.IntegrityError:
        print(f"Usuário '{username}' já existe — não foi criado.")

def main():
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    print("=== Criação do usuário administrador ===")
    username = input("Nome do admin (ex: admin): ").strip()
    while not username:
        username = input("Nome do admin (não vazio): ").strip()
    # usar getpass para não mostrar senha
    password = getpass.getpass("Senha do admin: ").strip()
    password2 = getpass.getpass("Confirme a senha: ").strip()
    if password != password2:
        print("Senhas não conferem. Rode o script novamente.")
        return
    create_admin(conn, username, password)
    conn.close()

if __name__ == "__main__":
    main()
