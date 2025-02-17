from datetime import datetime, timezone
from typing import List, Dict
from flask import current_app

from app.models import Fixture, MatchStatus, PredictionStatus
from app.services.score_processing import ScoreProcessingService
from app.services.football_api import FootballAPIService

class MatchMonitorService:
    def __init__(self, football_api_service: FootballAPIService, 
                 score_processor: ScoreProcessingService):
        self.api = football_api_service
        self.score_processor = score_processor

    async def monitor_live_matches(self):
        """Monitor all live matches and process completed ones"""
        try:
            # Get all matches that might need processing
            matches = Fixture.query.filter(
                Fixture.status.in_([
                    MatchStatus.LIVE,
                    MatchStatus.FIRST_HALF,
                    MatchStatus.SECOND_HALF,
                    MatchStatus.HALFTIME,
                    MatchStatus.EXTRA_TIME,
                    MatchStatus.PENALTY
                ])
            ).all()

            for match in matches:
                try:
                    # Get latest match data from API
                    api_data = await self.api.get_fixture_details(match.fixture_id)
                    if not api_data:
                        continue

                    current_status = api_data['fixture']['status']['short']
                    
                    # Check if match has completed
                    if current_status in ['FT', 'AET', 'PEN']:
                        await self.process_completed_match(match, api_data)
                        
                except Exception as e:
                    current_app.logger.error(
                        f"Error monitoring match {match.fixture_id}: {str(e)}"
                    )
                    continue

        except Exception as e:
            current_app.logger.error(f"Error in match monitoring: {str(e)}")
            raise

    async def process_completed_match(self, match: Fixture, api_data: Dict):
        """Process a completed match and update all related data"""
        try:
            # Update match status and scores
            await self.score_processor.update_fixture_status(match, api_data)
            
            # Process predictions and update points
            await self.score_processor.process_final_score(match, api_data)
            
            current_app.logger.info(
                f"Successfully processed completed match {match.fixture_id}"
            )
            
        except Exception as e:
            current_app.logger.error(
                f"Error processing completed match {match.fixture_id}: {str(e)}"
            )
            raise