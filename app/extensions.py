# app/extensions.py
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg
from psycopg_pool import ConnectionPool

DB_URI = "postgresql://git_agent_db_xocq_user:HRsa5HU2jL4y52lml80ZsmvG6dsjhlBF@dpg-d2r9j86r433s73fbnoa0-a.oregon-postgres.render.com/git_agent_db_xocq?sslmode=require"
pool = ConnectionPool(DB_URI, min_size=1, max_size=5, max_lifetime=1800)

conn = pool.connection()
checkpointer = PostgresSaver(conn)
# checkpointer.setup()  # make sure schema exists
