import sys
# ...
import logging
from flask import current_app
from langgraph.checkpoint.postgres import PostgresSaver
logging.basicConfig(level=logging.INFO)
def extract_commits(data):
    try:
        thread_id = data['repository']['full_name'].encode("utf-8").hex()
        username = data["repository"]["full_name"].split('/')[0]
        # DB_URI = current_app.config['SQLALCHEMY_DATABASE_URI']
        from app.agent_call.graph import builder
        from app.extensions import pool
        logging.info('Started')
        with pool.connection() as connect:
            checkpointer = PostgresSaver(connect)
            graph = builder.compile(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": thread_id}}
            graph.invoke({'commits':data,'user_id':username},config=config)
    except:
        logging.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        logging.info('Commit Extracted Completely')
