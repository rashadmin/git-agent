import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    if os.getenv('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://git_agent_db_xocq_user:HRsa5HU2jL4y52lml80ZsmvG6dsjhlBF@dpg-d2r9j86r433s73fbnoa0-a.oregon-postgres.render.com/git_agent_db_xocq?sslmode=require' or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
