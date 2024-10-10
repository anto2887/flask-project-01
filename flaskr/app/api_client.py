import requests
from flask import current_app
import os

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

def get_api_key():
    return os.environ.get("API_FOOTBALL_KEY")

def get_headers():
    return {
        "X-RapidAPI-Key": get_api_key(),
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

def get_fixtures(league_id, season, round):
    url = f"{BASE_URL}/fixtures"
    querystring = {"league": league_id, "season": season, "round": f"Regular Season - {round}"}
    
    response = requests.get(url, headers=get_headers(), params=querystring)
    
    if response.status_code == 200:
        return response.json()['response']
    else:
        current_app.logger.error(f"API request failed with status code {response.status_code}")
        return None

def get_league_id(league_name):
    league_mapping = {
        "Premier League": 39,
        "La Liga": 140,
        "UEFA Champions League": 2
    }
    return league_mapping.get(league_name)