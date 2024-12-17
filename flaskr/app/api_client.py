import requests
import os
import boto3
import time
import random
from botocore.exceptions import ClientError
from app.models import db, Fixture, InitializationStatus
from flask import current_app
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

BASE_URL = "https://v3.football.api-sports.io"
RATE_LIMIT_PAUSE = 15  # Seconds between API calls
BATCH_PAUSE = 60      # Seconds between batches
MIN_RATE_LIMIT = 50   # Minimum remaining calls before forcing pause

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
    try:
        current_app.logger.info("Starting secret retrieval process")
        
        secret_name = os.environ.get('SECRET_NAME')
        current_app.logger.info(f"SECRET_NAME from environment: {secret_name}")
        
        region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        current_app.logger.info(f"AWS region: {region_name}")
        
        if not secret_name:
            current_app.logger.error("SECRET_NAME environment variable not set")
            return None

        # Log IAM context
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            current_app.logger.info(f"AWS Identity: {identity.get('Arn')}")
        except Exception as e:
            current_app.logger.warning(f"Could not get AWS identity: {str(e)}")

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        current_app.logger.info("Attempting to retrieve secret value...")
        response = client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            current_app.logger.info("Successfully retrieved secret value")
            return response['SecretString']
        
        current_app.logger.error("No SecretString in response")
        current_app.logger.debug(f"Response keys available: {list(response.keys())}")
        return None
        
    except Exception as e:
        current_app.logger.error(f"Error in get_secret: {str(e)}", exc_info=True)
        return None

def check_rate_limit(headers):
    """Check API rate limit and pause if necessary"""
    remaining = headers.get('x-ratelimit-remaining')
    if remaining and int(remaining) < MIN_RATE_LIMIT:
        current_app.logger.warning(f"Rate limit low ({remaining} remaining). Pausing for {BATCH_PAUSE} seconds")
        time.sleep(BATCH_PAUSE)
        return False
    return True

def get_rounds(headers, league_id, season):
    """Get all rounds for a given league and season"""
    url = f"{BASE_URL}/fixtures/rounds"
    params = {
        "league": league_id,
        "season": int(season)
    }

    try:
        current_app.logger.info(f"Fetching rounds for league {league_id} season {season}")
        time.sleep(RATE_LIMIT_PAUSE)  # Rate limiting
        
        response = requests.get(url, headers=headers, params=params)
        check_rate_limit(response.headers)
        
        response.raise_for_status()
        data = response.json()
        
        if not data.get('response'):
            current_app.logger.error("No rounds found in response")
            return []

        rounds_count = len(data['response'])
        current_app.logger.info(f"Successfully retrieved {rounds_count} rounds")
        return data['response']
    except Exception as e:
        current_app.logger.error(f"Error fetching rounds: {str(e)}")
        return []

def get_fixtures_for_round(headers, league_id, season, round_name):
    """Get fixtures for a specific round with enhanced rate limiting"""
    try:
        current_app.logger.info(f"Starting fixture retrieval for round {round_name}")
        
        api_key = headers.get('x-apisports-key', '')
        if not api_key:
            current_app.logger.error("No API key in headers")
            return []

        url = f"{BASE_URL}/fixtures"
        params = {
            "league": league_id,
            "season": int(season),
            "round": round_name
        }
        
        # Enhanced rate limiting
        time.sleep(RATE_LIMIT_PAUSE)
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        check_rate_limit(response.headers)
        
        current_app.logger.info(f"Response status code: {response.status_code}")
        
        try:
            data = response.json()
            
            if 'errors' in data and data['errors']:
                current_app.logger.error(f"API errors found: {data['errors']}")
                return []
                
            if 'response' not in data:
                current_app.logger.error(f"No 'response' key in data. Keys found: {list(data.keys())}")
                return []
            
            fixtures = data['response']
            current_app.logger.info(f"Retrieved {len(fixtures)} fixtures for round {round_name}")
            return fixtures
            
        except ValueError as e:
            current_app.logger.error(f"JSON parsing error: {str(e)}")
            return []
            
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
            return False
        else:
            new_fixture = Fixture(**fixture_dict)
            db.session.add(new_fixture)
            return True
    except Exception as e:
        current_app.logger.error(f"Error processing fixture {fixture_data.get('fixture', {}).get('id')}: {str(e)}")
        return False

def populate_initial_data():
    """Populate initial fixture data with improved error handling and rate limiting"""
    current_app.logger.info("Starting initial data population")
    
    if current_app.config.get('DROP_EXISTING_TABLES'):
        try:
            Fixture.query.delete()
            InitializationStatus.query.delete()
            db.session.commit()
            current_app.logger.info("Cleared existing fixtures and initialization status")
        except Exception as e:
            current_app.logger.error(f"Error clearing existing data: {str(e)}")
            db.session.rollback()
            raise
    
    update_init_status('fixture_population', 'in_progress')
    
    API_KEY = get_secret()
    if not API_KEY:
        update_init_status('fixture_population', 'failed', 'Failed to retrieve API key')
        return

    headers = {'x-apisports-key': API_KEY}
    league_id = "39"  # Premier League
    season = "2023"   # Current season

    # Add initial delay to prevent multiple instances from hitting the API simultaneously
    time.sleep(random.randint(1, 30))

    rounds = get_rounds(headers, league_id, season)
    if not rounds:
        update_init_status('fixture_population', 'failed', 'No rounds found')
        return

    total_fixtures_added = 0
    total_fixtures_updated = 0
    
    try:
        for i in range(0, len(rounds), 3):  # Process fewer rounds at a time
            batch = rounds[i:i+3]
            
            for round_name in batch:
                fixtures = get_fixtures_for_round(headers, league_id, season, round_name)
                
                for fixture in fixtures:
                    try:
                        with db.session.begin_nested():
                            if update_or_create_fixture(fixture):
                                total_fixtures_added += 1
                            else:
                                total_fixtures_updated += 1
                        db.session.commit()
                    except IntegrityError as e:
                        db.session.rollback()
                        current_app.logger.error(f"Integrity error processing fixture: {str(e)}")
                    except Exception as e:
                        db.session.rollback()
                        current_app.logger.error(f"Error processing fixture: {str(e)}")
            
            # Longer wait between batches
            if i + 3 < len(rounds):
                time.sleep(BATCH_PAUSE)

        status_message = f'Added {total_fixtures_added} fixtures, updated {total_fixtures_updated}'
        update_init_status('fixture_population', 'completed', status_message)
        current_app.logger.info(f"Completed initial data population. {status_message}")

    except Exception as e:
        update_init_status('fixture_population', 'failed', str(e))
        current_app.logger.error(f"Error in populate_initial_data: {str(e)}")
        db.session.rollback()

def get_fixtures(league_id, season, round_name):
    """Get fixtures with proper error handling and rate limiting"""
    API_KEY = get_secret()
    if not API_KEY:
        return None

    headers = {'x-apisports-key': API_KEY}
    url = f"{BASE_URL}/fixtures"
    params = {"league": league_id, "season": int(season), "round": round_name}
    
    try:
        time.sleep(RATE_LIMIT_PAUSE)  # Rate limiting
        response = requests.get(url, headers=headers, params=params)
        check_rate_limit(response.headers)
        
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