# compare.py
from app import app
from fuzzywuzzy import process
from app.date_utils import date_init
from app.input import score_input
from app.models import Post, UserResults, UserPredictions, db
from season import get_current_season  # Ensure this import is added

# Function to calculate points based on predictions
def calculate_points(pred_score1, pred_score2, act_score1, act_score2):
    # Check for exact match
    if pred_score1 == act_score1 and pred_score2 == act_score2:
        return 3

    # Determine the predicted and actual outcomes (win, lose, draw)
    pred_outcome = "win" if pred_score1 > pred_score2 else "lose" if pred_score1 < pred_score2 else "draw"
    act_outcome = "win" if act_score1 > act_score2 else "lose" if act_score1 < act_score2 else "draw"

    # Check if the predicted outcome matches the actual outcome
    if pred_outcome == act_outcome:
        return 1

    # If none of the above, return 0 points
    return 0

def compare_and_update(week, league):
    season = get_current_season(league)

    with app.app_context():
        try:
            scraped_data_list = date_init()

            if scraped_data_list is None:
                app.logger.info("No scraped data was found. Exiting the function early.")
                return

            app.logger.info("Scraped data list: %s", scraped_data_list)

            known_teams = [team for match in scraped_data_list for team in [match['home_team'], match['away_team']]]
            sql_statement = '''
                SELECT p.* FROM post p
                WHERE p.week = :week AND p.season = :season
            '''
            posts = db.session.query(Post).from_statement(db.text(sql_statement)).params(week=week, season=season).all()

            if not posts:
                app.logger.info("No posts found. Exiting the function early.")
                return

            for post in posts:
                user_input_results = score_input(post.body)
                app.logger.info("User input results for post ID %s: %s", post.id, user_input_results)

                for result in user_input_results:
                    processed_result = {}
                    for user_team, score in result.items():
                        matched_team, _ = process.extractOne(user_team, known_teams)
                        processed_result[matched_team] = score

                    team1, team2 = processed_result.keys()
                    pred_score1, pred_score2 = processed_result[team1], processed_result[team2]
                    actual_result = next((item for item in scraped_data_list if item['home_team'] == team1 and item['away_team'] == team2), None)

                    if not actual_result:
                        app.logger.info(f"No actual result found for match: {team1} vs {team2}")
                        continue

                    act_score1, act_score2 = actual_result['home_score'], actual_result['away_score']
                    points_to_add = calculate_points(pred_score1, pred_score2, act_score1, act_score2)

                    user_result = UserResults.query.filter_by(author_id=post.author_id, season=season).first()
                    if not user_result:
                        user_result = UserResults(author_id=post.author_id, points=0, season=season)
                        db.session.add(user_result)
                    user_result.points += points_to_add

                    user_prediction = UserPredictions.query.filter_by(author_id=post.author_id, week=week, season=season, team1=team1, team2=team2).first()
                    if not user_prediction:
                        user_prediction = UserPredictions(
                            author_id=post.author_id, week=week, season=season,
                            team1=team1, team2=team2, score1=pred_score1, score2=pred_score2,
                            points=points_to_add
                        )
                        db.session.add(user_prediction)
                    else:
                        user_prediction.points = points_to_add

                    app.logger.info(f"Updating points for author_id {post.author_id}, week {week}, season {season}. New total: {user_result.points}")

                    try:
                        db.session.commit()
                        db.session.refresh(user_result)
                        db.session.refresh(user_prediction)
                        app.logger.info(f"Updated UserResults: author_id {user_result.author_id}, season {user_result.season}, total points: {user_result.points}")
                    except Exception as e:
                        db.session.rollback()
                        app.logger.error("Error during commit: %s", str(e))

        except Exception as e:
            app.logger.exception("An error occurred during the compare_and_update process.")
            raise e
