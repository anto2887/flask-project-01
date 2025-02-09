from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from http import HTTPStatus
from sqlalchemy import func, case, distinct

from app.api import login_required_api
from app.models import (
    Users, UserResults, UserPredictions, Group, 
    user_groups, db, PredictionStatus, Fixture
)

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('/profile', methods=['GET'])
@login_required_api
def get_profile():
    try:
        # Get user's groups
        user_groups_data = Group.query.join(
            user_groups
        ).filter(
            user_groups.c.user_id == current_user.id
        ).all()

        # Get total points
        total_points = db.session.query(
            func.sum(UserResults.points)
        ).filter(
            UserResults.author_id == current_user.id
        ).scalar() or 0

        # Get prediction stats
        prediction_stats = db.session.query(
            func.count(UserPredictions.id).label('total_predictions'),
            func.sum(case((UserPredictions.points == 3, 1), else_=0)).label('perfect_predictions'),
            func.avg(UserPredictions.points).label('average_points')
        ).filter(
            UserPredictions.author_id == current_user.id,
            UserPredictions.prediction_status == PredictionStatus.PROCESSED
        ).first()

        return jsonify({
            'status': 'success',
            'data': {
                'id': current_user.id,
                'username': current_user.username,
                'groups': [{
                    'id': group.id,
                    'name': group.name,
                    'league': group.league
                } for group in user_groups_data],
                'stats': {
                    'total_points': int(total_points),
                    'total_predictions': int(prediction_stats.total_predictions or 0),
                    'perfect_predictions': int(prediction_stats.perfect_predictions or 0),
                    'average_points': float(prediction_stats.average_points or 0)
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching user profile: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching user profile'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/profile', methods=['PUT'])
@login_required_api
def update_profile():
    try:
        data = request.get_json()

        # Currently only username can be updated
        if 'username' in data:
            # Check if username is taken
            existing_user = Users.query.filter(
                Users.username == data['username'],
                Users.id != current_user.id
            ).first()
            
            if existing_user:
                return jsonify({
                    'status': 'error',
                    'message': 'Username already taken'
                }), HTTPStatus.CONFLICT

            current_user.username = data['username']
            db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Profile updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user profile: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error updating user profile'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/stats', methods=['GET'])
@login_required_api
def get_user_stats():
    try:
        user_id = request.args.get('user_id', type=int)
        if user_id and user_id != current_user.id:
            # Check if user is in any of the same groups
            shared_groups = db.session.query(Group).join(
                user_groups, Group.id == user_groups.c.group_id
            ).filter(
                user_groups.c.user_id.in_([current_user.id, user_id])
            ).group_by(Group.id).having(
                func.count(distinct(user_groups.c.user_id)) == 2
            ).all()

            if not shared_groups:
                return jsonify({
                    'status': 'error',
                    'message': 'Unauthorized access'
                }), HTTPStatus.FORBIDDEN

            target_user = Users.query.get(user_id)
        else:
            target_user = current_user

        # Get user's stats
        season_stats = db.session.query(
            UserResults.season,
            func.sum(UserResults.points).label('total_points')
        ).filter(
            UserResults.author_id == target_user.id
        ).group_by(
            UserResults.season
        ).all()

        prediction_stats = db.session.query(
            func.count(UserPredictions.id).label('total_predictions'),
            func.sum(case((UserPredictions.points == 3, 1), else_=0)).label('perfect_predictions'),
            func.avg(UserPredictions.points).label('average_points')
        ).filter(
            UserPredictions.author_id == target_user.id,
            UserPredictions.prediction_status == PredictionStatus.PROCESSED
        ).first()

        return jsonify({
            'status': 'success',
            'data': {
                'username': target_user.username,
                'seasons': [{
                    'season': season,
                    'points': int(points)
                } for season, points in season_stats],
                'overall_stats': {
                    'total_predictions': int(prediction_stats.total_predictions or 0),
                    'perfect_predictions': int(prediction_stats.perfect_predictions or 0),
                    'average_points': float(prediction_stats.average_points or 0)
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching user stats: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching user stats'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/predictions', methods=['GET'])
@login_required_api
def get_prediction_history():
    try:
        # Get query parameters
        user_id = request.args.get('user_id', type=int)
        season = request.args.get('season')
        week = request.args.get('week', type=int)
        group_id = request.args.get('group_id', type=int)

        if user_id and user_id != current_user.id:
            # Check if user is in the same group
            if not group_id:
                return jsonify({
                    'status': 'error',
                    'message': 'Group ID required for other users'
                }), HTTPStatus.BAD_REQUEST

            shared_group = db.session.query(Group).join(
                user_groups
            ).filter(
                Group.id == group_id,
                user_groups.c.user_id.in_([current_user.id, user_id])
            ).first()

            if not shared_group:
                return jsonify({
                    'status': 'error',
                    'message': 'Unauthorized access'
                }), HTTPStatus.FORBIDDEN

            target_user = Users.query.get(user_id)
        else:
            target_user = current_user

        # Build query
        query = UserPredictions.query.filter_by(author_id=target_user.id)

        if season:
            query = query.filter_by(season=season)
        if week:
            query = query.filter_by(week=week)
        if group_id:
            query = query.join(
                Fixture
            ).join(
                Group, Group.league == Fixture.league
            ).filter(
                Group.id == group_id
            )

        predictions = query.order_by(
            UserPredictions.season.desc(),
            UserPredictions.week.desc(),
            UserPredictions.created.desc()
        ).all()

        return jsonify({
            'status': 'success',
            'data': [{
                'id': pred.id,
                'fixture_id': pred.fixture_id,
                'score1': pred.score1,
                'score2': pred.score2,
                'points': pred.points,
                'status': pred.prediction_status.value,
                'week': pred.week,
                'season': pred.season,
                'submission_time': pred.submission_time.isoformat() if pred.submission_time else None,
                'fixture': {
                    'home_team': pred.fixture.home_team,
                    'away_team': pred.fixture.away_team,
                    'home_score': pred.fixture.home_score,
                    'away_score': pred.fixture.away_score,
                    'status': pred.fixture.status.value,
                    'date': pred.fixture.date.isoformat()
                }
            } for pred in predictions]
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching prediction history: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching prediction history'
        }), HTTPStatus.INTERNAL_SERVER_ERROR