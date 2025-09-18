import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    X_API_KEY = os.environ.get('X_API_KEY')
    X_API_KEY_SECRET = os.environ.get('X_API_KEY_SECRET')
    X_ACCESS_TOKEN = os.environ.get('X_ACCESS_TOKEN')
    X_ACCESS_TOKEN_SECRET=os.environ.get('X_ACCESS_TOKEN_SECRET')
    ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    if os.getenv('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://postgres.mjmtjvjtuiqxsegqdzar:0KgFAn41OCl86W8M@aws-1-eu-north-1.pooler.supabase.com:6543/postgres?sslmode=require' or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
