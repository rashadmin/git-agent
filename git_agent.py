from app import create_app,db
from app.models import User,Post,Task
from app.agent_call.composer import run_compose
from app.agent_call.graph import builder
from flask import current_app
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg
app = create_app()
DB_URI = app.config['SQLALCHEMY_DATABASE_URI']

import pandas as pd


@app.shell_context_processor
def make_shell_context():
    conn = psycopg.connect(DB_URI, autocommit=True)
    
    checkpointer = PostgresSaver(conn)
    graph = builder.compile(checkpointer=checkpointer)
    return {'graph':graph,'user':User,'post':Post,'run':run_compose,'task':Task}



