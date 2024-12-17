import requests
import os
import boto3
import time
from botocore.exceptions import ClientError
from app.models import db, Fixture, InitializationStatus
from flask import current_app
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

BASE_URL = "https://v3.football.api-sports.io"

def update_init_status(task, status, details=None):
    """Update initialization status with proper session handling"""
    try:
        init_status = InitializationStatus(
            task=task,
            status=status,
            details=details,
            timestamp=datetime.utcnow()
        )
        db.session.add(init_status)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating initialization status: {str(e)}")

def get_secret():
    """Get API key from AWS Secrets Manager"""
    secret_name = os.environ.get('SECRET_NAME')
    region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    if not secret_name:
        current_app.logger.error("SECRET_NAME environment variable not set")
        return None

    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        response = client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            return response['SecretString']
        
        current_app.logger.error("No SecretString in response")
        return None
    except ClientError as e:
        current_app.logger.error(f"AWS Secrets Manager error: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected error retrieving secret: {str(e)}")
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

        return data['response']
    except Exception as e:
        current_app.logger.error(f"Error fetching rounds: {str(e)}")
        return []

def get_fixtures_for_round(headers, league_id, season, round_name):
    """Get fixtures for a specific round with rate limiting"""
    url = f"{BASE_URL}/fixtures"
    params = {
        "league": league_id,
        "season": int(season),
        "round": round_name
    }

    try:
        # Rate limiting delay
        time.sleep(6)
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        # Check rate limits
        remaining = response.headers.get('x-ratelimit-remaining')
        if remaining and int(remaining) < 5:
            current_app.logger.warning("Close to rate limit, pausing for 60 seconds")
            time.sleep(60)

        if 'errors' in data:
            current_app.logger.error(f"API returned errors: {data['errors']}")
            return []

        fixtures = data.get('response', [])
        
        # Validate fixture IDs
        fixture_ids = [f['fixture']['id'] for f in fixtures]
        if len(fixture_ids) != len(set(fixture_ids)):
            current_app.logger.error(f"Duplicate fixture IDs found in round {round_name}")
            return []

        return fixtures
    except Exception as e:
        current_app.logger.error(f"Error fetching fixtures for round {round_name}: {str(e)}")
        return []

def update_or_create_fixture(fixture_data):
    """Update existing fixture or create new one"""
    try:
        fixture_id = fixture_data['fixture']['id']
        existing_fixture = Fixture.query.filter_by(fixture_id=fixture_id).first()
        
        fixture_dict = {
            'fixture_id': fixture_id,
            'home_team': fixture_data['teams']['home']['name'],
            'away_team': fixture_data['teams']['away']['name'],
            'home_team_logo': fixture_data['teams']['home']['logo'],
            'away_team_logo': fixture_data['teams']['away']['logo'],
            'date': fixture_data['fixture']['date'],
            'league': fixture_data['league']['name'],
            'season': fixture_data['league']['season'],
            'round': fixture_data['league']['round'],
            'status': fixture_data['fixture']['status']['long'],
            'home_score': fixture_data['goals']['home'] if fixture_data['goals']['home'] is not None else 0,
            'away_score': fixture_data['goals']['away'] if fixture_data['goals']['away'] is not None else 0
        }

        if existing_fixture:
            for key, value in fixture_dict.items():
                setattr(existing_fixture, key, value)
            return False  # Not a new fixture
        else:
            new_fixture = Fixture(**fixture_dict)
            db.session.add(new_fixture)
            return True  # New fixture added
    except Exception as e:
        current_app.logger.error(f"Error processing fixture {fixture_data.get('fixture', {}).get('id')}: {str(e)}")
        return False

def populate_initial_data():
    """Populate initial fixture data with improved error handling"""
    current_app.logger.info("Starting initial data population")
    update_init_status('fixture_population', 'in_progress')
    
    API_KEY = get_secret()
    if not API_KEY:
        update_init_status('fixture_population', 'failed', 'Failed to retrieve API key')
        return

    headers = {'x-apisports-key': API_KEY}
    league_id = "39"  # Premier League
    season = "2023"   # Current season

    rounds = get_rounds(headers, league_id, season)
    if not rounds:
        update_init_status('fixture_population', 'failed', 'No rounds found')
        return

    total_fixtures_added = 0
    total_fixtures_updated = 0
    
    try:
        for i in range(0, len(rounds), 5):
            batch = rounds[i:i+5]
            
            for round_name in batch:
                fixtures = get_fixtures_for_round(headers, league_id, season, round_name)
                
                for fixture in fixtures:
                    try:
                        # Begin a new transaction for each fixture
                        with db.session.begin_nested():
                            if update_or_create_fixture(fixture):
                                total_fixtures_added += 1
                            else:
                                total_fixtures_updated += 1
                        
                        # Commit after each fixture
                        db.session.commit()
                    except IntegrityError as e:
                        db.session.rollback()
                        current_app.logger.error(f"Integrity error processing fixture: {str(e)}")
                    except Exception as e:
                        db.session.rollback()
                        current_app.logger.error(f"Error processing fixture: {str(e)}")
            
            # Wait between batches
            if i + 5 < len(rounds):
                time.sleep(30)

        status_message = f'Added {total_fixtures_added} fixtures, updated {total_fixtures_updated}'
        update_init_status('fixture_population', 'completed', status_message)
        current_app.logger.info(f"Completed initial data population. {status_message}")

    except Exception as e:
        update_init_status('fixture_population', 'failed', str(e))
        current_app.logger.error(f"Error in populate_initial_data: {str(e)}")
        db.session.rollback()

def get_fixtures(league_id, season, round_name):
    """Get fixtures with proper error handling"""
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

def is_initialization_complete():
    """Check if data initialization is complete"""
    try:
        latest_status = InitializationStatus.query.order_by(
            InitializationStatus.timestamp.desc()
        ).first()
        return latest_status and latest_status.status == 'completed'
    except Exception as e:
        current_app.logger.error(f"Error checking initialization status: {str(e)}")
        return False