from flask import Blueprint

bp = Blueprint('posting', __name__)

from app.posting import facebook_post,linkedin_post,twitter_post