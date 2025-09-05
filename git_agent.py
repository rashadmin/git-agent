from app import create_app,db
from app.agent_call.graph import graph
from app.extensions import checkpointer,conn
from app.models import User,Post
app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'graph':graph,'user':User,'post':Post}