from flask import Blueprint

bp = Blueprint('api', __name__)

from app.api import user, errors, tokens



# GET	/api/users/<id>	Return a user.
# GET	/api/users	Return the collection of all users.
# GET	/api/users/<id>/followers	Return the followers of this user.
# GET	/api/users/<id>/followed	Return the users this user is following.
# POST	/api/users	Register a new user account.
# PUT	/api/users/<id>	Modify a user.