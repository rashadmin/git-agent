from app import create_app,db
from app.agent_call.graph import get_graph
from app.models import User,Post
from app.agent_call.composer import run_compose
app = create_app()


@app.shell_context_processor
def make_shell_context():
    graph = get_graph()
    return {'graph':graph,'user':User,'post':Post,'run':run_compose}