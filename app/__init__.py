from flask import Flask
from config import Config
import threading
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import sqlalchemy as sa
from psycopg_pool import ConnectionPool

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()

def create_app(config_class=Config):    
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    with app.app_context():
        from app.errors import bp as errors_bp
        app.register_blueprint(errors_bp)
        from app.agent_call import bp as agent_call_bp
        app.register_blueprint(agent_call_bp,url_prefix='/agent_call')
        from app.api import bp as api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        from app.posting import bp as posting_bp
        app.register_blueprint(posting_bp, url_prefix='/posting')
    engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'],connect_args={"sslmode": "require"})
    inspector = sa.inspect(engine)
    if not inspector.has_table("user"):
        with app.app_context():
            db.drop_all()
            db.create_all()
            app.logger.info('Initialized the database!')
    return app

# from app.agent_call import routes