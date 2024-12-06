import requests
import os
import boto3
from botocore.exceptions import ClientError
from app.models import db, Fixture
from flask import current_app

BASE_URL = "https://v3.football.api-sports.io"

def get_secret():
    secret_name = "football_api_key"  # Hard-coded secret name
    region_name = "us-east-1"         # Hard-coded region
    
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

def get_rounds(headers, league_id, season):
    """Get all rounds for a given league and season"""
    url = f"{BASE_URL}/fixtures/rounds"
    params = {
        "league": league_id,
        "season": season
    }

    try:
        current_app.logger.info(f"Fetching rounds for league {league_id}, season {season}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
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
        "season": season,
        "round": round_name
    }

    try:
        current_app.logger.info(f"Fetching fixtures for round: {round_name}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('response', [])
    except Exception as e:
        current_app.logger.error(f"Error fetching fixtures for round {round_name}: {str(e)}")
        return []

def populate_initial_data():
    current_app.logger.info("Starting initial data population")
    
    API_KEY = get_secret()
    if not API_KEY:
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
        current_app.logger.error("No rounds found for the season")
        return

    total_fixtures_added = 0
    
    try:
        # Process each round
        for round_name in rounds:
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

        current_app.logger.info(f"Completed initial data population. Total fixtures added: {total_fixtures_added}")

    except Exception as e:
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
    querystring = {"league": league_id, "season": season, "round": round}
    
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