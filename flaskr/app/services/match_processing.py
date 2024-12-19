from datetime import datetime, timezone
from typing import Optional, List
from flask import current_app
from app.models import db, Fixture, UserPredictions, UserResults
from app.services.football_api import FootballAPIService

class MatchProcessingService:
    def __init__(self, football_api: FootballAPIService):
        self.api = football_api

    def process_daily_matches(self, league_id: int):
        """Process all matches for today"""
        try:
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            matches = self.api.get_fixtures_by_date(league_id, today)
            
            for match in matches:
                fixture = self._get_or_create_fixture(match)
                if fixture.status != match['fixture']['status']['long']:
                    self._update_fixture_status(fixture, match)

        except Exception as e:
            current_app.logger.error(f"Error processing daily matches: {str(e)}")
            raise

    def _get_or_create_fixture(self, match_data: dict) -> Fixture:
        """Get existing fixture or create new one"""
        fixture = Fixture.query.filter_by(
            fixture_id=match_data['fixture']['id']
        ).first()

        if not fixture:
            fixture = Fixture(
                fixture_id=match_data['fixture']['id'],
                home_team=match_data['teams']['home']['name'],
                away_team=match_data['teams']['away']['name'],
                home_team_logo=match_data['teams']['home']['logo'],
                away_team_logo=match_data['teams']['away']['logo'],
                date=datetime.strptime(match_data['fixture']['date'], '%Y-%m-%dT%H:%M:%S%z'),
                league=match_data['league']['name'],
                season=str(match_data['league']['season']),
                round=match_data['league']['round'],
                status=match_data['fixture']['status']['long'],
                home_score=match_data['goals']['home'] or 0,
                away_score=match_data['goals']['away'] or 0,
                venue_city=match_data['fixture']['venue']['city'],
                competition_id=match_data['league']['id'],
                last_checked=datetime.now(timezone.utc)
            )
            db.session.add(fixture)
            db.session.commit()

        return fixture

    def _update_fixture_status(self, fixture: Fixture, match_data: dict):
        """Update fixture status and scores"""
        try:
            fixture.status = match_data['fixture']['status']['long']
            fixture.home_score = match_data['goals']['home'] or 0
            fixture.away_score = match_data['goals']['away'] or 0
            fixture.last_checked = datetime.now(timezone.utc)

            if match_data['fixture']['status']['short'] == 'FT':
                self._process_predictions(fixture)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating fixture status: {str(e)}")
            raise

    def _process_predictions(self, fixture: Fixture):
        """Process predictions for completed match"""
        try:
            predictions = UserPredictions.query.filter_by(
                fixture_id=fixture.fixture_id,
                processed=False
            ).all()

            for prediction in predictions:
                points = self._calculate_points(
                    prediction.score1,
                    prediction.score2,
                    fixture.home_score,
                    fixture.away_score
                )
                
                prediction.points = points
                prediction.processed = True

                # Update user's total points
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

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error processing predictions: {str(e)}")
            raise

    def _calculate_points(self, pred_score1: int, pred_score2: int, 
                         actual_score1: int, actual_score2: int) -> int:
        """Calculate points for a prediction"""
        if pred_score1 == actual_score1 and pred_score2 == actual_score2:
            return 3

        pred_outcome = "win" if pred_score1 > pred_score2 else "lose" if pred_score1 < pred_score2 else "draw"
        actual_outcome = "win" if actual_score1 > actual_score2 else "lose" if actual_score1 < actual_score2 else "draw"

        return 1 if pred_outcome == actual_outcome else 0