from datetime import datetime
from app.db import db

class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    results = db.relationship('UserResults', backref='author', lazy=True)

class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.relationship('Users', backref='user_posts', foreign_keys=[author_id])
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    title = db.Column(db.String, nullable=False)
    body = db.Column(db.String, nullable=False)

class UserResults(db.Model):
    __tablename__ = 'user_results'

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    username = db.relationship('Users', backref='user_results', foreign_keys=[author_id])
    points = db.Column(db.Integer, nullable=False)
