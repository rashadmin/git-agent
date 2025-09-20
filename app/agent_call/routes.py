from flask import Flask, request, jsonify
from app.agent_call.external import format_github_request,text_composer
import threading
import time
import requests
import psycopg
from flask import jsonify,request,current_app
from app.agent_call import bp
from datetime import datetime,timedelta
from langgraph.types import Command
import pandas as pd
from app.models import User,Post
from app import db
from app.agent_call.external import doy_to_date
# from app.extensions import graph_context
# from app.agent_call.graph import builder
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg
from app.agent_call.graph import graph
# from app.extensions import pool
import logging
logging.basicConfig(level=logging.INFO)
# from app.agent_call.graph import graph
# Start listener thread when app launches
# listener_thread = threading.Thread(target=background_listener, args=(graph,), daemon=True)
# listener_thread.start()
from redis import Redis
import rq
#to add model
def yday_to_date(row):
    return datetime(int(row["year"]), 1, 1) + timedelta(days=int(row["dayofyear"]) - 1)


@bp.route("/health",methods=['GET'])
def health_check():
    print('Checking Health Status')
    return jsonify(status="ok")






@bp.route("/agent", methods=["POST"])
# @retry_route(retries=3, delay=2, backoff=2)
# @app.route("/agent")
def run_agent():
    from app.tasks import extract_commits
    event = request.headers.get("X-GitHub-Event")
    if event != "push":
        return jsonify({"msg": "Not a push event"}), 200
    print('hereeeeeeeee')
    data = request.json
    username = data["repository"]["full_name"].split('/')[0]
    user = User.query.filter_by(username=username).first_or_404()
    # user.launch_task('extract_commits',data)
    extract_commits(data)
    # db.session.commit()
    return 'Agent run'
    
@bp.route("/compose", methods=["GET"])
def compose_text():
    conn = psycopg.connect(current_app.config['SQLALCHEMY_DATABASE_URI'],autocommit=True)
    cur = conn.cursor()
    printer = []
    cur.execute("SELECT thread_id, checkpoint_id, checkpoint FROM checkpoints ORDER BY checkpoint_id DESC")
    rows = cur.fetchall()
    yesterday = datetime.now().date() - timedelta(days=1)
    today_thread_id = {row[0] for row in rows if datetime.fromisoformat(row[2]['ts']).date() == datetime.now().date()}
    # compose for every commit for that day per repo by :
    # we will query the db for the checkpointer to return all threads that was modified the previous day
    for thread_id in today_thread_id:
        text_composer(thread_id)
        repo = bytes.fromhex(thread_id).decode("utf-8")
        date_in_db = cur.execute(f"SELECT date_committed FROM post where repo ='{repo}'")
        #getting date in db
        config = {"configurable": {"thread_id": thread_id}}
        DB_URI = current_app.config['SQLALCHEMY_DATABASE_URI']
        state = graph.get_state(config=config).values
        df = pd.DataFrame().from_records(state['compiled_diary_list'])
        date_in_diary = df['date'].str.split('-',expand=True).rename(columns={0:'year',1:'dayofyear'})
        date_in_diary_val = date_in_diary.apply(yday_to_date, axis=1).values
        for date in date_in_diary_val:
            # we don't need to convert, get the datein compiled_diary_list, conveert to year-dayofyear
            # conver from datetime to date
            dayofyear= str(pd.Timestamp(date).dayofyear)
            year = str(pd.Timestamp(date).year)
            coded_date = year+'-'+dayofyear
            info = df[df['date']==coded_date].iloc[0].to_dict()
            print(date,'\n\n\n\n\n\n')
            # convert date in db to y-doy format
            if not date in date_in_db:
                username=repo.split('/')[0]
                user_id = User.query.filter_by(username=username).first().id
                id = (username+repo+coded_date).encode("utf-8").hex()
                info.update({'date_committed':pd.Timestamp(date).to_pydatetime(),'user_id':user_id,'id':id})
                post = Post()
                post.from_dict(info)
                db.session.add(post)
                db.session.commit()
        #convert the date in the diary list to an actual date, check if it is in db, if not, add it to it
    conn.close()

    return 'DONE'
    # return state.values['extracted_commits']

    # return jsonify({
    #     "thread_id": thread_id,
    #     "response": result
    # })

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8000, debug=True)
