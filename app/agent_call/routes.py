from flask import Flask, request, jsonify
from app.agent_call.graph import graph
from app.agent_call.external import format_github_request
import threading
import time
import requests
from app.agent_call import bp
# Start listener thread when app launches
# listener_thread = threading.Thread(target=background_listener, args=(graph,), daemon=True)
# listener_thread.start()


def ping_self():
    """Keep the app alive by pinging itself periodically."""
    while True:
        try:
            requests.get("https://git-agent.onrender.com/health")
            print("Pinged successfully")
        except Exception as e:
            print(f"Ping failed: {e}")
        time.sleep(6)  # every 10 minutes


# @bp.before_app_request
# def activate_job():
#     thread = threading.Thread(target=ping_self)
#     thread.daemon = True
#     thread.start()

@bp.route("/health")
def health_check():
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
    config = {"configurable": {"thread_id": "5"}}
    graph.invoke({'commits':data},config=config)
    # user_input = data.get("message")
    # thread_id = data.get("thread_id", "default")
    # active_thread_id = thread_id

    # config = {"configurable": {"thread_id": thread_id}}

    # result = graph.invoke({"requests": [], "last_id": "0"}, config=config)
    return 'hello world'
    # return jsonify({
    #     "thread_id": thread_id,
    #     "response": result
    # })

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8000, debug=True)
