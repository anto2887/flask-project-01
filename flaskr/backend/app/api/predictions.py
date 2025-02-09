from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from http import HTTPStatus
from datetime import datetime, timezone

from app.api import login_required_api
from app.models import (
    UserPredictions, Fixture, PredictionStatus,
    MatchStatus, db
)

bp = Blueprint('predictions', __name__, url_prefix='/predictions')

@bp.route('', methods=['POST'])
@login_required_api
def submit_prediction():
    try:
        data = request.get_json()
        if not data or 'fixture_id' not in data or 'score1' not in data or 'score2' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), HTTPStatus.BAD_REQUEST

        fixture = Fixture.query.filter_by(fixture_id=data['fixture_id']).first()
        if not fixture:
            return jsonify({
                'status': 'error',
                'message': 'Fixture not found'
            }), HTTPStatus.NOT_FOUND

        if fixture.status != MatchStatus.NOT_STARTED:
            return jsonify({
                'status': 'error',
                'message': 'Cannot predict after match has started'
            }), HTTPStatus.BAD_REQUEST

        prediction = UserPredictions.query.filter_by(
            author_id=current_user.id,
            fixture_id=data['fixture_id']
        ).first()

        if not prediction:
            prediction = UserPredictions(
                author_id=current_user.id,
                fixture_id=data['fixture_id'],
                week=int(fixture.round.split(' ')[-1]),
                season=fixture.season
            )
            db.session.add(prediction)

        prediction.score1 = data['score1']
        prediction.score2 = data['score2']
        prediction.prediction_status = PredictionStatus.SUBMITTED
        prediction.submission_time = datetime.now(timezone.utc)

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Prediction submitted successfully',
            'data': {
                'prediction_id': prediction.id,
                'fixture_id': prediction.fixture_id,
                'score1': prediction.score1,
                'score2': prediction.score2,
                'status': prediction.prediction_status.value,
                'submission_time': prediction.submission_time.isoformat()
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting prediction: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error submitting prediction'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:prediction_id>', methods=['GET'])
@login_required_api
def get_prediction(prediction_id):
    try:
        prediction = UserPredictions.query.get(prediction_id)
        if not prediction:
            return jsonify({
                'status': 'error',
                'message': 'Prediction not found'
            }), HTTPStatus.NOT_FOUND

        if prediction.author_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

        return jsonify({
            'status': 'success',
            'data': {
                'prediction_id': prediction.id,
                'fixture_id': prediction.fixture_id,
                'score1': prediction.score1,
                'score2': prediction.score2,
                'status': prediction.prediction_status.value,
                'points': prediction.points,
                'submission_time': prediction.submission_time.isoformat() if prediction.submission_time else None
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching prediction: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching prediction'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/reset/<int:prediction_id>', methods=['POST'])
@login_required_api
def reset_prediction(prediction_id):
    try:
        prediction = UserPredictions.query.get(prediction_id)
        if not prediction:
            return jsonify({
                'status': 'error',
                'message': 'Prediction not found'
            }), HTTPStatus.NOT_FOUND

        if prediction.author_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

        if prediction.fixture.status != MatchStatus.NOT_STARTED:
            return jsonify({
                'status': 'error',
                'message': 'Cannot reset prediction after match has started'
            }), HTTPStatus.BAD_REQUEST

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
            'message': 'Error resetting prediction'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/user', methods=['GET'])
@login_required_api
def get_user_predictions():
    try:
        fixture_id = request.args.get('fixture_id')
        status = request.args.get('status')
        
        query = UserPredictions.query.filter_by(author_id=current_user.id)
        
        if fixture_id:
            query = query.filter_by(fixture_id=fixture_id)
        if status:
            query = query.filter_by(prediction_status=PredictionStatus[status])
            
        predictions = query.order_by(UserPredictions.submission_time.desc()).all()

        return jsonify({
            'status': 'success',
            'data': [{
                'prediction_id': p.id,
                'fixture_id': p.fixture_id,
                'score1': p.score1,
                'score2': p.score2,
                'status': p.prediction_status.value,
                'points': p.points,
                'submission_time': p.submission_time.isoformat() if p.submission_time else None,
                'fixture': {
                    'home_team': p.fixture.home_team,
                    'away_team': p.fixture.away_team,
                    'status': p.fixture.status.value,
                    'date': p.fixture.date.isoformat()
                }
            } for p in predictions]
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching user predictions: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching predictions'
        }), HTTPStatus.INTERNAL_SERVER_ERROR