# app/extensions.py
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg

DB_URI = "postgresql://git_agent_db_user:Jg8FAmsZRmRNWPsSowBFfNTCD40bwQ4S@dpg-d2q621f5r7bs73abgs6g-a.oregon-postgres.render.com/git_agent_db?sslmode=require"
conn = psycopg.connect(DB_URI)

checkpointer = PostgresSaver(conn)
checkpointer.setup()  # make sure schema exists
