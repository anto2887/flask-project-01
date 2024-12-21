from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify, current_app, abort
from flask_login import current_user, login_required
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List, Dict, Optional

from app.models import (
    Post, Users, UserResults, UserPredictions, Group, 
    user_groups, db, Fixture, PredictionStatus, MatchStatus
)
from app.season import get_current_season
from app.services.football_api import FootballAPIService
from app.api_client import get_secret

bp = Blueprint('blog', __name__)

def get_api_service() -> FootballAPIService:
    """Initialize the Football API service"""
    api_key = get_secret()
    if not api_key:
        raise ValueError("Failed to retrieve API key")
    return FootballAPIService(api_key)

def get_user_points() -> Dict[int, int]:
    """Get points for all users"""
    points_query = db.session.query(
        UserResults.author_id,
        func.sum(UserResults.points).label('total_points')
    ).group_by(UserResults.author_id).all()
    
    return {up.author_id: up.total_points for up in points_query}

def get_current_matchday(league: Optional[str] = None) -> int:
    """Get current matchday for a league"""
    if not league:
        return 1
        
    current_fixture = Fixture.query.filter(
        Fixture.league == league,
        Fixture.date > datetime.now(timezone.utc)
    ).order_by(Fixture.date).first()
    
    return int(current_fixture.round.split(' ')[-1]) if current_fixture else 1

@bp.route('/')
@login_required
def index():
    try:
        # Get user groups
        user_groups_query = Group.query.join(user_groups).filter(
            user_groups.c.user_id == current_user.id
        ).all()
        
        # Get live matches
        live_matches = []
        for group in user_groups_query:
            matches = Fixture.query.filter(
                Fixture.league == group.league,
                Fixture.status.in_([MatchStatus.LIVE, MatchStatus.HALFTIME])
            ).all()
            live_matches.extend(matches)
            
        # Get upcoming matches for predictions
        upcoming_matches = Fixture.query.filter(
            Fixture.status == MatchStatus.NOT_STARTED,
            Fixture.date > datetime.now(timezone.utc)
        ).order_by(Fixture.date).limit(5).all()
        
        # Get user stats and predictions
        seasons = db.session.query(UserPredictions.season.distinct()).all()
        seasons = [season[0] for season in seasons]
        
        current_group = user_groups_query[0] if user_groups_query else None
        if current_group:
            users = Users.query.join(user_groups).filter(
                user_groups.c.group_id == current_group.id
            ).all()
        else:
            users = [current_user]
            
        # Get user points and predictions
        user_points = get_user_points()
        recent_predictions = UserPredictions.query.filter_by(
            author_id=current_user.id,
            prediction_status=PredictionStatus.SUBMITTED
        ).order_by(UserPredictions.created.desc()).limit(5).all()
        
        current_matchday = get_current_matchday(current_group.league if current_group else None)
        top_performers = get_top_performers(current_matchday)

        return render_template('base.html',
            live_matches=live_matches,
            upcoming_matches=upcoming_matches,
            users=users,
            user_points=user_points,
            recent_predictions=recent_predictions,
            user_groups=user_groups_query,
            seasons=seasons,
            current_matchday=current_matchday,
            top_performers=top_performers
        )
        
    except Exception as e:
        current_app.logger.error(f"Error in index route: {str(e)}")
        flash("An error occurred while loading the page", "error")
        return render_template('base.html')

@bp.route('/api/live-matches')
@login_required
def get_live_matches():
    try:
        user_groups = Group.query.join(user_groups).filter(
            user_groups.c.user_id == current_user.id
        ).all()
        
        live_matches = []
        for group in user_groups:
            matches = Fixture.query.filter(
                Fixture.league == group.league,
                Fixture.status.in_([MatchStatus.LIVE, MatchStatus.HALFTIME])
            ).all()
            
            live_matches.extend([{
                'fixture_id': match.fixture_id,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'home_team_logo': match.home_team_logo,
                'away_team_logo': match.away_team_logo,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'status': match.status.value,
                'league': match.league
            } for match in matches])
            
        return jsonify({
            'status': 'success',
            'matches': live_matches
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching live matches: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch live matches'
        }), 500

