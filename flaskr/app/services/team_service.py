from typing import List, Dict, Optional
from flask import current_app
import requests
from datetime import datetime, timezone

class TeamService:
    def __init__(self, football_api_service):
        self.api = football_api_service
        self.league_ids = {
            "Premier League": 39,
            "La Liga": 140,
            "UEFA Champions League": 2
        }
        
        # Cache teams in memory to reduce API calls
        self._teams_cache = {}
        self._cache_timestamp = None
        self._cache_duration = 3600  # 1 hour

    def get_league_teams(self, league: str) -> List[Dict]:
        """Get all teams for a specific league."""
        try:
            current_app.logger.info(f"Getting teams for league: {league}")
            
            # Check cache first
            if self._should_use_cache(league):
                cached_teams = self._teams_cache.get(league, [])
                current_app.logger.info(f"Returning {len(cached_teams)} teams from cache")
                return cached_teams

            league_id = self.league_ids.get(league)
            if not league_id:
                current_app.logger.error(f"No league ID found for: {league}")
                return []

            current_app.logger.debug(f"Using league ID: {league_id}")
            teams = self._fetch_teams_from_api(league_id)
            
            if teams:
                current_app.logger.info(f"Found {len(teams)} teams from API")
                self._update_cache(league, teams)
                return teams
                
            current_app.logger.warning("No teams found from API")
            return []

        except Exception as e:
            current_app.logger.error(f"Error fetching teams: {str(e)}")
            return []

    def _should_use_cache(self, league: str) -> bool:
        """Check if cached data should be used."""
        if not self._cache_timestamp or league not in self._teams_cache:
            return False

        age = (datetime.now(timezone.utc) - self._cache_timestamp).total_seconds()
        return age < self._cache_duration

    def _update_cache(self, league: str, teams: List[Dict]) -> None:
        """Update the teams cache."""
        self._teams_cache[league] = teams
        self._cache_timestamp = datetime.now(timezone.utc)

    def _fetch_teams_from_api(self, league_id: int) -> List[Dict]:
        """Fetch teams from football API."""
        try:
            current_app.logger.debug(f"Fetching teams for league ID: {league_id}")
            params = {
                'league': league_id,
                'season': datetime.now().year
            }
            
            response = self.api._make_request('teams', params)
            current_app.logger.debug(f"API response received: {response}")
            
            if not response:
                current_app.logger.warning("No response from API")
                return []
                    
            teams = [{
                'id': team['team']['id'],
                'name': team['team']['name'],
                'logo': team['team']['logo'],
                'venue': team['venue']['name'] if 'venue' in team else None,
            } for team in response]

            current_app.logger.info(f"Successfully processed {len(teams)} teams")
            return teams

        except Exception as e:
            current_app.logger.error(f"API request failed: {str(e)}")
            return []

    def get_team_details(self, team_id: int) -> Optional[Dict]:
        """Get details for a specific team."""
        # Check cache first
        for teams in self._teams_cache.values():
            for team in teams:
                if team['id'] == team_id:
                    return team
                    
        # If not in cache, fetch from API
        try:
            params = {'id': team_id}
            response = self.api._make_request('teams', params)
            
            if response and response[0]:
                team_data = response[0]
                return {
                    'id': team_data['team']['id'],
                    'name': team_data['team']['name'],
                    'logo': team_data['team']['logo'],
                    'venue': team_data['venue']['name'] if 'venue' in team_data else None,
                    'founded': team_data['team'].get('founded'),
                    'country': team_data['team'].get('country')
                }
                
        except Exception as e:
            current_app.logger.error(f"Error fetching team details: {str(e)}")
            
        return None