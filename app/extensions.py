# # app/extensions.py
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg
from app.agent_call.graph import builder
DB_URI = "postgresql://git_agent_db_xocq_user:HRsa5HU2jL4y52lml80ZsmvG6dsjhlBF@dpg-d2r9j86r433s73fbnoa0-a.oregon-postgres.render.com/git_agent_db_xocq?sslmode=require"

from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

pool = ConnectionPool(DB_URI)

def make_saver():
    conn = pool.connection()
    return PostgresSaver(conn)

# then inside your code:

from contextlib import contextmanager
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

# global pool
# pool = ConnectionPool("postgresql://user:pass@localhost/dbname")
pool = ConnectionPool("postgresql://git_agent_db_xocq_user:HRsa5HU2jL4y52lml80ZsmvG6dsjhlBF@dpg-d2r9j86r433s73fbnoa0-a.oregon-postgres.render.com/git_agent_db_xocq?sslmode=require", min_size=1, max_size=5)
@contextmanager
def graph_context():
    with pool.connection() as conn:
        saver = PostgresSaver(conn)
        graph = builder.compile(checkpointer=saver)
        yield graph
