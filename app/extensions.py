# app/extensions.py
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://git_agent_db_user:Jg8FAmsZRmRNWPsSowBFfNTCD40bwQ4S@dpg-d2q621f5r7bs73abgs6g-a.oregon-postgres.render.com/git_agent_db?sslmode=require"

checkpointer = PostgresSaver.from_conn_string(DB_URI)
checkpointer.setup()  # make sure schema exists
