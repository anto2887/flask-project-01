from datetime import datetime
from app.db import db
from flask_login import UserMixin
from enum import Enum

class MatchStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    LIVE = "LIVE"
    HALFTIME = "HALFTIME"
    FINISHED = "FINISHED"
    POSTPONED = "POSTPONED"
    CANCELLED = "CANCELLED"

class PredictionStatus(Enum):
    EDITABLE = "EDITABLE"      # Can be edited
    SUBMITTED = "SUBMITTED"    # Submitted but can be reset
    LOCKED = "LOCKED"         # Match started, can't edit
    PROCESSED = "PROCESSED"   # Points calculated

class GroupPrivacyType(Enum):
    PRIVATE = "PRIVATE"          # Invite code only
    SEMI_PRIVATE = "SEMI_PRIVATE"  # Invite code + admin approval

class MemberRole(Enum):
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    MEMBER = "MEMBER"

class MembershipStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

user_groups = db.Table('user_groups',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True)
)

class Users(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    results = db.relationship('UserResults', backref='author', lazy=True)
    predictions = db.relationship('UserPredictions', backref='author', lazy=True)
    groups = db.relationship('Group', secondary=user_groups, back_populates='users')
    created_groups = db.relationship('Group', backref='creator', lazy=True)
    member_roles = db.relationship('GroupMember', backref='user', lazy=True)
    pending_memberships = db.relationship('PendingMembership', 
                                        foreign_keys='PendingMembership.user_id',
                                        backref='user', 
                                        lazy=True)
    processed_memberships = db.relationship('PendingMembership',
                                          foreign_keys='PendingMembership.processed_by',
                                          backref='processor',
                                          lazy=True)
    audit_logs = db.relationship('GroupAuditLog', backref='user', lazy=True)

class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    league = db.Column(db.String, nullable=False)
    invite_code = db.Column(db.String(8), unique=True, nullable=False)
    privacy_type = db.Column(db.Enum(GroupPrivacyType), default=GroupPrivacyType.PRIVATE)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    
    users = db.relationship('Users', secondary=user_groups, back_populates='groups')
    tracked_teams = db.relationship('TeamTracker', backref='group', lazy=True)
    member_roles = db.relationship('GroupMember', backref='group', lazy=True)
    analytics = db.relationship('GroupAnalytics', backref='group', lazy=True)
    pending_members = db.relationship('PendingMembership', backref='group', lazy=True)
    audit_logs = db.relationship('GroupAuditLog', backref='group', lazy=True)
    posts = db.relationship('Post', backref='group', lazy=True)

class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    body = db.Column(db.Text, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    season = db.Column(db.String, nullable=False)
    processed = db.Column(db.Boolean, default=False, nullable=False)

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
    fixture_id = db.Column(db.Integer, db.ForeignKey('fixtures.fixture_id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    season = db.Column(db.String, nullable=False)
    score1 = db.Column(db.Integer, nullable=False)
    score2 = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    prediction_status = db.Column(db.Enum(PredictionStatus), 
                                nullable=False, 
                                default=PredictionStatus.EDITABLE)
    submission_time = db.Column(db.DateTime, nullable=True)
    last_modified = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('author_id', 'fixture_id', name='_user_fixture_uc'),
        db.Index('idx_predictions_status', 'prediction_status'),
        db.Index('idx_predictions_fixture', 'fixture_id')
    )

class Fixture(db.Model):
    __tablename__ = 'fixtures'

    id = db.Column(db.Integer, primary_key=True)
    fixture_id = db.Column(db.Integer, unique=True, nullable=False)
    home_team = db.Column(db.String, nullable=False)
    away_team = db.Column(db.String, nullable=False)
    home_team_logo = db.Column(db.String)
    away_team_logo = db.Column(db.String)
    date = db.Column(db.DateTime, nullable=False)
    league = db.Column(db.String, nullable=False)
    season = db.Column(db.String, nullable=False)
    round = db.Column(db.String, nullable=False)
    status = db.Column(db.Enum(MatchStatus), nullable=False, default=MatchStatus.NOT_STARTED)
    home_score = db.Column(db.Integer, default=0)
    away_score = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    venue = db.Column(db.String)
    referee = db.Column(db.String)
    league_id = db.Column(db.Integer)
    
    predictions = db.relationship('UserPredictions', 
                                backref='fixture', 
                                lazy=True,
                                cascade="all, delete-orphan")
    
    __table_args__ = (
        db.Index('idx_fixture_date_status', 'date', 'status'),
        db.Index('idx_fixture_league_season', 'league', 'season')
    )

class TeamTracker(db.Model):
    __tablename__ = 'team_tracker'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    team_id = db.Column(db.Integer, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('group_id', 'team_id', name='_group_team_uc'),
    )

class GroupMember(db.Model):
    __tablename__ = 'group_members'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.Enum(MemberRole), default=MemberRole.MEMBER)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('group_id', 'user_id', name='_group_member_uc'),
    )

class PendingMembership(db.Model):
    __tablename__ = 'pending_memberships'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Enum(MembershipStatus), default=MembershipStatus.PENDING)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))

class GroupAnalytics(db.Model):
    __tablename__ = 'group_analytics'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    analysis_type = db.Column(db.String, nullable=False)  # 'weekly', 'monthly', 'seasonal'
    period = db.Column(db.String, nullable=False)  # '2023-W45', '2023-10', '2023-2024'
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_analytics_group_type', 'group_id', 'analysis_type'),
        db.UniqueConstraint('group_id', 'analysis_type', 'period', name='_analytics_period_uc')
    )

class GroupAuditLog(db.Model):
    __tablename__ = 'group_audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String, nullable=False)
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_audit_group_date', 'group_id', 'created_at'),
    )

class InitializationStatus(db.Model):
    __tablename__ = 'initialization_status'

    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)