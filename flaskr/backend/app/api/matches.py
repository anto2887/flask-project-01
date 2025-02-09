from flask import Blueprint, jsonify, request, current_app
from http import HTTPStatus
from datetime import datetime, timezone

from app.api import login_required_api
from app.models import Fixture, MatchStatus, db
from app.services.football_api import FootballAPIService
from app.services.match_processing import get_prediction_deadlines

bp = Blueprint('matches', __name__, url_prefix='/matches')

@bp.route('/live', methods=['GET'])
@login_required_api
def get_live_matches():
    try:
        matches = Fixture.query.filter(
            Fixture.status.in_([
                MatchStatus.LIVE,
                MatchStatus.FIRST_HALF,
                MatchStatus.SECOND_HALF,
                MatchStatus.HALFTIME,
                MatchStatus.EXTRA_TIME,
                MatchStatus.PENALTY
            ])
        ).all()

        return jsonify({
            'status': 'success',
            'data': [{
                'fixture_id': match.fixture_id,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'home_team_logo': match.home_team_logo,
                'away_team_logo': match.away_team_logo,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'status': match.status.value,
                'league': match.league,
                'date': match.date.isoformat(),
                'venue_city': match.venue_city
            } for match in matches]
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching live matches: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching live matches'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:match_id>', methods=['GET'])
@login_required_api
def get_match(match_id):
    try:
        match = Fixture.query.filter_by(fixture_id=match_id).first()
        if not match:
            return jsonify({
                'status': 'error',
                'message': 'Match not found'
            }), HTTPStatus.NOT_FOUND

        prediction_deadlines = get_prediction_deadlines()
        
        return jsonify({
            'status': 'success',
            'data': {
                'fixture_id': match.fixture_id,
                'home_team': match.home_team,
                'away_team': match.away_team,
                'home_team_logo': match.home_team_logo,
                'away_team_logo': match.away_team_logo,
                'home_score': match.home_score,
                'away_score': match.away_score,
                'status': match.status.value,
                'league': match.league,
                'season': match.season,
                'round': match.round,
                'date': match.date.isoformat(),
                'venue_city': match.venue_city,
                'prediction_deadline': prediction_deadlines.get(str(match.fixture_id))
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching match {match_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching match details'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/fixtures', methods=['GET'])
@login_required_api
def get_fixtures():
    try:
        # Get query parameters
        league = request.args.get('league')
        season = request.args.get('season')
        status = request.args.get('status')
        from_date = request.args.get('from')
        to_date = request.args.get('to')

        # Build query
        query = Fixture.query

        if league:
            query = query.filter_by(league=league)
        if season:
            query = query.filter_by(season=season)
        if status:
            query = query.filter_by(status=MatchStatus[status])
        if from_date:
            query = query.filter(Fixture.date >= datetime.fromisoformat(from_date))
        if to_date:
            query = query.filter(Fixture.date <= datetime.fromisoformat(to_date))

        # Execute query with ordering
        fixtures = query.order_by(Fixture.date).all()

        return jsonify({
            'status': 'success',
            'data': [{
                'fixture_id': fixture.fixture_id,
                'home_team': fixture.home_team,
                'away_team': fixture.away_team,
                'home_team_logo': fixture.home_team_logo,
                'away_team_logo': fixture.away_team_logo,
                'home_score': fixture.home_score,
                'away_score': fixture.away_score,
                'status': fixture.status.value,
                'league': fixture.league,
                'season': fixture.season,
                'round': fixture.round,
                'date': fixture.date.isoformat(),
                'venue_city': fixture.venue_city
            } for fixture in fixtures]
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching fixtures: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching fixtures'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/statuses', methods=['GET'])
@login_required_api
def get_match_statuses():
    try:
        statuses = [status.value for status in MatchStatus]
        return jsonify({
            'status': 'success',
            'data': statuses
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching match statuses: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching match statuses'
        }), HTTPStatus.INTERNAL_SERVER_ERROR