import requests
import os
import boto3
import time
from botocore.exceptions import ClientError
from app.models import db, Fixture
from flask import current_app
from datetime import datetime
from app.models import db, Fixture, InitializationStatus

BASE_URL = "https://v3.football.api-sports.io"

def update_init_status(task, status, details=None):
    init_status = InitializationStatus(
        task=task,
        status=status,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.session.add(init_status)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating initialization status: {str(e)}")

def get_secret():
    secret_name = os.environ.get('SECRET_NAME')
    region_name = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    if not secret_name:
        current_app.logger.error("SECRET_NAME environment variable not set")
        return None

    current_app.logger.info(f"Attempting to retrieve secret: {secret_name}")
    current_app.logger.info(f"Using AWS region: {region_name}")
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        current_app.logger.info(f"Making GetSecretValue request with SecretId: {secret_name}")
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        current_app.logger.info("Successfully retrieved secret value")
        if 'SecretString' in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            current_app.logger.error("No SecretString in response")
            return None
    except ClientError as e:
        error_code = e.response['Error'].get('Code', 'Unknown')
        error_message = e.response['Error'].get('Message', 'No message')
        current_app.logger.error(f"Error retrieving secret. Code: {error_code}, Message: {error_message}")
        current_app.logger.error(f"Full error: {str(e)}")
    except Exception as e:
        current_app.logger.error(f"Unexpected error retrieving secret: {str(e)}")
        current_app.logger.error(f"Error type: {type(e)}")
    
    return None

def get_rounds(headers, league_id, season):
    """Get all rounds for a given league and season"""
    url = f"{BASE_URL}/fixtures/rounds"
    params = {
        "league": league_id,
        "season": int(season)
    }

    try:
        current_app.logger.info(f"Fetching rounds for league {league_id}, season {season}")
        current_app.logger.info(f"Request URL: {url}")
        current_app.logger.info(f"Request params: {params}")
        current_app.logger.info(f"Request headers: {headers}")
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        current_app.logger.info(f"Response data: {data}")
        
        # Log rate limit information
        remaining = response.headers.get('x-ratelimit-remaining')
        if remaining:
            current_app.logger.info(f"API calls remaining: {remaining}")
        
        if data.get('response'):
            current_app.logger.info(f"Found {len(data['response'])} rounds")
            return data['response']
        else:
            current_app.logger.error("No rounds found in response")
            return []
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
        current_app.logger.info(f"Request URL: {url}")
        current_app.logger.info(f"Request params: {params}")
        current_app.logger.info(f"Request headers: {headers}")
        
        # Add delay between requests
        time.sleep(6)  # Wait 6 seconds between requests to stay under rate limit
        
        response = requests.get(url, headers=headers, params=params)
        
        # Log rate limit information
        remaining = response.headers.get('x-ratelimit-remaining')
        if remaining:
            current_app.logger.info(f"API calls remaining: {remaining}")
            
        # If we're close to the rate limit, pause
        if remaining and int(remaining) < 5:
            current_app.logger.warning("Close to rate limit, pausing for 60 seconds")
            time.sleep(60)
            
        response.raise_for_status()
        
        data = response.json()
        current_app.logger.info(f"Response data for round {round_name}: {data}")
        
        # Check if we're hitting rate limits
        if 'errors' in data and 'ratelimit' in str(data['errors']).lower():
            current_app.logger.warning("Rate limit reached, waiting for 60 seconds")
            time.sleep(60)
            return []
            
        if 'errors' in data and data['errors'] and len(data['errors']) > 0:
            current_app.logger.error(f"API returned errors for round {round_name}: {data['errors']}")
            return []
            
        fixtures = data.get('response', [])
        current_app.logger.info(f"Found {len(fixtures)} fixtures for round {round_name}")
        return fixtures
    except Exception as e:
        current_app.logger.error(f"Error fetching fixtures for round {round_name}: {str(e)}")
        return []

def populate_initial_data():
    current_app.logger.info("Starting initial data population")
    update_init_status('fixture_population', 'in_progress')
    
    API_KEY = get_secret()
    if not API_KEY:
        update_init_status('fixture_population', 'failed', 'Failed to retrieve API key')
        current_app.logger.error("Failed to retrieve API_FOOTBALL_KEY from Secrets Manager")
        return

    headers = {
        'x-apisports-key': API_KEY
    }

    league_id = "39"  # Premier League
    season = "2023"   # Current season

    # First get all rounds
    rounds = get_rounds(headers, league_id, season)
    if not rounds:
        update_init_status('fixture_population', 'failed', 'No rounds found')
        current_app.logger.error("No rounds found for the season")
        return

    total_fixtures_added = 0
    
    try:
        # Process rounds in batches of 5
        for i in range(0, len(rounds), 5):
            batch = rounds[i:i+5]
            current_app.logger.info(f"Processing batch of rounds {i+1}-{i+len(batch)}")
            
            for round_name in batch:
                current_app.logger.info(f"Processing round: {round_name}")
                fixtures = get_fixtures_for_round(headers, league_id, season, round_name)
                
                fixture_count = 0
                for fixture in fixtures:
                    try:
                        existing_fixture = Fixture.query.filter_by(fixture_id=fixture['fixture']['id']).first()
                        if not existing_fixture:
                            new_fixture = Fixture(
                                fixture_id=fixture['fixture']['id'],
                                home_team=fixture['teams']['home']['name'],
                                away_team=fixture['teams']['away']['name'],
                                home_team_logo=fixture['teams']['home']['logo'],  # Added this
                                away_team_logo=fixture['teams']['away']['logo'],  # Added this
                                date=fixture['fixture']['date'],
                                league=fixture['league']['name'],
                                season=fixture['league']['season'],
                                round=fixture['league']['round'],
                                status=fixture['fixture']['status']['long'],
                                home_score=fixture['goals']['home'] if fixture['goals']['home'] is not None else 0,
                                away_score=fixture['goals']['away'] if fixture['goals']['away'] is not None else 0
                            )
                            db.session.add(new_fixture)
                            fixture_count += 1
                            current_app.logger.info(f"Added new fixture: {new_fixture.home_team} vs {new_fixture.away_team}")
                    except Exception as e:
                        current_app.logger.error(f"Error processing fixture {fixture.get('fixture', {}).get('id')}: {str(e)}")
                        continue

                if fixture_count > 0:
                    try:
                        db.session.commit()
                        total_fixtures_added += fixture_count
                        current_app.logger.info(f"Added {fixture_count} fixtures for round {round_name}")
                    except Exception as e:
                        current_app.logger.error(f"Error committing fixtures for round {round_name}: {str(e)}")
                        db.session.rollback()
            
            # Wait between batches
            if i + 5 < len(rounds):
                current_app.logger.info("Waiting between batches...")
                time.sleep(30)

        update_init_status('fixture_population', 'completed', f'Added {total_fixtures_added} fixtures')
        current_app.logger.info(f"Completed initial data population. Total fixtures added: {total_fixtures_added}")

    except Exception as e:
        update_init_status('fixture_population', 'failed', str(e))
        current_app.logger.error(f"Error in populate_initial_data: {str(e)}")
        db.session.rollback()

def get_fixtures(league_id, season, round):
    API_KEY = get_secret()
    if not API_KEY:
        current_app.logger.error("Failed to retrieve API_FOOTBALL_KEY from Secrets Manager")
        return None

    headers = {
        'x-apisports-key': API_KEY
    }

    url = f"{BASE_URL}/fixtures"
    querystring = {"league": league_id, "season": int(season), "round": round}
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
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

def is_initialization_complete():
    """Check if data initialization is complete"""
    latest_status = InitializationStatus.query.order_by(
        InitializationStatus.timestamp.desc()
    ).first()
    return latest_status and latest_status.status == 'completed'