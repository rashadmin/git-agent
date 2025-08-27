from flask import Flask
from config import Config
def create_app(config_class=Config):    
    app = Flask(__name__)
    app.config.from_object(config_class)
    with app.app_context():
        from app.errors import bp as errors_bp
        app.register_blueprint(errors_bp)
        from app.agent_call import bp as agent_call_bp
        app.register_blueprint(agent_call_bp,url_prefix='/agent_call')
    return app

# from app.agent_call import routes