@bp.route('/api/submit-prediction', methods=['POST'])
@login_required
def submit_prediction():
    try:
        data = request.get_json()
        fixture_id = data.get('fixture_id')
        score1 = data.get('score1')
        score2 = data.get('score2')
        
        if not all([fixture_id, score1 is not None, score2 is not None]):
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), 400
            
        fixture = Fixture.query.filter_by(fixture_id=fixture_id).first()
        if not fixture:
            return jsonify({
                'status': 'error',
                'message': 'Fixture not found'
            }), 404
            
        if fixture.status != MatchStatus.NOT_STARTED:
            return jsonify({
                'status': 'error',
                'message': 'Cannot predict after match has started'
            }), 400
            
        prediction = UserPredictions.query.filter_by(
            author_id=current_user.id,
            fixture_id=fixture_id
        ).first()
        
        if not prediction:
            prediction = UserPredictions(
                author_id=current_user.id,
                fixture_id=fixture_id,
                week=int(fixture.round.split(' ')[-1]),
                season=fixture.season
            )
            db.session.add(prediction)
            
        prediction.score1 = score1
        prediction.score2 = score2
        prediction.prediction_status = PredictionStatus.SUBMITTED
        prediction.submission_time = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Prediction submitted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting prediction: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to submit prediction'
        }), 500

@bp.route('/api/reset-prediction/<int:fixture_id>', methods=['POST'])
@login_required
def reset_prediction(fixture_id):
    try:
        fixture = Fixture.query.filter_by(fixture_id=fixture_id).first()
        if not fixture:
            return jsonify({
                'status': 'error',
                'message': 'Fixture not found'
            }), 404
            
        if fixture.status != MatchStatus.NOT_STARTED:
            return jsonify({
                'status': 'error',
                'message': 'Cannot reset prediction after match has started'
            }), 400
            
        prediction = UserPredictions.query.filter_by(
            author_id=current_user.id,
            fixture_id=fixture_id
        ).first()
        
        if prediction:
            prediction.prediction_status = PredictionStatus.EDITABLE
            prediction.last_modified = datetime.now(timezone.utc)
            db.session.commit()
            
        return jsonify({
            'status': 'success',
            'message': 'Prediction reset successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error resetting prediction: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to reset prediction'
        }), 500

@bp.route('/api/get-predictions')
@login_required
def get_predictions():
    try:
        fixture_id = request.args.get('fixture_id')
        if not fixture_id:
            return jsonify({
                'status': 'error',
                'message': 'Fixture ID required'
            }), 400
            
        fixture = Fixture.query.filter_by(fixture_id=fixture_id).first()
        if not fixture:
            return jsonify({
                'status': 'error',
                'message': 'Fixture not found'
            }), 404
            
        predictions = UserPredictions.query.filter_by(
            fixture_id=fixture_id,
            prediction_status=PredictionStatus.SUBMITTED
        ).all()
        
        return jsonify({
            'status': 'success',
            'predictions': [{
                'username': p.author.username,
                'score1': p.score1,
                'score2': p.score2,
                'submission_time': p.submission_time.isoformat() if p.submission_time else None
            } for p in predictions]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching predictions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch predictions'
        }), 500

@bp.route('/get_filtered_results')
@login_required
def get_filtered_results():
    try:
        group_id = request.args.get('group_id')
        season = request.args.get('season')

        query = db.session.query(
            Users.id,
            Users.username,
            func.coalesce(func.sum(UserResults.points), 0).label('total_points')
        ).join(user_groups, Users.id == user_groups.c.user_id)
        
        if group_id:
            query = query.filter(user_groups.c.group_id == group_id)
        
        if season:
            query = query.filter(UserResults.season == season)
        
        query = (query
                .outerjoin(UserResults, Users.id == UserResults.author_id)
                .group_by(Users.id, Users.username)
                .order_by(func.sum(UserResults.points).desc()))

        results = query.all()

        return jsonify([{
            'username': result.username,
            'points': int(result.total_points)
        } for result in results])
        
    except Exception as e:
        current_app.logger.error(f"Error getting filtered results: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get results'
        }), 500

def get_top_performers(matchday=None, group_id=None):
    try:
        query = db.session.query(
            Users.username,
            func.sum(UserPredictions.points).label('total_points')
        ).join(UserPredictions, Users.id == UserPredictions.author_id)
        
        if group_id:
            query = query.join(user_groups, Users.id == user_groups.c.user_id)
            query = query.filter(user_groups.c.group_id == group_id)
        
        if matchday:
            query = query.filter(UserPredictions.week == matchday)
        
        query = (query
                .filter(UserPredictions.prediction_status == PredictionStatus.PROCESSED)
                .group_by(Users.username)
                .order_by(func.sum(UserPredictions.points).desc())
                .limit(3))

        results = query.all()

        return [{
            'username': result.username,
            'points': int(result.total_points)
        } for result in results]
        
    except Exception as e:
        current_app.logger.error(f"Error getting top performers: {str(e)}")
        return []