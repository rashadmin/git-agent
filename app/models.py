from app import db,login
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for
from hashlib import md5
from flask_login import UserMixin
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page=page, per_page=per_page,
                                   error_out=False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data

class User(UserMixin,PaginatedAPIMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    firstname = db.Column(db.String(64), index=True)
    lastname = db.Column(db.String(64), index=True)
    email = db.Column(db.String(120), index=True, unique=True)
    about_me = db.Column(db.String(360))
    password_hash = db.Column(db.String(256))
    posts = db.relationship('Post', backref='author', lazy='dynamic')

## add user to get post

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'first_name':self.firstname,
            'last_name':self.lastname,
            'about_me': self.about_me,
            'post_count': self.posts.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data
    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'about_me','firstname','lastname']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

class Post(PaginatedAPIMixin,db.Model):
    id = db.Column(db.String(64), primary_key=True)
    repo = db.Column(db.String(64), index=True)
    summary = db.Column(db.Text, index=True)
    body = db.Column(db.Text)
    date_commited = db.Column(db.DateTime, index=True)
    date_posted = db.Column(db.DateTime, index=True, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body)
    
    def to_dict(self):
        user = User.query.get_or_404(self.user_id)

        data = {
            'id': self.id,
            'username': user.username,
            'first_name':user.firstname,
            'last_name':user.lastname,
            'repo':self.repo,
            'summary':self.summary,
            'body': self.body,
            'date_committed':self.date_commited,
            'date_posted':self.date_posted,
            '_links': {
                'self': url_for('api.get_post', id=self.id),
                'user':  url_for('api.get_user', id=self.user_id),
                'avatar': user.avatar(128)
            }
        }
        return data


    def from_dict(self, data):
        for field in ['user_id','summary','repo' ,'body', 'date_committed','id']:
            if field in data:
                setattr(self, field, data[field])




                
