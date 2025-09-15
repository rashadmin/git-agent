from app import create_app,db
from app.agent_call.graph import graph
from app.models import User,Post
from app.agent_call.composer import run_compose
from app.extensions import checkpoint_set
app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'graph':graph,'user':User,'post':Post,'run':run_compose,'set':checkpoint_set}