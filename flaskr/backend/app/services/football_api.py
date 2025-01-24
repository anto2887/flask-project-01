from flask import Blueprint, jsonify, request, current_app
from app.db import get_db
import requests
from typing import Optional, List, Dict, Any
import time
from datetime import datetime, timedelta

class FootballAPIService:
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()  # Remove any whitespace
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-rapidapi-key': self.api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }
        # Pro Plan rate limiting
        self.requests_per_minute = 300
        self.minute_requests = 0
        self.last_request_time = datetime.now()
        self.last_reset_time = datetime.now()

    def _check_rate_limits(self):
        """Check and handle rate limits"""
        current_time = datetime.now()

        # Reset minute counter if it's been more than a minute
        if (current_time - self.last_reset_time) >= timedelta(minutes=1):
            self.minute_requests = 0
            self.last_reset_time = current_time
            current_app.logger.debug("Rate limit counter reset")

        # Check if we're approaching the limit (leave some buffer)
        if self.minute_requests >= (self.requests_per_minute - 10):
            seconds_until_reset = 60 - (current_time - self.last_reset_time).seconds
            if seconds_until_reset > 0:
                current_app.logger.info(f"Approaching rate limit. Waiting {seconds_until_reset} seconds...")
                time.sleep(seconds_until_reset)
                self.minute_requests = 0
                self.last_reset_time = datetime.now()

    def _make_request(self, endpoint: str, params: Dict[str, Any], max_retries: int = 3) -> Optional[List[Dict]]:
        """Make request to football API with error handling and rate limiting"""
        retries = 0
        while retries < max_retries:
            try:
                self._check_rate_limits()
                
                url = f"{self.base_url}/{endpoint}"
                current_app.logger.debug(f"Making API request to: {url} with params: {params}")
                
                response = requests.get(url, headers=self.headers, params=params)
                
                # Update rate limit counter
                self.minute_requests += 1
                self.last_request_time = datetime.now()
                
                response.raise_for_status()
                
                data = response.json()
                if not data.get('response') and data.get('errors'):
                    current_app.logger.error(f"API Error: {data['errors']}")
                    return None
                
                # Log successful response
                current_app.logger.info(f"API request successful. Found {len(data.get('response', []))} items")
                    
                return data.get('response', [])
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    retries += 1
                    wait_time = min(2 ** retries, 60)  # Exponential backoff, max 60 seconds
                    current_app.logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds... (Attempt {retries}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                current_app.logger.error(f"HTTP Error: {str(e)}")
                break
            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"API Request failed: {str(e)}")
                break
            
        return None

    def get_fixtures_by_season(self, league_id: int, season: int) -> Optional[List[Dict]]:
        """Get fixtures for a specific league and season"""
        params = {
            'league': league_id,
            'season': season
        }
        return self._make_request('fixtures', params)

    def get_fixtures_by_date(self, league_id: int, season: int, date: Optional[str] = None) -> Optional[List[Dict]]:
        """Get fixtures for a specific date"""
        params = {
            'league': league_id,
            'season': season
        }
        if date:
            params['date'] = date
            
        return self._make_request('fixtures', params)

    def get_live_fixtures(self, league_id: int) -> Optional[List[Dict]]:
        """Get live fixtures for a specific league"""
        params = {
            'league': league_id,
            'live': 'all'
        }
        return self._make_request('fixtures', params)

bp = Blueprint('football_api', __name__, url_prefix='/api')

@bp.route('/teams/<league>', methods=['GET'])
def get_teams_by_league(league):
    """
    Retrieve teams for the given league using TeamService.
    """
    try:
        team_service = current_app.config.get('TEAM_SERVICE')
        if not team_service:
            current_app.logger.error("Team service not initialized")
            return jsonify({"error": "Team service not initialized"}), 500

        current_app.logger.debug(f"Attempting to get teams for league: {league}")
        teams = team_service.get_league_teams(league)
        
        if not teams:
            current_app.logger.warning(f"No teams found for league: {league}")
            return jsonify({"error": "No teams found for the given league."}), 404

        current_app.logger.info(f"Successfully retrieved {len(teams)} teams for {league}")
        return jsonify(teams)

    except ValueError as e:
        current_app.logger.error(f"Invalid league requested: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error retrieving teams: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve teams"}), 500

@bp.route('/fixtures/status', methods=['GET'])
def get_fixture_status():
    """Get all possible fixture statuses"""
    try:
        db = get_db()
        query = "SELECT DISTINCT status FROM fixtures"
        statuses = db.execute(query).fetchall()

        if not statuses:
            current_app.logger.warning("No fixture statuses found in database")
            return jsonify([]), 200

        result = [status["status"] for status in statuses]
        current_app.logger.debug(f"Retrieved {len(result)} fixture statuses")
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error retrieving fixture statuses: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve fixture statuses"}), 500

@bp.route('/fixtures', methods=['GET'])
def get_fixtures():
    """Get all fixtures"""
    try:
        db = get_db()
        query = """
            SELECT 
                fixture_id, home_team, away_team, home_team_logo, away_team_logo,
                date, league, season, round, status, home_score, away_score,
                venue, venue_city
            FROM fixtures
        """
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

        current_app.logger.debug(f"Retrieved {len(result)} fixtures")
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error retrieving fixtures: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve fixtures"}), 500

@bp.route('/fixtures/<league>', methods=['GET'])
def get_fixtures_by_league(league):
    """Get fixtures for a specific league"""
    try:
        db = get_db()
        query = """
            SELECT 
                fixture_id, home_team, away_team, home_team_logo, away_team_logo,
                date, league, season, round, status, home_score, away_score,
                venue, venue_city
            FROM fixtures 
            WHERE league = ?
        """
        fixtures = db.execute(query, (league,)).fetchall()

        if not fixtures:
            current_app.logger.warning(f"No fixtures found for league: {league}")
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

        current_app.logger.debug(f"Retrieved {len(result)} fixtures for league: {league}")
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error retrieving fixtures: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve fixtures"}), 500

@bp.route('/leagues', methods=['GET'])
def get_leagues():
    """Get all available leagues"""
    try:
        db = get_db()
        query = "SELECT DISTINCT league FROM fixtures"
        leagues = db.execute(query).fetchall()

        if not leagues:
            current_app.logger.warning("No leagues found in database")
            return jsonify([]), 200

        result = [league["league"] for league in leagues]
        current_app.logger.debug(f"Retrieved {len(result)} leagues")
        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error retrieving leagues: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve leagues"}), 500