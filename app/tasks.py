import sys
from app import db
import logging
from flask import current_app
from langgraph.checkpoint.postgres import PostgresSaver
logging.basicConfig(level=logging.INFO)
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from psycopg.errors import OperationalError, DatabaseError
from app.agent_call.external import format_github_request,get_all_commits
import pandas as pd
import datetime
@retry(
    retry=retry_if_exception_type((OperationalError, DatabaseError)),
    stop=stop_after_attempt(3),    # retry up to 3 times
    wait=wait_fixed(2),            # wait 2s between retries
    reraise=True
)
def extract_commits(data):
    formatted = get_all_commits(data)
    print('It is formatting')
    # print(formatted)
    formatted = [item for sublist in formatted for item in sublist]
    df = pd.DataFrame().from_records(formatted)
    df['commit_date'] = pd.to_datetime(df['commit_date'])
    today = pd.Timestamp.today().normalize()
    filtered_df = df[~(df['commit_date'].dt.normalize() == today)]
    filtered_df['dayofyear'] = filtered_df['commit_date'].dt.dayofyear.astype(str)
    filtered_df['year'] = filtered_df['commit_date'].dt.year.astype(str)
    filtered_df['day'] = filtered_df['year']+'-'+filtered_df['dayofyear']
    filtered_df.drop(['dayofyear','year'],axis=1,inplace=True)
    days = filtered_df['day'].unique()
    for day in days:
        temp_df = filtered_df[filtered_df['day']==day]
        try:
            thread_id = data['repository']['full_name'].encode("utf-8").hex()
            username = data["repository"]["full_name"].split('/')[0]
            # DB_URI = current_app.config['SQLALCHEMY_DATABASE_URI']
            from app.agent_call.graph import builder
            from app.extensions import pool
            logging.info('Started')
            with pool.connection() as conn:
                checkpointer = PostgresSaver(conn)
                graph = builder.compile(checkpointer=checkpointer)
                config = {"configurable": {"thread_id": thread_id}}
                graph.invoke({'repo':data['repository']['full_name'],'formatted_commits':temp_df.to_dict(orient='records'),'day':day},config=config)
        except:
            current_app.logger.error("DB connection lost, resetting session...", exc_info=True)
            # throw away dead session
            db.session.remove()
            # also clear engine pool (forces new connections next time)
            db.engine.dispose()
            logging.error('Unhandled exception', exc_info=sys.exc_info())

        finally:
            logging.info('Commit Extracted Completely')
