from flask import Blueprint, jsonify, request
from app.db import get_db

class FootballAPIService:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_fixtures_by_season(self, league_id, season):
        # Placeholder for fetching fixtures by season
        # Replace this with the actual API logic
        return []

    def get_fixtures_by_date(self, league_id, season, date=None):
        # Placeholder for fetching fixtures by date
        # Replace this with the actual API logic
        return []

bp = Blueprint('football_api', __name__, url_prefix='/api')

@bp.route('/teams/<league>', methods=['GET'])
def get_teams_by_league(league):
    """
    Retrieve distinct teams and their logos from the fixtures table for the given league.
    """
    db = get_db()
    try:
        query = (
            "SELECT DISTINCT home_team AS team, home_team_logo AS logo "
            "FROM fixtures WHERE league = ? "
            "UNION "
            "SELECT DISTINCT away_team AS team, away_team_logo AS logo "
            "FROM fixtures WHERE league = ?"
        )
        teams = db.execute(query, (league, league)).fetchall()

        if not teams:
            return jsonify({"error": "No teams found for the given league."}), 404

        result = [
            {"team": team["team"], "logo": team["logo"]}
            for team in teams
        ]
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/fixtures/status', methods=['GET'])
def get_fixture_status():
    """
    Retrieve distinct fixture statuses from the database.
    """
    db = get_db()
    try:
        query = "SELECT DISTINCT status FROM fixtures"
        statuses = db.execute(query).fetchall()

        result = [status["status"] for status in statuses]
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/fixtures', methods=['GET'])
def get_fixtures():
    """
    Retrieve all fixtures from the database.
    """
    db = get_db()
    try:
        query = "SELECT * FROM fixtures"
        fixtures = db.execute(query).fetchall()

        result = [
            {
                "fixture_id": fixture["fixture_id"],
                "home_team": fixture["home_team"],
                "away_team": fixture["away_team"],
                "home_team_logo": fixture["home_team_logo"],
                "away_team_logo": fixture["away_team_logo"],
                "date": fixture["date"],
                "league": fixture["league"],
                "season": fixture["season"],
                "round": fixture["round"],
                "status": fixture["status"],
                "home_score": fixture["home_score"],
                "away_score": fixture["away_score"],
                "venue": fixture["venue"],
                "venue_city": fixture["venue_city"],
            }
            for fixture in fixtures
        ]
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/fixtures/<league>', methods=['GET'])
def get_fixtures_by_league(league):
    """
    Retrieve fixtures by league from the database.
    """
    db = get_db()
    try:
        query = "SELECT * FROM fixtures WHERE league = ?"
        fixtures = db.execute(query, (league,)).fetchall()

        if not fixtures:
            return jsonify({"error": "No fixtures found for the given league."}), 404

        result = [
            {
                "fixture_id": fixture["fixture_id"],
                "home_team": fixture["home_team"],
                "away_team": fixture["away_team"],
                "home_team_logo": fixture["home_team_logo"],
                "away_team_logo": fixture["away_team_logo"],
                "date": fixture["date"],
                "league": fixture["league"],
                "season": fixture["season"],
                "round": fixture["round"],
                "status": fixture["status"],
                "home_score": fixture["home_score"],
                "away_score": fixture["away_score"],
                "venue": fixture["venue"],
                "venue_city": fixture["venue_city"],
            }
            for fixture in fixtures
        ]
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/leagues', methods=['GET'])
def get_leagues():
    """
    Retrieve distinct leagues from the fixtures table.
    """
    db = get_db()
    try:
        query = "SELECT DISTINCT league FROM fixtures"
        leagues = db.execute(query).fetchall()

        result = [league["league"] for league in leagues]
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
