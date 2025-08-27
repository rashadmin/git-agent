from flask import render_template,current_app
from app.errors import bp


current_app.config['SECRET_KEY']
current_app.config['GITHUB_TOKEN']
@bp.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500