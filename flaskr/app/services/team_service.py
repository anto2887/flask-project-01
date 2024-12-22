from typing import List, Dict, Optional
from flask import current_app
import requests
from datetime import datetime, timezone

class TeamService:
    def __init__(self):
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
            # Check cache first
            if self._should_use_cache(league):
                return self._teams_cache.get(league, [])

            league_id = self.league_ids.get(league)
            if not league_id:
                raise ValueError(f"Unsupported league: {league}")

            teams = self._fetch_teams_from_api(league_id)
            self._update_cache(league, teams)
            return teams

        except Exception as e:
            current_app.logger.error(f"Error fetching teams for {league}: {str(e)}")
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
            api_key = current_app.config['FOOTBALL_API_KEY']
            url = "https://api-football-v1.p.rapidapi.com/v3/teams"
            
            headers = {
                'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
                'x-rapidapi-key': api_key
            }
            
            params = {
                'league': league_id,
                'season': datetime.now().year
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return [{
                'id': team['team']['id'],
                'name': team['team']['name'],
                'logo': team['team']['logo']
            } for team in data.get('response', [])]

        except Exception as e:
            current_app.logger.error(f"API request failed: {str(e)}")
            raise

    def get_team_details(self, team_id: int) -> Optional[Dict]:
        """Get details for a specific team."""
        for teams in self._teams_cache.values():
            for team in teams:
                if team['id'] == team_id:
                    return team
        return None