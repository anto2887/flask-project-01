from datetime import datetime, timezone
from typing import Optional, List
from flask import current_app
from app.models import db, Fixture, UserPredictions, UserResults, MatchStatus
from app.services.football_api import FootballAPIService
from datetime import datetime, timedelta, timezone


class MatchProcessingService:
    def __init__(self, football_api: FootballAPIService):
        self.api = football_api

    def process_daily_matches(self, league_id: int):
        """Process all matches for today"""
        try:
            matches = self.api.get_fixtures_by_date(
                league_id=league_id,
                season=datetime.now().year
            )
            
            if not matches:
                current_app.logger.info(f"No matches found for league {league_id}")
                return
            
            for match in matches:
                try:
                    fixture = self._get_or_create_fixture(match)
                    if fixture.status != match['fixture']['status']['long']:
                        self._update_fixture_status(fixture, match)
                except Exception as e:
                    current_app.logger.error(f"Error processing match {match.get('fixture', {}).get('id')}: {str(e)}")
                    continue

        except Exception as e:
            current_app.logger.error(f"Error processing daily matches: {str(e)}")
            raise

    def _get_or_create_fixture(self, match_data: dict) -> Fixture:
        """Get existing fixture or create new one"""
        try:
            fixture = Fixture.query.filter_by(
                fixture_id=match_data['fixture']['id']
            ).first()

            if not fixture:
                # Handle date parsing based on format
                match_date = match_data['fixture']['date']
                if isinstance(match_date, int):
                    fixture_datetime = datetime.fromtimestamp(match_date)
                else:
                    fixture_datetime = datetime.strptime(match_date, '%Y-%m-%dT%H:%M:%S%z')

                fixture = Fixture(
                    fixture_id=match_data['fixture']['id'],
                    home_team=match_data['teams']['home']['name'],
                    away_team=match_data['teams']['away']['name'],
                    home_team_logo=match_data['teams']['home']['logo'],
                    away_team_logo=match_data['teams']['away']['logo'],
                    date=fixture_datetime,
                    league=match_data['league']['name'],
                    season=str(match_data['league']['season']),
                    round=match_data['league']['round'],
                    status=match_data['fixture']['status']['long'],
                    home_score=match_data['goals']['home'] if match_data['goals']['home'] is not None else 0,
                    away_score=match_data['goals']['away'] if match_data['goals']['away'] is not None else 0,
                    venue_city=match_data['fixture']['venue']['city'],
                    competition_id=match_data['league']['id'],
                    match_timestamp=fixture_datetime,
                    last_checked=datetime.now(timezone.utc)
                )
                db.session.add(fixture)
                db.session.commit()

            return fixture

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating/getting fixture: {str(e)}")
            raise

    def _update_fixture_status(self, fixture: Fixture, match_data: dict):
        """Update fixture status and scores"""
        try:
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
            fixture.last_checked = datetime.now(timezone.utc)

            # Add additional scores if available
            if 'score' in match_data:
                if 'halftime' in match_data['score']:
                    fixture.halftime_score = f"{match_data['score']['halftime']['home']}-{match_data['score']['halftime']['away']}"
                if 'fulltime' in match_data['score']:
                    fixture.fulltime_score = f"{match_data['score']['fulltime']['home']}-{match_data['score']['fulltime']['away']}"

            if match_data['fixture']['status']['short'] in ['FT', 'AET', 'PEN']:
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
            current_app.logger.info(f"Processed {len(predictions)} predictions for fixture {fixture.fixture_id}")

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
    
def get_prediction_deadlines():
    """Retrieve prediction deadlines for upcoming fixtures."""
    try:
        # Fetch all upcoming fixtures
        fixtures = Fixture.query.filter(
            Fixture.status == MatchStatus.NOT_STARTED,
            Fixture.date > datetime.now(timezone.utc)
        ).all()

        # Create a dictionary with fixture IDs and their deadlines
        deadlines = {}
        for fixture in fixtures:
            # Assuming prediction deadline is 1 hour before the match starts
            deadline = fixture.date - timedelta(hours=1)
            deadlines[fixture.fixture_id] = deadline.isoformat()

        return deadlines
    except Exception as e:
        current_app.logger.error(f"Error fetching prediction deadlines: {str(e)}")
        return {}