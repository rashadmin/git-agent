# app/extensions.py
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg

DB_URI = "postgresql://git_agent_db_xocq_user:HRsa5HU2jL4y52lml80ZsmvG6dsjhlBF@dpg-d2r9j86r433s73fbnoa0-a.oregon-postgres.render.com/git_agent_db_xocq?sslmode=require"
conn = psycopg.connect(DB_URI,autocommit=True)

checkpointer = PostgresSaver(conn)
# checkpointer.setup()  # make sure schema exists
