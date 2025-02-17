from datetime import datetime, timezone
from typing import List, Dict
from flask import current_app
from app.models import (
    Fixture, UserPredictions, UserResults, db, 
    MatchStatus, PredictionStatus, Group
)

class ScoreProcessingService:
    def __init__(self, football_api_service):
        self.api = football_api_service

    def process_live_matches(self, league_id: int):
        """Process all live matches for a league"""
        try:
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
                    
                    # Check for match completion
                    if match['fixture']['status']['short'] in ['FT', 'AET', 'PEN', 'Match Finished']:
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
            status_mapping = {
                "1H": MatchStatus.FIRST_HALF,
                "HT": MatchStatus.HALFTIME,
                "2H": MatchStatus.SECOND_HALF,
                "FT": MatchStatus.FINISHED,
                "PEN": MatchStatus.PENALTY,
                "AET": MatchStatus.EXTRA_TIME,
                "LIVE": MatchStatus.LIVE,
                "PST": MatchStatus.POSTPONED,
                "CANC": MatchStatus.CANCELLED
            }

            api_status = match_data['fixture']['status']['short']
            new_status = status_mapping.get(api_status, MatchStatus.LIVE)

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
                if 'extratime' in match_data['score']:
                    fixture.extratime_score = f"{match_data['score']['extratime']['home']}-{match_data['score']['extratime']['away']}"
                if 'penalty' in match_data['score']:
                    fixture.penalty_score = f"{match_data['score']['penalty']['home']}-{match_data['score']['penalty']['away']}"

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
            predictions = UserPredictions.query.filter_by(
                fixture_id=fixture.fixture_id,
                prediction_status=PredictionStatus.LOCKED
            ).all()

            if not predictions:
                current_app.logger.info(f"No unprocessed predictions found for fixture {fixture.fixture_id}")
                return

            for prediction in predictions:
                try:
                    points = self._calculate_points(
                        prediction.score1,
                        prediction.score2,
                        match_data['goals']['home'],
                        match_data['goals']['away']
                    )

                    # Update prediction
                    prediction.points = points
                    prediction.prediction_status = PredictionStatus.PROCESSED
                    prediction.processed_at = datetime.now(timezone.utc)

                    # Get user's leagues and update points
                    user_leagues = Group.query.join(
                        Group.member_roles
                    ).filter(
                        Group.member_roles.any(user_id=prediction.author_id)
                    ).all()

                    # Update user season results
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

                    # Update league tables
                    for league in user_leagues:
                        self._update_league_table(league.id, prediction.author_id, points)

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

    def _calculate_points(self, pred_home: int, pred_away: int, 
                         actual_home: int, actual_away: int) -> int:
        """Calculate prediction points"""
        # Exact score match
        if pred_home == actual_home and pred_away == actual_away:
            return 3
            
        # Correct result but wrong score
        pred_result = pred_home - pred_away
        actual_result = actual_home - actual_away
        if (pred_result > 0 and actual_result > 0) or \
           (pred_result < 0 and actual_result < 0) or \
           (pred_result == 0 and actual_result == 0):
            return 1
            
        return 0

    def _update_league_table(self, league_id: int, user_id: int, points: int) -> None:
        """Update league table with new points"""
        try:
            league = Group.query.get(league_id)
            if not league:
                return

            # Update user's points in the league
            member = next((m for m in league.member_roles if m.user_id == user_id), None)
            if member:
                member.points = (member.points or 0) + points
                current_app.logger.info(
                    f"Updated league table for user {user_id} in league {league_id}: +{points} points"
                )

        except Exception as e:
            current_app.logger.error(f"Error updating league table: {str(e)}")
            raise

    def get_live_scores(self, league_id: int) -> List[Dict]:
        """Get current live scores for a league"""
        try:
            live_fixtures = Fixture.query.filter_by(
                competition_id=league_id
            ).filter(
                Fixture.status.in_([
                    MatchStatus.LIVE,
                    MatchStatus.FIRST_HALF,
                    MatchStatus.SECOND_HALF,
                    MatchStatus.HALFTIME,
                    MatchStatus.EXTRA_TIME,
                    MatchStatus.PENALTY
                ])
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