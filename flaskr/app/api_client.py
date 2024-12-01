import requests
import os
import boto3
from botocore.exceptions import ClientError
from app.models import db, Fixture
from flask import current_app

BASE_URL = "https://v3.football.api-sports.io"

def get_secret():
    secret_name = os.environ.get('SECRET_NAME')  # Get the full secret name from environment
    region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    if not secret_name:
        current_app.logger.error("SECRET_NAME environment variable not set")
        return None

    current_app.logger.info(f"Attempting to retrieve secret: {secret_name}")
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        current_app.logger.info("Successfully retrieved secret value")
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
    except ClientError as e:
        current_app.logger.error(f"Error retrieving secret: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"Unexpected error retrieving secret: {str(e)}")
    
    return None

def populate_initial_data():
    current_app.logger.info("Starting initial data population")
    
    API_KEY = get_secret()
    if not API_KEY:
        current_app.logger.error("Failed to retrieve API_FOOTBALL_KEY from Secrets Manager")
        return

    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }

    url = f"{BASE_URL}/fixtures"
    querystring = {"league":"39","season":"2023"}  # Premier League, 2023 season
    
    try:
        current_app.logger.info(f"Making API request to: {url}")
        response = requests.request("GET", url, headers=headers, params=querystring)
        current_app.logger.info(f"API response status code: {response.status_code}")
        current_app.logger.info(f"API response headers: {response.headers}")
        
        response.raise_for_status()
        
        data = response.json()
        if 'response' not in data:
            current_app.logger.error("Invalid API response format")
            return
            
        fixtures = data['response']
        current_app.logger.info(f"Retrieved {len(fixtures)} fixtures from API")
        
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
        if hasattr(e, 'response') and e.response is not None:
            current_app.logger.error(f"Response content: {e.response.text}")
        db.session.rollback()
    except Exception as e:
        current_app.logger.error(f"Error populating initial data: {str(e)}")
        db.session.rollback()

def get_fixtures(league_id, season, round):
    API_KEY = get_secret()
    if not API_KEY:
        current_app.logger.error("Failed to retrieve API_FOOTBALL_KEY from Secrets Manager")
        return None

    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }

    url = f"{BASE_URL}/fixtures"
    querystring = {"league": league_id, "season": season, "round": f"Regular Season - {round}"}
    
    try:
        response = requests.request("GET", url, headers=headers, params=querystring)
        response.raise_for_status()
        
        data = response.json()
        if 'response' not in data:
            current_app.logger.error("Invalid API response format")
            return None
            
        fixtures = data['response']
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
        if hasattr(e, 'response') and e.response is not None:
            current_app.logger.error(f"Response content: {e.response.text}")
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