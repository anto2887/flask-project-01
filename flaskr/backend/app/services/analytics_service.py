from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, and_, case
from flask import current_app
import json

from app.models import (
    Group, Users, UserPredictions, GroupAnalytics, 
    PredictionStatus, Fixture, MatchStatus
)
from app.db import db
from app.services.cache_service import CacheService

class AnalyticsService:
    def __init__(self):
        self.cache = CacheService()

    def generate_group_analytics(self, group_id: int) -> Dict:
        """Generate comprehensive analytics for a group."""
        try:
            try:
                cache_key = f"group_analytics:{group_id}"
                cached_data = self.cache.get(cache_key)
                if cached_data:
                    return cached_data
            except Exception as cache_error:
                current_app.logger.warning(f"Cache retrieval failed: {str(cache_error)}")

            analytics = {
                'overall_stats': self._get_overall_stats(group_id),
                'member_performance': self._get_member_performance(group_id),
                'prediction_patterns': self._get_prediction_patterns(group_id),
                'weekly_trends': self._get_weekly_trends(group_id),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }

            # Store in database for historical tracking
            self._store_analytics(group_id, analytics)
            
            # Try to cache, but don't fail if cache is unavailable
            try:
                self.cache.set(cache_key, analytics, timeout=3600)  # 1 hour cache
            except Exception as cache_error:
                current_app.logger.warning(f"Cache storage failed: {str(cache_error)}")
            
            return analytics

        except Exception as e:
            current_app.logger.error(f"Error generating group analytics: {str(e)}")
            return {
                'overall_stats': {},
                'member_performance': [],
                'prediction_patterns': {},
                'weekly_trends': [],
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'error': 'Error generating analytics'
            }

    def _get_overall_stats(self, group_id: int) -> Dict:
        """Get overall group statistics."""
        try:
            group = Group.query.get(group_id)
            
            # Get all predictions for the group
            predictions = UserPredictions.query.join(
                Fixture
            ).filter(
                Fixture.league == group.league,
                UserPredictions.prediction_status == PredictionStatus.PROCESSED
            ).all()

            total_predictions = len(predictions)
            if not total_predictions:
                return {
                    'total_predictions': 0,
                    'average_points': 0,
                    'perfect_predictions': 0,
                    'participation_rate': 0
                }

            perfect_predictions = sum(1 for p in predictions if p.points == 3)
            total_points = sum(p.points for p in predictions)

            return {
                'total_predictions': total_predictions,
                'average_points': round(total_points / total_predictions, 2),
                'perfect_predictions': perfect_predictions,
                'participation_rate': self._calculate_participation_rate(group_id)
            }

        except Exception as e:
            current_app.logger.error(f"Error getting overall stats: {str(e)}")
            return {}

    def _get_member_performance(self, group_id: int) -> List[Dict]:
        """Get detailed member performance statistics."""
        try:
            group = Group.query.get(group_id)
            
            results = db.session.query(
                Users.username,
                func.count(UserPredictions.id).label('total_predictions'),
                func.sum(UserPredictions.points).label('total_points'),
                func.avg(UserPredictions.points).label('average_points'),
                func.sum(case(whens=[(UserPredictions.points == 3, 1)], else_=0)).label('perfect_predictions')
            ).join(
                UserPredictions, Users.id == UserPredictions.author_id
            ).join(
                Fixture, UserPredictions.fixture_id == Fixture.fixture_id
            ).filter(
                Fixture.league == group.league,
                UserPredictions.prediction_status == PredictionStatus.PROCESSED
            ).group_by(
                Users.username
            ).all()

            return [{
                'username': r.username,
                'total_predictions': r.total_predictions,
                'total_points': int(r.total_points or 0),
                'average_points': round(float(r.average_points or 0), 2),
                'perfect_predictions': int(r.perfect_predictions or 0)
            } for r in results]

        except Exception as e:
            current_app.logger.error(f"Error getting member performance: {str(e)}")
            return []

    def _get_prediction_patterns(self, group_id: int) -> Dict:
        """Analyze prediction patterns within the group."""
        try:
            group = Group.query.get(group_id)
            
            predictions = UserPredictions.query.join(
                Fixture
            ).filter(
                Fixture.league == group.league,
                UserPredictions.prediction_status == PredictionStatus.PROCESSED
            ).all()

            patterns = {
                'home_bias': self._calculate_home_bias(predictions),
                'score_distribution': self._analyze_score_distribution(predictions),
                'success_by_team': self._analyze_team_success(predictions),
                'time_based_accuracy': self._analyze_time_based_accuracy(predictions)
            }

            return patterns

        except Exception as e:
            current_app.logger.error(f"Error analyzing prediction patterns: {str(e)}")
            return {}

    def _get_weekly_trends(self, group_id: int) -> List[Dict]:
        """Get weekly performance trends."""
        try:
            group = Group.query.get(group_id)
            
            weeks = db.session.query(
                UserPredictions.week
            ).join(
                Fixture
            ).filter(
                Fixture.league == group.league,
                UserPredictions.prediction_status == PredictionStatus.PROCESSED
            ).distinct().order_by(
                UserPredictions.week.desc()
            ).limit(10).all()

            trends = []
            for week in weeks:
                week_num = week[0]
                stats = self._calculate_weekly_stats(group_id, week_num)
                trends.append({
                    'week': week_num,
                    'stats': stats
                })

            return trends

        except Exception as e:
            current_app.logger.error(f"Error getting weekly trends: {str(e)}")
            return []

    def _calculate_participation_rate(self, group_id: int) -> float:
        """Calculate member participation rate."""
        try:
            group = Group.query.get(group_id)
            total_members = len(group.users)
            if not total_members:
                return 0.0

            active_predictors = db.session.query(
                func.count(func.distinct(UserPredictions.author_id))
            ).join(
                Fixture
            ).filter(
                Fixture.league == group.league,
                UserPredictions.prediction_status == PredictionStatus.PROCESSED
            ).scalar()

            return round((active_predictors or 0) / total_members * 100, 2)

        except Exception as e:
            current_app.logger.error(f"Error calculating participation rate: {str(e)}")
            return 0.0

    def _store_analytics(self, group_id: int, data: Dict) -> None:
        """Store analytics data in database."""
        try:
            now = datetime.now(timezone.utc)
            week_number = now.isocalendar()[1]
            
            analytics = GroupAnalytics(
                group_id=group_id,
                analysis_type='weekly',
                period=f"{now.year}-W{week_number}",
                data=data
            )
            
            db.session.add(analytics)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error storing analytics: {str(e)}")

    def _calculate_home_bias(self, predictions: List[UserPredictions]) -> Dict:
        """Calculate home team prediction bias."""
        total = len(predictions)
        if not total:
            return {'rate': 0, 'accuracy': 0}

        home_wins_predicted = sum(1 for p in predictions if p.score1 > p.score2)
        home_wins_correct = sum(1 for p in predictions 
                              if p.score1 > p.score2 and p.points > 0)

        return {
            'rate': round(home_wins_predicted / total * 100, 2) if total else 0,
            'accuracy': round(home_wins_correct / home_wins_predicted * 100, 2) if home_wins_predicted else 0
        }

    def _analyze_score_distribution(self, predictions: List[UserPredictions]) -> Dict:
        """Analyze the distribution of predicted scores."""
        scores = {}
        for pred in predictions:
            score_key = f"{pred.score1}-{pred.score2}"
            if score_key not in scores:
                scores[score_key] = {'count': 0, 'correct': 0}
            scores[score_key]['count'] += 1
            if pred.points == 3:
                scores[score_key]['correct'] += 1

        # Sort by frequency and get top 5
        return dict(sorted(
            scores.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:5])

    def _analyze_team_success(self, predictions: List[UserPredictions]) -> Dict:
        """Analyze prediction success rates by team."""
        team_stats = {}
        for pred in predictions:
            fixture = pred.fixture
            for team in [fixture.home_team, fixture.away_team]:
                if team not in team_stats:
                    team_stats[team] = {'total': 0, 'correct': 0}
                team_stats[team]['total'] += 1
                if pred.points > 0:
                    team_stats[team]['correct'] += 1

        return {
            team: {
                'success_rate': round(stats['correct'] / stats['total'] * 100, 2) if stats['total'] else 0,
                'predictions': stats['total']
            }
            for team, stats in team_stats.items()
        }

    def _analyze_time_based_accuracy(self, predictions: List[UserPredictions]) -> Dict:
        """Analyze prediction accuracy based on submission timing."""
        time_brackets = {
            'early': {'count': 0, 'correct': 0},  # >24h before
            'normal': {'count': 0, 'correct': 0}, # 12-24h before
            'late': {'count': 0, 'correct': 0}    # <12h before
        }

        for pred in predictions:
            if not pred.submission_time:
                continue
                
            fixture_time = pred.fixture.date
            submission_time = pred.submission_time
            hours_before = (fixture_time - submission_time).total_seconds() / 3600
            
            if hours_before > 24:
                bracket = 'early'
            elif hours_before > 12:
                bracket = 'normal'
            else:
                bracket = 'late'

            time_brackets[bracket]['count'] += 1
            if pred.points > 0:
                time_brackets[bracket]['correct'] += 1

        return {
            bracket: {
                'accuracy': round(stats['correct'] / stats['count'] * 100, 2) if stats['count'] else 0,
                'predictions': stats['count']
            }
            for bracket, stats in time_brackets.items()
        }

    def _calculate_weekly_stats(self, group_id: int, week: int) -> Dict:
        """Calculate statistics for a specific week."""
        try:
            group = Group.query.get(group_id)
            
            predictions = UserPredictions.query.join(
                Fixture
            ).filter(
                Fixture.league == group.league,
                UserPredictions.week == week,
                UserPredictions.prediction_status == PredictionStatus.PROCESSED
            ).all()

            if not predictions:
                return {
                    'average_points': 0,
                    'participation': 0,
                    'perfect_predictions': 0
                }

            total_points = sum(p.points for p in predictions)
            perfect_predictions = sum(1 for p in predictions if p.points == 3)
            participants = len(set(p.author_id for p in predictions))

            return {
                'average_points': round(total_points / len(predictions), 2),
                'participation': round(participants / len(group.users) * 100, 2) if len(group.users) > 0 else 0,
                'perfect_predictions': perfect_predictions
            }

        except Exception as e:
            current_app.logger.error(f"Error calculating weekly stats: {str(e)}")
            return {}