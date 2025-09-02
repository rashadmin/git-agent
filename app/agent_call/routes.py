from flask import Flask, request, jsonify
from app.agent_call.graph import graph
from app.agent_call.external import format_github_request,text_composer
import threading
import time
import requests
from app.agent_call import bp
from datetime import datetime,timedelta
from langgraph.types import Command
from app.extensions import checkpointer,conn,pool


# Start listener thread when app launches
# listener_thread = threading.Thread(target=background_listener, args=(graph,), daemon=True)
# listener_thread.start()




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
    thread_id = data['repository']['name'].encode("utf-8").hex()
    config = {"configurable": {"thread_id": thread_id}}
    graph.invoke({'commits':data},config=config)
    # user_input = data.get("message")
    # thread_id = data.get("thread_id", "default")
    # active_thread_id = thread_id

    # config = {"configurable": {"thread_id": thread_id}}

    # result = graph.invoke({"requests": [], "last_id": "0"}, config=config)
    return 'hello world'
    
@bp.route("/compose", methods=["GET"])
def compose_text():
    printer = []
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT thread_id, checkpoint_id, checkpoint
                FROM checkpoints
                ORDER BY checkpoint_id DESC
            """)
            rows = cur.fetchall()
            today_thread_id = {row[0] for row in rows if datetime.fromisoformat(row[2]['ts']).date() == datetime.now().date()}
            # compose for every commit for that day per repo by :
            # we will query the db for the checkpointer to return all threads that was modified the previous day
            for thread_id in today_thread_id:
                printer.extend(text_composer(thread_id))

        # commit only if you modify data
        conn.commit()
    
    return printer
    # return state.values['extracted_commits']

    # return jsonify({
    #     "thread_id": thread_id,
    #     "response": result
    # })

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8000, debug=True)
