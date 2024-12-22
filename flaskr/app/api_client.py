import boto3
import os
from botocore.exceptions import ClientError
from flask import current_app
from app.services.football_api import FootballAPIService
from app.services.score_processing import ScoreProcessingService
from app.models import db, Fixture
from datetime import datetime

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

def initialize_services():
    """Initialize API services"""
    api_key = get_secret()
    if not api_key:
        raise ValueError("Failed to retrieve API key")
        
    football_api = FootballAPIService(api_key)
    score_processor = ScoreProcessingService(football_api)
    return football_api, score_processor

def populate_initial_data():
    """Populate initial fixture data"""
    current_app.logger.info("Starting initial data population")
    
    try:
        football_api, _ = initialize_services()
        
        # League IDs
        leagues = {
            "Premier League": 39,
            "La Liga": 140,
            "UEFA Champions League": 2
        }
        
        for league_name, league_id in leagues.items():
            current_app.logger.info(f"Processing league: {league_name}")
            
            # Get current season fixtures
            fixtures = football_api.get_fixtures_by_date(league_id=league_id, date=datetime.now().strftime('%Y-%m-%d'))
            
            if not fixtures:
                current_app.logger.info(f"No fixtures found for {league_name}")
                continue
            
            for fixture_data in fixtures:
                try:
                    existing_fixture = Fixture.query.filter_by(
                        fixture_id=fixture_data['fixture']['id']
                    ).first()
                    
                    if not existing_fixture:
                        new_fixture = Fixture(
                            fixture_id=fixture_data['fixture']['id'],
                            home_team=fixture_data['teams']['home']['name'],
                            away_team=fixture_data['teams']['away']['name'],
                            home_team_logo=fixture_data['teams']['home']['logo'],
                            away_team_logo=fixture_data['teams']['away']['logo'],
                            date=datetime.strptime(fixture_data['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z'),
                            league=league_name,
                            season=str(fixture_data['league']['season']),
                            round=fixture_data['league']['round'],
                            status=fixture_data['fixture']['status']['long'],
                            home_score=fixture_data['goals']['home'] if fixture_data['goals']['home'] is not None else 0,
                            away_score=fixture_data['goals']['away'] if fixture_data['goals']['away'] is not None else 0,
                            venue_city=fixture_data['fixture']['venue']['city'],
                            competition_id=league_id,
                            match_timestamp=datetime.strptime(fixture_data['fixture']['timestamp'], '%Y-%m-%dT%H:%M:%S%z'),
                            last_checked=datetime.utcnow()
                        )
                        db.session.add(new_fixture)
                        current_app.logger.info(f"Added new fixture: {new_fixture.home_team} vs {new_fixture.away_team}")
                    
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error processing fixture: {str(e)}")
                    continue
                
        current_app.logger.info("Completed initial data population")
        
    except Exception as e:
        current_app.logger.error(f"Error in populate_initial_data: {str(e)}")
        raise

def get_fixtures(league_id: int, season: str, round_name: str = None):
    """Get fixtures for viewing"""
    try:
        football_api, _ = initialize_services()
        
        params = {
            'league': league_id,
            'season': season
        }
        if round_name:
            params['round'] = round_name
            
        fixtures = football_api.get_fixtures_by_date(**params)
        
        if not fixtures:
            current_app.logger.warning("No fixtures found")
            return None
            
        return [{
            'home_team': fixture['teams']['home']['name'],
            'away_team': fixture['teams']['away']['name'],
            'home_team_logo': fixture['teams']['home']['logo'],
            'away_team_logo': fixture['teams']['away']['logo'],
            'fixture_id': fixture['fixture']['id']
        } for fixture in fixtures]
        
    except Exception as e:
        current_app.logger.error(f"Error fetching fixtures: {str(e)}")
        return None

def get_league_id(league_name: str) -> int:
    """Get league ID from name"""
    league_mapping = {
        "Premier League": 39,
        "La Liga": 140,
        "UEFA Champions League": 2
    }
    return league_mapping.get(league_name)

def process_live_scores():
    """Process live scores for all leagues"""
    try:
        _, score_processor = initialize_services()
        
        for league_name, league_id in {
            "Premier League": 39,
            "La Liga": 140,
            "UEFA Champions League": 2
        }.items():
            current_app.logger.info(f"Processing live scores for {league_name}")
            score_processor.process_live_matches(league_id)
            
    except Exception as e:
        current_app.logger.error(f"Error processing live scores: {str(e)}")
        raise
