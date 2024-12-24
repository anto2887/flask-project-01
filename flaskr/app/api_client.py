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
    """Initialize API services with proper error handling"""
    try:
        api_key = get_secret()
        if not api_key:
            current_app.logger.error("Failed to retrieve API key")
            raise ValueError("Failed to retrieve API key")
            
        football_api = FootballAPIService(api_key)
        score_processor = ScoreProcessingService(football_api)
        
        current_app.logger.info("Successfully initialized API services")
        return football_api, score_processor
        
    except Exception as e:
        current_app.logger.error(f"Error initializing services: {str(e)}")
        raise

def populate_initial_data():
    """Populate initial fixture data with enhanced error handling"""
    current_app.logger.info("Starting initial data population")
    
    try:
        football_api, _ = initialize_services()
        
        leagues = {
            "Premier League": 39,
            "La Liga": 140,
            "UEFA Champions League": 2
        }
        
        season = 2024

        status_mapping = {
            "Not Started": "NOT_STARTED",
            "Live": "LIVE",
            "Halftime": "HALFTIME",
            "Finished": "FINISHED",
            "Postponed": "POSTPONED",
            "Cancelled": "CANCELLED"
        }

        for league_name, league_id in leagues.items():
            current_app.logger.info(f"Processing league: {league_name} for season {season}")
            
            fixtures = football_api.get_fixtures_by_season(league_id=league_id, season=season)
            
            if not fixtures:
                current_app.logger.info(f"No fixtures found for {league_name} in season {season}")
                continue
            
            for fixture_data in fixtures:
                try:
                    fixture_date = fixture_data['fixture']['date']
                    if isinstance(fixture_date, int):
                        fixture_datetime = datetime.fromtimestamp(fixture_date)
                    else:
                        fixture_datetime = datetime.strptime(fixture_date, '%Y-%m-%dT%H:%M:%S%z')
                    
                    status = status_mapping.get(
                        fixture_data['fixture']['status']['long'],
                        "NOT_STARTED"
                    )
                    
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
                            date=fixture_datetime,
                            league=league_name,
                            season=str(season),
                            round=fixture_data['league']['round'],
                            status=status,
                            home_score=fixture_data['goals']['home'] if fixture_data['goals']['home'] is not None else 0,
                            away_score=fixture_data['goals']['away'] if fixture_data['goals']['away'] is not None else 0,
                            venue_city=fixture_data['fixture']['venue']['city'],
                            competition_id=league_id,
                            match_timestamp=fixture_datetime,
                            last_checked=datetime.utcnow()
                        )
                        db.session.add(new_fixture)
                        current_app.logger.info(f"Added new fixture: {new_fixture.home_team} vs {new_fixture.away_team}")
                    else:
                        # Update existing fixture with new data
                        existing_fixture.status = status
                        existing_fixture.home_score = fixture_data['goals']['home'] if fixture_data['goals']['home'] is not None else existing_fixture.home_score
                        existing_fixture.away_score = fixture_data['goals']['away'] if fixture_data['goals']['away'] is not None else existing_fixture.away_score
                        existing_fixture.last_checked = datetime.utcnow()
                        current_app.logger.info(f"Updated existing fixture: {existing_fixture.home_team} vs {existing_fixture.away_team}")
                    
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
    """Get fixtures for viewing with enhanced error handling"""
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
            'fixture_id': fixture['fixture']['id'],
            'status': fixture['fixture']['status']['long'],
            'date': fixture['fixture']['date'],
            'venue_city': fixture['fixture']['venue']['city'],
            'goals': {
                'home': fixture['goals']['home'],
                'away': fixture['goals']['away']
            }
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
    """Process live scores for all leagues with enhanced error handling"""
    try:
        _, score_processor = initialize_services()
        
        leagues = {
            "Premier League": 39,
            "La Liga": 140,
            "UEFA Champions League": 2
        }
        
        for league_name, league_id in leagues.items():
            current_app.logger.info(f"Processing live scores for {league_name}")
            try:
                score_processor.process_live_matches(league_id)
            except Exception as e:
                current_app.logger.error(f"Error processing live scores for {league_name}: {str(e)}")
                continue
            
    except Exception as e:
        current_app.logger.error(f"Error in process_live_scores: {str(e)}")
        raise