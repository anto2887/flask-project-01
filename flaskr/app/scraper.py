import requests
import pandas as pd
from io import StringIO

def table_scraper(n):
    standing_url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    data = requests.get(standing_url)

    # Extracting tables matching "Scores & Fixtures" from the HTML content
    matches = pd.read_html(StringIO(data.text), match="Scores & Fixtures")

    # Assuming there's only one table of interest, we'll process the first DataFrame in the list
    df = matches[0]

    # Filter rows based on the value in the "Wk" column
    df_filtered = df[df["Wk"] == n].copy()

    # List of columns to drop
    columns_to_drop = ["Time", "Day", "xG", "xG.1", "Venue", "Referee", "Match Report", "Notes"]

    # Dropping the specified columns
    for column in columns_to_drop:
        if column in df_filtered.columns:
            df_filtered.drop(column, axis=1, inplace=True)

    # Selected teams
    selected_teams = ["Arsenal", "Chelsea", "Manchester Utd", "Manchester City", "Liverpool"]
    
    # Creating a list to store results
    results_list = []

    for _, row in df_filtered.iterrows():
        home_team = row["Home"]
        away_team = row["Away"]
        home_score, away_score = map(int, row["Score"].split('–' if '–' in row["Score"] else '-'))

        if home_team in selected_teams or away_team in selected_teams:
            match_result = {
                home_team: home_score,
                away_team: away_score
            }
            results_list.append(match_result)

    return results_list
