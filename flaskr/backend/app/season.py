from datetime import datetime

SEASON_START_DATE = {
    "Premier League": "2024-08-01",
    "La Liga": "2024-08-01",
    "UEFA Champions League": "2024-09-01"
}

def get_current_season(league):
    start_date = datetime.strptime(SEASON_START_DATE[league], "%Y-%m-%d")
    current_date = datetime.utcnow()
    current_year = current_date.year
    next_year = current_year + 1

    # If current date is before start date, adjust the season
    if current_date < start_date.replace(year=current_year):
        current_year -= 1
        next_year -= 1

    return f"{current_year}-{next_year}"
