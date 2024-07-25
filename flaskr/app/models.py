from datetime import datetime
from app.db import db

user_groups = db.Table('user_groups',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True)
)

class Users(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    results = db.relationship('UserResults', backref='author', lazy=True)
    predictions = db.relationship('UserPredictions', backref='author', lazy=True)
    groups = db.relationship('Group', secondary=user_groups, back_populates='users')
    created_groups = db.relationship('Group', backref='creator', lazy=True)

class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    league = db.Column(db.String, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    users = db.relationship('Users', secondary=user_groups, back_populates='groups')

class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    body = db.Column(db.Text, nullable=False)
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
