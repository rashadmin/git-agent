# # app/extensions.py
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg

DB_URI = "postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M@aws-1-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require"
# conn = psycopg.connect(DB_URI,autocommit=True)
# def connect():
#     return psycopg.connect(DB_URI, autocommit=True)

# checkpointer = PostgresSaver(connect)
# # checkpointer = PostgresSaver(conn)
# checkpointer.setup()  # make sure schema exists
# app/extensions.py
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg
from contextlib import contextmanager

DB_URI = (
    "postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M"
    "@aws-1-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require"
)

# --- Patch: fake pipeline for PgBouncer ---
@contextmanager
def fake_pipeline(conn):
    # Just yield the connection instead of opening a pipeline
    yield conn

# Monkey patch psycopg Connection objects
psycopg.Connection.pipeline = fake_pipeline

# # --- Create checkpointer with autocommit ---
# def connect():
#     return psycopg.connect(DB_URI, autocommit=True)
conn = psycopg.connect(DB_URI, autocommit=True)

# --- Pass the connection to PostgresSaver ---
checkpointer = PostgresSaver(conn)
# checkpointer = PostgresSaver(connect)

