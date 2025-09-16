# # app/extensions.py
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg

# DB_URI = "postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M@aws-1-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require"
# conn = psycopg.connect(DB_URI,autocommit=True)
# def connect():
#     return psycopg.connect(DB_URI, autocommit=True)

# checkpointer = PostgresSaver(connect)
# checkpointer = PostgresSaver(conn)
# checkpointer.setup()  # make sure schema exists
# app/extensions.py
import psycopg
from contextlib import contextmanager
from app.agent_call.graph import builder # adjust imports

@contextmanager
def graph_context(db_uri: str):
    conn = psycopg.connect(db_uri, autocommit=True)
    try:
        checkpointer = PostgresSaver(conn)
        graph = builder.compile(checkpointer=checkpointer)
        print('Started')
        yield graph
    finally:
        conn.close()
        print('Closed')
