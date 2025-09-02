from app import create_app
from app.agent_call.graph import graph
from app.extensions import checkpointer,conn

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'graph':graph}