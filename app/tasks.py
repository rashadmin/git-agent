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
from app.extensions import run_graph
import datetime
import time
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
    today = datetime.date.today().strftime("%Y-%m-%d")
    filtered_df = df[~(df['commit_date'].dt.normalize() == today)]
    filtered_df.loc[:,'dayofyear'] = filtered_df['commit_date'].dt.dayofyear.astype(str)
    filtered_df.loc[:,'year'] = filtered_df['commit_date'].dt.year.astype(str)
    filtered_df.loc[:,'day'] = filtered_df['year']+'-'+filtered_df['dayofyear']
    filtered_df.drop(['dayofyear','year'],axis=1,inplace=True)
    days = sorted(filtered_df['day'].unique())
    logging.info(f'Dates :{days}')
    for day in days:
        temp_df = filtered_df[filtered_df['day'] == day]
        max_retries = 3  # how many times you want to retry
        attempt = 0
        success = False

        while attempt < max_retries and not success:
            try:
                thread_id = data['repository']['full_name'].encode("utf-8").hex()
                username = data["repository"]["full_name"].split('/')[0]
                from app.extensions import graph_context

                with graph_context() as graph:
                    config = {"configurable": {"thread_id": thread_id}}
                    graph_data = {
                            'repo': data['repository']['full_name'],
                            'formatted_commits': temp_df.to_dict(orient='records'),
                            'day': day
                        }
                    run_graph(graph, graph_data, config)
                success = True  # ✅ success, break the retry loop

            except Exception as e:
                attempt += 1
                current_app.logger.error(f"Error on day {day}, attempt {attempt}: {e}", exc_info=True)
                db.session.remove()
                db.engine.dispose()

                if attempt < max_retries:
                    logging.info(f"Retrying day {day} (attempt {attempt + 1})...")
                    time.sleep(2)  # optional delay before retry
                else:
                    logging.error(f"Failed permanently on day {day} after {max_retries} attempts")

            finally:
                logging.info(f"Finished attempt {attempt} for day {day}")

    # for day in days:
    #     temp_df = filtered_df[filtered_df['day']==day]
    #     try:
    #         thread_id = data['repository']['full_name'].encode("utf-8").hex()
    #         username = data["repository"]["full_name"].split('/')[0]
    #         # DB_URI = current_app.config['SQLALCHEMY_DATABASE_URI']
    #         from app.extensions import graph_context
    #         from app.extensions import pool
    #         with graph_context() as graph:
    #             config = {"configurable": {"thread_id": thread_id}}
    #             graph.invoke({'repo':data['repository']['full_name'],'formatted_commits':temp_df.to_dict(orient='records'),'day':day},config=config)
    #     except:
    #         current_app.logger.error("DB connection lost, resetting session...", exc_info=True)
    #         # throw away dead session
    #         db.session.remove()
    #         # also clear engine pool (forces new connections next time)
    #         db.engine.dispose()
    #         logging.error('Unhandled exception', exc_info=sys.exc_info())

    #     finally:
    #         logging.info('Commit Extracted Completely')
