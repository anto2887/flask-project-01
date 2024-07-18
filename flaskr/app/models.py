from datetime import datetime
from app.db import db

class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    results = db.relationship('UserResults', backref='author', lazy=True)
    predictions = db.relationship('UserPredictions', backref='author', lazy=True)

class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    title = db.Column(db.String, nullable=False)
    body = db.Column(db.String, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    season = db.Column(db.String, nullable=False)

class UserResults(db.Model):
    __tablename__ = 'user_results'

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    season = db.Column(db.String, nullable=False)

class UserPredictions(db.Model):
    __tablename__ = 'user_predictions'

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    season = db.Column(db.String, nullable=False)
    team1 = db.Column(db.String, nullable=False)
    team2 = db.Column(db.String, nullable=False)
    score1 = db.Column(db.Integer, nullable=False)
    score2 = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('author_id', 'week', 'season', 'team1', 'team2', name='_author_week_season_teams_uc'),)
