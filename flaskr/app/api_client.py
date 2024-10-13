import requests
import os
from app.models import db, Fixture
from flask import current_app

API_KEY = os.environ.get('API_FOOTBALL_KEY')
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

def populate_initial_data():
    current_app.logger.info("Starting initial data population")
    if not API_KEY:
        current_app.logger.error("API_FOOTBALL_KEY not set in environment variables")
        return

    url = f"{BASE_URL}/fixtures"
    querystring = {"league":"39","season":"2023"}  # Premier League, 2023 season
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        fixtures = response.json()['response']
        for fixture in fixtures:
            existing_fixture = Fixture.query.filter_by(fixture_id=fixture['fixture']['id']).first()
            if not existing_fixture:
                new_fixture = Fixture(
                    fixture_id=fixture['fixture']['id'],
                    home_team=fixture['teams']['home']['name'],
                    away_team=fixture['teams']['away']['name'],
                    date=fixture['fixture']['date'],
                    league=fixture['league']['name'],
                    season=fixture['league']['season'],
                    round=fixture['league']['round'],
                    status=fixture['fixture']['status']['long'],
                    home_score=fixture['goals']['home'],
                    away_score=fixture['goals']['away']
                )
                db.session.add(new_fixture)
        
        db.session.commit()
        current_app.logger.info(f"Populated {len(fixtures)} fixtures")
    except requests.RequestException as e:
        current_app.logger.error(f"API request failed: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"Error populating initial data: {str(e)}")

def get_fixtures(league_id, season, round):
    url = f"{BASE_URL}/fixtures"
    querystring = {"league": league_id, "season": season, "round": f"Regular Season - {round}"}
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        
        fixtures = response.json()['response']
        return [
            {
                'home_team': fixture['teams']['home']['name'],
                'away_team': fixture['teams']['away']['name'],
                'home_team_logo': fixture['teams']['home']['logo'],
                'away_team_logo': fixture['teams']['away']['logo'],
                'fixture_id': fixture['fixture']['id']
            }
            for fixture in fixtures
        ]
    except requests.RequestException as e:
        current_app.logger.error(f"API request failed: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"Error fetching fixtures: {str(e)}")
    return None

def get_league_id(league_name):
    league_mapping = {
        "Premier League": 39,
        "La Liga": 140,
        "UEFA Champions League": 2
    }
    return league_mapping.get(league_name)