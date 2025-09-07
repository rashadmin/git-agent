from flask import jsonify,request,url_for
from app.models import Post,User
from app.api import bp
from app.api.errors import bad_request
from app import db
import pandas as pd
from app.agent_call.external import doy_to_date
import time
@bp.route('/posts/<thread_id>/<date>', methods=['POST'])
def create_posts(thread_id,date):
    from app.agent_call.graph import graph
    config = {"configurable": {"thread_id": str(thread_id)}}
    print(type(thread_id))
    # time.sleep(1)
    state = graph.get_state(config=config).values
    username = 'rashadmin'#state['user_id']
    user_id = User.query.filter_by(username=username).first_or_404().id
    if user_id is None:
        return bad_request('User does not exist')
    # info = state['compiled_dictionary']
    compiled_df = pd.DataFrame().from_records(state['compiled_diary_list'])
    info = compiled_df[compiled_df['date']==date].iloc[0].to_dict()
    print(compiled_df)
    id = f'{username}{info['repo']}{date}'.encode("utf-8").hex()
    year =int(date.split('-')[0])
    dayofyear = int(date.split('-')[1])
    date_committed = doy_to_date(year,dayofyear)
    info.update({'body':info['compiled_diary'],'date_committed':date_committed,'user_id':user_id,'id':id})
    info.pop('compiled_diary')
    post = Post()
    post.from_dict(info)
    db.session.add(post)
    db.session.commit()
    response = jsonify(post.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_post', id=post.id)
    return response


@bp.route('/posts/<id>', methods=['GET'])
def get_post(id):
    return jsonify(Post.query.get_or_404(id).to_dict())

@bp.route('/posts', methods=['GET'])
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page,
                                   'api.get_posts')
    return jsonify(data)


@bp.route('/posts/<id>', methods=['PUT'])
def update_post(id):
    post = Post.query.get_or_404(id)
    data = request.get_json() or {}
    post.from_dict(data)
    db.session.commit()
    return jsonify(post.to_dict())
