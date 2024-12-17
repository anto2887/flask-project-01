import requests
import os
import boto3
import time
from botocore.exceptions import ClientError
from app.models import db, Fixture
from flask import current_app

BASE_URL = "https://v3.football.api-sports.io"
RATE_LIMIT_PAUSE = 6  # Seconds between API calls
BATCH_PAUSE = 30     # Seconds between batches

def get_secret():
    """Get API key from AWS Secrets Manager"""
    secret_name = os.environ.get('SECRET_NAME')
    region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    if not secret_name:
        current_app.logger.error("SECRET_NAME environment variable not set")
        return None

    current_app.logger.info(f"Attempting to retrieve secret: {secret_name}")
    
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        response = client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            current_app.logger.info("Successfully retrieved secret value")
            return response['SecretString']
        else:
            current_app.logger.error("No SecretString in response")
            return None
    except ClientError as e:
        current_app.logger.error(f"Error retrieving secret: {str(e)}")
        return None

def get_rounds(headers, league_id, season):
    """Get all rounds for a given league and season"""
    url = f"{BASE_URL}/fixtures/rounds"
    params = {
        "league": league_id,
        "season": int(season)
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('response'):
            current_app.logger.error("No rounds found in response")
            return []

        current_app.logger.info(f"Successfully retrieved {len(data['response'])} rounds")
        return data['response']
    except Exception as e:
        current_app.logger.error(f"Error fetching rounds: {str(e)}")
        return []

def get_fixtures_for_round(headers, league_id, season, round_name):
    """Get fixtures for a specific round"""
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": league_id,
        "season": int(season),
        "round": round_name
    }

    try:
        current_app.logger.info(f"Fetching fixtures for round: {round_name}")
        
        # Rate limiting delay
        time.sleep(RATE_LIMIT_PAUSE)
        
        response = requests.get(url, headers=headers, params=params)
        
        # Check rate limits
        remaining = response.headers.get('x-ratelimit-remaining')
        if remaining and int(remaining) < 5:
            current_app.logger.warning("Close to rate limit, pausing for 60 seconds")
            time.sleep(60)
        
        response.raise_for_status()
        data = response.json()
        
        if 'errors' in data and data['errors']:
            current_app.logger.error(f"API returned errors: {data['errors']}")
            return []
        
        fixtures = data.get('response', [])
        current_app.logger.info(f"Found {len(fixtures)} fixtures for round {round_name}")
        return fixtures
    except Exception as e:
        current_app.logger.error(f"Error fetching fixtures for round {round_name}: {str(e)}")
        return []

def populate_initial_data():
    """Populate initial fixture data"""
    current_app.logger.info("Starting initial data population")
    
    API_KEY = get_secret()
    if not API_KEY:
        current_app.logger.error("Failed to retrieve API key")
        return

    headers = {
        'x-apisports-key': API_KEY
    }

    league_id = "39"  # Premier League
    season = "2023"   # Current season

    rounds = get_rounds(headers, league_id, season)
    if not rounds:
        current_app.logger.error("No rounds found for the season")
        return

    total_fixtures_added = 0
    
    try:
        for i in range(0, len(rounds), 5):
            batch = rounds[i:i+5]
            current_app.logger.info(f"Processing batch of rounds {i+1}-{i+len(batch)}")
            
            for round_name in batch:
                fixtures = get_fixtures_for_round(headers, league_id, season, round_name)
                
                for fixture in fixtures:
                    try:
                        existing_fixture = Fixture.query.filter_by(
                            fixture_id=fixture['fixture']['id']
                        ).first()
                        
                        if not existing_fixture:
                            new_fixture = Fixture(
                                fixture_id=fixture['fixture']['id'],
                                home_team=fixture['teams']['home']['name'],
                                away_team=fixture['teams']['away']['name'],
                                home_team_logo=fixture['teams']['home']['logo'],
                                away_team_logo=fixture['teams']['away']['logo'],
                                date=fixture['fixture']['date'],
                                league=fixture['league']['name'],
                                season=fixture['league']['season'],
                                round=fixture['league']['round'],
                                status=fixture['fixture']['status']['long'],
                                home_score=fixture['goals']['home'] if fixture['goals']['home'] is not None else 0,
                                away_score=fixture['goals']['away'] if fixture['goals']['away'] is not None else 0
                            )
                            db.session.add(new_fixture)
                            total_fixtures_added += 1
                    except Exception as e:
                        current_app.logger.error(f"Error processing fixture: {str(e)}")
                        db.session.rollback()
                        continue

                try:
                    db.session.commit()
                    current_app.logger.info(f"Committed fixtures for round {round_name}")
                except Exception as e:
                    current_app.logger.error(f"Error committing fixtures: {str(e)}")
                    db.session.rollback()
            
            # Wait between batches
            if i + 5 < len(rounds):
                time.sleep(BATCH_PAUSE)

        current_app.logger.info(f"Completed initial data population. Added {total_fixtures_added} fixtures")

    except Exception as e:
        current_app.logger.error(f"Error in populate_initial_data: {str(e)}")
        db.session.rollback()

def get_fixtures(league_id, season, round_name):
    """Get fixtures for viewing"""
    API_KEY = get_secret()
    if not API_KEY:
        return None

    headers = {'x-apisports-key': API_KEY}
    url = f"{BASE_URL}/fixtures"
    params = {"league": league_id, "season": int(season), "round": round_name}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'response' not in data:
            current_app.logger.error("Invalid API response format")
            return None
            
        return [{
            'home_team': fixture['teams']['home']['name'],
            'away_team': fixture['teams']['away']['name'],
            'home_team_logo': fixture['teams']['home']['logo'],
            'away_team_logo': fixture['teams']['away']['logo'],
            'fixture_id': fixture['fixture']['id']
        } for fixture in data['response']]
    except Exception as e:
        current_app.logger.error(f"Error fetching fixtures: {str(e)}")
        return None

def get_league_id(league_name):
    """Get league ID from name"""
    league_mapping = {
        "Premier League": 39,
        "La Liga": 140,
        "UEFA Champions League": 2
    }
    return league_mapping.get(league_name)