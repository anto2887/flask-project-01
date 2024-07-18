import requests
import pandas as pd
from io import StringIO

def scrape_league(url, week):
    data = requests.get(url)
    matches = pd.read_html(StringIO(data.text), match="Scores & Fixtures")
    df = matches[0]
    df_filtered = df[df["Wk"] == week].copy()
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
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'week': week
        }
        results_list.append(match_result)
    return results_list

def table_scraper(week, league='Premier League'):
    if league == 'Premier League':
        url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    elif league == 'La Liga':
        url = "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures"
    else:
        raise ValueError("Unsupported league")
    return scrape_league(url, week)
