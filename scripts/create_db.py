"""
Create PostgreSQL database from .env values.
Usage (from project root, venv active):

    python scripts/create_db.py
"""

from pathlib import Path

import environ
import psycopg
from psycopg import sql

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

db_name = env("DB_NAME")
db_user = env("DB_USER")
db_password = env("DB_PASSWORD")
db_host = env("DB_HOST", default="localhost")
db_port = env("DB_PORT", default="5432")

if not db_password:
    raise SystemExit(
        "DB_PASSWORD kosong di .env. Isi password PostgreSQL kamu, lalu jalankan lagi."
    )

with psycopg.connect(
    host=db_host,
    port=db_port,
    user=db_user,
    password=db_password,
    dbname="postgres",
    autocommit=True,
) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone()
        if exists:
            print(f"Database '{db_name}' sudah ada.")
        else:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            print(f"Database '{db_name}' berhasil dibuat.")
