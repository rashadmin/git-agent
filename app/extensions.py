# # app/extensions.py
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg

# DB_URI = "postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M@aws-1-eu-north-1.pooler.supabase.com:5432/postgres?sslmode=require"
# conn = psycopg.connect(DB_URI,autocommit=True)
# def connect():
#     return 
# psycopg.connect(DB_URI, autocommit=True)

# checkpointer = PostgresSaver(connect)
# checkpointer = PostgresSaver(conn)
# checkpointer.setup()  # make sure schema exists
# app/extensions.py
import psycopg
from contextlib import contextmanager
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
import logging

logging.basicConfig(level=logging.INFO)
from flask import current_app
DB_URI = "postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"
pool = ConnectionPool(DB_URI, open=True,max_idle=60,max_lifetime=300,max_size=15,kwargs={"prepare_threshold": None, "row_factory": dict_row, 'autocommit':True})

@contextmanager
def graph_context():
    logging.info("[POOL] Waiting for connection...")
    from app.agent_call.graph import builder
    with pool.connection() as conn:
        logging.info(f"[POOL] acquired conn={id(conn)}")
        logging.info(f"[POOL] open={pool.open} used={pool.used} available={pool.available} max_size={pool.max_size}")

        try:
            conn.prepare_threshold = None
            checkpointer = PostgresSaver(conn)
            graph = builder.compile(checkpointer=checkpointer)
            yield graph
        finally:
            logging.info(f"[POOL] open={pool.open} used={pool.used} available={pool.available} max_size={pool.max_size}")

            logging.info(f"[POOL] released conn={id(conn)}")

    # try:
    #     checkpointer = PostgresSaver(conn)
    #     graph = builder.compile(checkpointer=checkpointer)
    #     print('Started')
    #     yield graph
    # finally:
    #     conn.close()
    #     print('Closed')
