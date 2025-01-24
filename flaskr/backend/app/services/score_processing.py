from datetime import datetime
from typing import List, Dict
from flask import current_app
from app.models import Fixture, UserPredictions, UserResults, db

class ScoreProcessingService:
    def __init__(self, football_api_service):
        self.api = football_api_service

    def process_live_matches(self, league_id: int):
        """Process all live matches for a league"""
        try:
            # Changed from get_live_matches to get_live_fixtures to match new API
            live_matches = self.api.get_live_fixtures(league_id)
            
            if not live_matches:
                current_app.logger.info(f"No live matches found for league {league_id}")
                return
                
            for match in live_matches:
                try:
                    fixture = Fixture.query.filter_by(
                        fixture_id=match['fixture']['id']
                    ).first()
                    
                    if not fixture:
                        current_app.logger.warning(f"Fixture not found: {match['fixture']['id']}")
                        continue
                        
                    self.update_fixture_status(fixture, match)
                    
                    # Check for both 'FT' and 'Match Finished' status
                    if match['fixture']['status']['short'] in ['FT', 'Match Finished']:
                        self.process_final_score(fixture, match)
                        
                except Exception as e:
                    current_app.logger.error(f"Error processing match {match.get('fixture', {}).get('id')}: {str(e)}")
                    continue
                    
        except Exception as e:
            current_app.logger.error(f"Error processing live matches: {str(e)}")
            raise

    def update_fixture_status(self, fixture: Fixture, match_data: dict):
        """Update fixture status and scores"""
        try:
            # Status mapping to standardize status values
            status_mapping = {
                "1H": "FIRST_HALF",
                "HT": "HALFTIME",
                "2H": "SECOND_HALF",
                "FT": "FINISHED",
                "PEN": "PENALTY",
                "AET": "EXTRA_TIME",
                "LIVE": "LIVE",
                "PST": "POSTPONED",
                "CANC": "CANCELLED"
            }

            api_status = match_data['fixture']['status']['short']
            new_status = status_mapping.get(api_status, match_data['fixture']['status']['long'])

            fixture.status = new_status
            fixture.home_score = match_data['goals']['home'] if match_data['goals']['home'] is not None else fixture.home_score
            fixture.away_score = match_data['goals']['away'] if match_data['goals']['away'] is not None else fixture.away_score
            fixture.last_checked = datetime.utcnow()

            # Add additional scores if available
            if 'score' in match_data:
                if 'halftime' in match_data['score']:
                    fixture.halftime_score = f"{match_data['score']['halftime']['home']}-{match_data['score']['halftime']['away']}"
                if 'fulltime' in match_data['score']:
                    fixture.fulltime_score = f"{match_data['score']['fulltime']['home']}-{match_data['score']['fulltime']['away']}"

            db.session.commit()
            current_app.logger.info(
                f"Updated fixture {fixture.fixture_id}: {fixture.home_team} {fixture.home_score} - "
                f"{fixture.away_score} {fixture.away_team} (Status: {new_status})"
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating fixture status: {str(e)}")
            raise

    def process_final_score(self, fixture: Fixture, match_data: dict):
        """Process final scores and update user points"""
        try:
            # Import inside the function to avoid circular dependency
            from app.compare import calculate_points

            predictions = UserPredictions.query.filter_by(
                fixture_id=fixture.fixture_id,
                processed=False
            ).all()

            if not predictions:
                current_app.logger.info(f"No unprocessed predictions found for fixture {fixture.fixture_id}")
                return

            for prediction in predictions:
                try:
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
                    current_app.logger.info(
                        f"Updated points for user {prediction.author_id}: +{points} points "
                        f"(Fixture: {fixture.fixture_id})"
                    )

                except Exception as e:
                    current_app.logger.error(
                        f"Error processing prediction for user {prediction.author_id}: {str(e)}"
                    )
                    continue

            db.session.commit()
            current_app.logger.info(f"Processed final score for fixture {fixture.fixture_id}")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing final score: {str(e)}")
            raise

    def get_live_scores(self, league_id: int) -> List[Dict]:
        """Get current live scores for a league"""
        try:
            live_fixtures = Fixture.query.filter_by(
                competition_id=league_id
            ).filter(
                Fixture.status.in_(['LIVE', 'FIRST_HALF', 'SECOND_HALF', 'HALFTIME', 'EXTRA_TIME', 'PENALTY'])
            ).all()

            return [{
                'fixture_id': fixture.fixture_id,
                'home_team': fixture.home_team,
                'away_team': fixture.away_team,
                'home_score': fixture.home_score,
                'away_score': fixture.away_score,
                'status': fixture.status,
                'last_updated': fixture.last_checked.isoformat() if fixture.last_checked else None,
                'home_team_logo': fixture.home_team_logo,
                'away_team_logo': fixture.away_team_logo
            } for fixture in live_fixtures]

        except Exception as e:
            current_app.logger.error(f"Error getting live scores: {str(e)}")
            return []