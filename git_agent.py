from app import create_app,db
from app.models import User,Post
from app.agent_call.composer import run_compose
from app.extensions import graph_context
app = create_app()
DB_URI = app.config['SQLALCHEMY_DATABASE_URI']

@app.shell_context_processor
def make_shell_context():
    with graph_context(DB_URI) as graph:
        # state = graph.get_state(config=config).values
        return {'graph':graph,'user':User,'post':Post,'run':run_compose}