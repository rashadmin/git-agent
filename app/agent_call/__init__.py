from flask import Blueprint

bp = Blueprint('agent_call', __name__)

from app.agent_call import routes,external,graph