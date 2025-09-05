from flask import jsonify,request,url_for
from app.models import Post
from app.api import bp
from app.api.errors import bad_request
from app import db


@bp.route('/posts', methods=['POST'])
def create_posts():
    data = request.get_json() or {}
    if 'summary' not in data or 'body' not in data or 'repo' not in data or 'date_committed' not in data:
        return bad_request('must include summary,body,date_committed,repo fields')
    if Post.query.get_or_404(data['id']).first():
        return bad_request('please use a different username')
    post = Post()
    post.from_dict(data)
    db.session.add(post)
    db.session.commit()
    response = jsonify(post.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_post', id=post.id)
    return response


@bp.route('/posts/<str:id>', methods=['GET'])
def get_post(id):
    return jsonify(Post.query.get_or_404(id).to_dict())



@bp.route('/posts/<str:id>', methods=['PUT'])
def update_post(id):
    post = Post.query.get_or_404(id)
    data = request.get_json() or {}
    post.from_dict(data)
    db.session.commit()
    return jsonify(post.to_dict())
