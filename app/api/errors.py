from werkzeug.http import HTTP_STATUS_CODES 
from app.api import bp
from werkzeug.exceptions import HTTPException
from app import db
def error_response(status_code,message=None):
    payload = {'error':HTTP_STATUS_CODES.get(status_code,'unknown_error')}
    if message:
        payload['message'] = message
    return payload,status_code



def bad_request(message):
    return error_response(400,message)

@bp.errorhandler(HTTPException)
def handle_exception(e):
    return error_response(e.code)

@bp.app_errorhandler(404)
def not_found_error(error):
    return error_response(404)

@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return error_response(500)
