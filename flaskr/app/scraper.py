# scraper.py
import requests
import pandas as pd
from io import StringIO

# URL mappings for different leagues
LEAGUE_URLS = {
    'Premier League': "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures",
    'La Liga': "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures",
    'UCL': "https://fbref.com/en/comps/8/schedule/Champions-League-Scores-and-Fixtures"
}

def table_scraper(n, league):
    if league not in LEAGUE_URLS:
        raise ValueError("Unsupported league.")

    standing_url = LEAGUE_URLS[league]
    data = requests.get(standing_url)

    matches = pd.read_html(StringIO(data.text), match="Scores & Fixtures")
    df = matches[0]
    df_filtered = df[df["Wk"] == n].copy()

    columns_to_drop = ["Time", "Day", "xG", "xG.1", "Venue", "Referee", "Match Report", "Notes"]
    for column in columns_to_drop:
        if column in df_filtered.columns:
            df_filtered.drop(column, axis=1, inplace=True)

    results_list = []
    for _, row in df_filtered.iterrows():
        home_team = row["Home"]
        away_team = row["Away"]
        home_score, away_score = map(int, row["Score"].split('–' if '–' in row["Score"] else '-'))

        match_result = {
            home_team: home_score,
            away_team: away_score
        }
        results_list.append(match_result)

    return results_list
