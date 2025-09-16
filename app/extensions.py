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
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

from flask import current_app
DB_URI = "postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"
pool = ConnectionPool(DB_URI, open=True, max_size=5,kwargs={"prepare_threshold": 0, "row_factory": dict_row, 'autocommit':True})
@contextmanager
def graph_context():
    from app.agent_call.graph import builder # adjust imports
    # conn = psycopg.connect(db_uri, autocommit=True,prepare_threshold=0)
    with pool.connection() as conn:
        # with conn.cursor() as cur:
        #     cur.execute("DEALLOCATE ALL;")
        checkpointer = PostgresSaver(conn)
        graph = builder.compile(checkpointer=checkpointer)
        yield graph
    # try:
    #     checkpointer = PostgresSaver(conn)
    #     graph = builder.compile(checkpointer=checkpointer)
    #     print('Started')
    #     yield graph
    # finally:
    #     conn.close()
    #     print('Closed')
