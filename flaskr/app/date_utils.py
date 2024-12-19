from datetime import datetime, timezone
from flask import current_app
from app.services.football_api import FootballAPIService
from app.services.match_processing import MatchProcessingService
from app.models import db
from app.api_client import get_secret

def daily_update():
    """Perform daily update of fixtures and results"""
    try:
        # Initialize services
        api_key = get_secret()  # Your existing get_secret function
        football_api = FootballAPIService(api_key)
        match_processor = MatchProcessingService(football_api)

        # Process each league
        leagues = {
            "Premier League": 39,
            "La Liga": 140,
            "UEFA Champions League": 2
        }

        for league_name, league_id in leagues.items():
            current_app.logger.info(f"Processing daily update for {league_name}")
            match_processor.process_daily_matches(league_id)

        current_app.logger.info("Daily update completed successfully")

    except Exception as e:
        current_app.logger.error(f"Error in daily update: {str(e)}")
        db.session.rollback()
        raise