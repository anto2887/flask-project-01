from typing import Optional, List, Dict
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from flask import current_app

class FootballAPIService:
    def __init__(self, api_key: str):
        self.base_url = "https://v3.football.api-sports.io"
        self.session = requests.Session()
        self.session.headers.update({
            'x-apisports-key': api_key
        })

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_live_matches(self, league_id: int) -> List[Dict]:
        """Get all live matches for a league"""
        try:
            response = self.session.get(
                f"{self.base_url}/fixtures",
                params={
                    'league': league_id,
                    'live': 'all'
                }
            )
            response.raise_for_status()
            
            # Log remaining API calls
            remaining = response.headers.get('x-ratelimit-remaining')
            if remaining and int(remaining) < 10:
                current_app.logger.warning(f"API calls remaining: {remaining}")
                
            return response.json()['response']
        except Exception as e:
            current_app.logger.error(f"Error fetching live matches: {str(e)}")
            raise

    def get_fixtures_by_date(self, league_id: int, date: str) -> List[Dict]:
        """Get fixtures for a specific date"""
        try:
            response = self.session.get(
                f"{self.base_url}/fixtures",
                params={
                    'league': league_id,
                    'date': date
                }
            )
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            current_app.logger.error(f"Error fetching fixtures: {str(e)}")
            raise

    def get_fixture_status(self, fixture_id: int) -> Optional[Dict]:
        """Get current status of a specific fixture"""
        try:
            response = self.session.get(
                f"{self.base_url}/fixtures",
                params={'id': fixture_id}
            )
            response.raise_for_status()
            fixtures = response.json()['response']
            return fixtures[0] if fixtures else None
        except Exception as e:
            current_app.logger.error(f"Error fetching fixture status: {str(e)}")
            raise