from flask import Flask, request, jsonify
from app.agent_call.graph import graph
from app.agent_call.external import format_github_request,text_composer
import threading
import time
import requests
from app.agent_call import bp
from datetime import datetime,timedelta
from langgraph.types import Command
from app.extensions import checkpointer,conn
import pandas as pd
from app.models import User,Post
from app import db
from app.agent_call.external import doy_to_date
# Start listener thread when app launches
# listener_thread = threading.Thread(target=background_listener, args=(graph,), daemon=True)
# listener_thread.start()

#to add model
def yday_to_date(row):
    return datetime(int(row["year"]), 1, 1) + timedelta(days=int(row["dayofyear"]) - 1)


@bp.route("/health",methods=['GET'])
def health_check():
    print('Checking Health Status')
    return jsonify(status="ok")

@bp.route("/agent", methods=["POST"])
# @app.route("/agent")
def run_agent():
    # global active_thread_id
    event = request.headers.get("X-GitHub-Event")
    # print(event)
    if event != "push":
        return jsonify({"msg": "Not a push event"}), 200
    data = request.json
    thread_id = data['repository']['full_name'].encode("utf-8").hex()
    username = data["repository"]["full_name"].split('/')[0]
    config = {"configurable": {"thread_id": thread_id}}
    graph.invoke({'commits':data,'user_id':username},config=config)
    # user_input = data.get("message")
    # thread_id = data.get("thread_id", "default")
    # active_thread_id = thread_id

    # config = {"configurable": {"thread_id": thread_id}}

    # result = graph.invoke({"requests": [], "last_id": "0"}, config=config)
    return 'hello world'
    
@bp.route("/compose", methods=["GET"])
def compose_text():
    cur = conn.cursor()
    printer = []
    cur.execute("SELECT thread_id, checkpoint_id, checkpoint FROM checkpoints ORDER BY checkpoint_id DESC")
    rows = cur.fetchall()
    today_thread_id = {row[0] for row in rows if datetime.fromisoformat(row[2]['ts']).date() == datetime.now().date()}
    # compose for every commit for that day per repo by :
    # we will query the db for the checkpointer to return all threads that was modified the previous day
    for thread_id in today_thread_id:
        text_composer(thread_id)
        repo = bytes.fromhex(thread_id).decode("utf-8")
        cur.execute(f"SELECT date_commited FROM post where repo ='{repo}'")
        config = {"configurable": {"thread_id": thread_id}}
        state = graph.get_state(config=config).values
        date_in_db = cur.fetchall()
        df = pd.DataFrame().from_records(state['compiled_diary_list'])
        date_in_diary = df['date'].str.split('-',expand=True).rename(columns={0:'year',1:'dayofyear'})
        date_in_diary_val = date_in_diary.apply(yday_to_date, axis=1).values
        for date in date_in_diary_val:
            # conver from datetime to date
            dayofyear= date.dt.dayofyear.astype(str)
            year = date.dt.year.astype(str)
            coded_date = year+'-'+dayofyear
            info = df[df['date']==coded_date].iloc[0].to_dict()
            if not date in date_in_db:
                username=repo.split('/')[0]
                user_id = User.query.filter_by(username=username).first().id
                id = (username+repo+coded_date).encode("utf-8").hex()
                info.update({'body':info['compiled_diary'],'date_committed':date,'user_id':user_id,'id':id})
                info.pop('compiled_diary')
                post = Post()
                post.from_dict(info)
                db.session.add(post)
                db.session.commit()
        #convert the date in the diary list to an actual date, check if it is in db, if not, add it to it


    return 'DONE'
    # return state.values['extracted_commits']

    # return jsonify({
    #     "thread_id": thread_id,
    #     "response": result
    # })

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8000, debug=True)
