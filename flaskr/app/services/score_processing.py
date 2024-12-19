from datetime import datetime
from typing import List, Dict
from flask import current_app
from app.models import Fixture, UserPredictions, UserResults, db
from app.compare import calculate_points

class ScoreProcessingService:
    def __init__(self, football_api_service):
        self.api = football_api_service

    def process_live_matches(self, league_id: int):
        """Process all live matches for a league"""
        try:
            live_matches = self.api.get_live_matches(league_id)
            
            for match in live_matches:
                fixture = Fixture.query.filter_by(
                    fixture_id=match['fixture']['id']
                ).first()
                
                if not fixture:
                    current_app.logger.warning(f"Fixture not found: {match['fixture']['id']}")
                    continue
                    
                self.update_fixture_status(fixture, match)
                
                if match['fixture']['status']['short'] == 'FT':
                    self.process_final_score(fixture, match)
                    
        except Exception as e:
            current_app.logger.error(f"Error processing live matches: {str(e)}")
            raise

    def update_fixture_status(self, fixture: Fixture, match_data: dict):
        """Update fixture status and scores"""
        try:
            fixture.status = match_data['fixture']['status']['long']
            fixture.home_score = match_data['goals']['home']
            fixture.away_score = match_data['goals']['away']
            fixture.last_checked = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating fixture status: {str(e)}")
            raise

    def process_final_score(self, fixture: Fixture, match_data: dict):
        """Process final scores and update user points"""
        try:
            predictions = UserPredictions.query.filter_by(
                fixture_id=fixture.fixture_id,
                processed=False
            ).all()

            for prediction in predictions:
                points = calculate_points(
                    prediction.score1,
                    prediction.score2,
                    match_data['goals']['home'],
                    match_data['goals']['away']
                )

                # Update prediction
                prediction.points = points
                prediction.processed = True

                # Update user results
                user_result = UserResults.query.filter_by(
                    author_id=prediction.author_id,
                    season=fixture.season
                ).first()

                if not user_result:
                    user_result = UserResults(
                        author_id=prediction.author_id,
                        points=0,
                        season=fixture.season
                    )
                    db.session.add(user_result)

                user_result.points += points

            db.session.commit()
            current_app.logger.info(f"Processed final score for fixture {fixture.fixture_id}")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing final score: {str(e)}")
            raise