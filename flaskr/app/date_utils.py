import datetime
from flask import current_app
from app.api_client import get_fixtures, get_league_id
from app.season import get_current_season
from app.models import db, Post, UserResults, UserPredictions
from app.compare import calculate_points
from app.input import score_input  # Add this import

def daily_update():
    leagues = ["Premier League", "La Liga", "UEFA Champions League"]
    today = datetime.date.today()
   
    for league in leagues:
        season = get_current_season(league)
        league_id = get_league_id(league)
       
        # Fetch fixtures for today
        fixtures = get_fixtures(league_id, season, today)
       
        if fixtures:
            process_fixtures(fixtures, league, season)

def process_fixtures(fixtures, league, season):
    for fixture in fixtures:
        round_number = fixture['league']['round'].split(' - ')[1]
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        home_score = fixture['goals']['home']
        away_score = fixture['goals']['away']
       
        # Fetch predictions for this fixture
        predictions = Post.query.filter_by(
            season=season,
            week=round_number,
            processed=False
        ).all()
       
        for prediction in predictions:
            user_input_results = score_input(prediction.body, league)  # Pass the league parameter
            for result in user_input_results:
                if home_team in result and away_team in result:
                    pred_home_score = result[home_team]
                    pred_away_score = result[away_team]
                    points = calculate_points(pred_home_score, pred_away_score, home_score, away_score)
                   
                    # Update UserResults
                    user_result = UserResults.query.filter_by(author_id=prediction.author_id, season=season).first()
                    if not user_result:
                        user_result = UserResults(author_id=prediction.author_id, points=0, season=season)
                        db.session.add(user_result)
                    user_result.points += points
                   
                    # Update UserPredictions
                    user_prediction = UserPredictions(
                        author_id=prediction.author_id,
                        week=round_number,
                        season=season,
                        team1=home_team,
                        team2=away_team,
                        score1=pred_home_score,
                        score2=pred_away_score,
                        points=points
                    )
                    db.session.add(user_prediction)
                   
                    # Mark prediction as processed
                    prediction.processed = True
       
        db.session.commit()