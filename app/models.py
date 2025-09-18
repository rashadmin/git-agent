from app import db,login
from datetime import datetime,timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for
from hashlib import md5
from flask_login import UserMixin
from app.posting.linkedin_post import post_linkedin
from app.posting.twitter_post import post_thread
import os
import base64
import json
from flask import current_app
import redis
import rq
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
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

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

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.now() - timedelta(seconds=1)

    def launch_task(self, name,data, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue('app.tasks.' + name, data,
                                                *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name,
                    user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user
    
    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'first_name':self.firstname,
            'last_name':self.lastname,
            'about_me': self.about_me,
            'post_count': self.posts.count(),
            '_links': {
                'self': url_for('api.get_user', username=self.username),
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
    id = db.Column(db.String(128), primary_key=True)
    repo = db.Column(db.String(64), index=True)
    summary = db.Column(db.Text, index=True)
    twitter_thread = db.Column(db.Text, index=True)
    facebook_post = db.Column(db.Text, index=True)
    linkedin_post = db.Column(db.Text, index=True)
    date_committed = db.Column(db.DateTime, index=True)
    date_posted = db.Column(db.DateTime, index=True, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.summary)
    
    def to_dict(self):
        user = User.query.get_or_404(self.user_id)
        ordered_post = Post.query.filter_by(repo=self.repo).order_by('date_committed').all()
        entry = [post.id for post in ordered_post].index(self.id)+1

        data = {
            'id': self.id,
            'entry':entry,
            'username': user.username,
            'first_name':user.firstname,
            'last_name':user.lastname,
            'repo':self.repo,
            'summary':self.summary,
            'twitter_thread':json.loads(self.twitter_thread)['tweets'],
            'facebook_post':self.facebook_post, 
            'linkedin_post':self.linkedin_post,
            # 'post_linkedin':post_linkedin(self.)
            'date_committed':self.date_committed,
            'date_posted':self.date_posted,
            '_links': {
                'self': url_for('api.get_post', id=self.id),
                'user':  url_for('api.get_user', username=user.username),
                'post_linkedin':url_for('api.PostLinkedin', id=self.id),
                'post_thread':url_for('api.PostThread', id=self.id),
                'avatar': user.avatar(128)
            }
        }
        return data


    def from_dict(self, data):
        for field in ['user_id','summary','repo', 'facebook_post', 'linkedin_post', 'date_committed','id']:
            if field in data:
                setattr(self, field, data[field])
        self.twitter_thread = json.dumps(data["twitter_thread"])


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)

    def get_rq_job(self):
        try:
            rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
        except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
            return None
        return rq_job

    def get_progress(self):
        job = self.get_rq_job()
        return job.meta.get('progress', 0) if job is not None else 100

                
