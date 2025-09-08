from flask import jsonify
from app import db
from app.api import bp
from app.api.auth import basic_auth
from app.api.auth import token_auth

@bp.route('/tokens', methods=['POST'])
@basic_auth.login_required
def get_token():
    token = basic_auth.current_user().get_token()
    db.session.commit()
    return jsonify({'token': token})



@bp.route('/tokens', methods=['DELETE'])
@token_auth.login_required
def revoke_token():
    token_auth.current_user().revoke_token()
    db.session.commit()
    return '', 204



# the login button takes the username and password, and will only login if the response is a 
# 200 and a token which will redirect to the homepage with the edit button visible, 
# else no edit button will be shown if not logged in i.e for just visitor only the blogs will be shown without the edit button.