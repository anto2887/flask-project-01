# compare.py
from app import app
from fuzzywuzzy import process
from app.date_utils import date_init
from app.input import score_input
from app.models import Post, UserResults, Group, db

# Function to calculate points based on predictions
def calculate_points(pred_score1, pred_score2, act_score1, act_score2):
    if pred_score1 == act_score1 and pred_score2 == act_score2:
        return 3
    pred_outcome = "win" if pred_score1 > pred_score2 else "lose" if pred_score1 < pred_score2 else "draw"
    act_outcome = "win" if act_score1 > act_score2 else "lose" if act_score1 < act_score2 else "draw"
    if pred_outcome == act_outcome:
        return 1
    return 0

def compare_and_update(group_id):
    with app.app_context():
        try:
            group = Group.query.get(group_id)
            if not group:
                app.logger.info(f"No group found with ID: {group_id}")
                return

            scraped_data_list = date_init(group.league)
            if scraped_data_list is None:
                app.logger.info("No scraped data was found. Exiting the function early.")
                return

            known_teams = [team for match in scraped_data_list for team in match]
            sql_statement = '''
                SELECT p.* FROM post p
                WHERE p.group_id = :group_id AND p.id = (
                    SELECT MAX(pp.id) FROM post pp WHERE pp.author_id = p.author_id
                )
            '''
            posts = db.session.query(Post).from_statement(db.text(sql_statement)).params(group_id=group_id).all()

            if not posts:
                app.logger.info("No posts found. Exiting the function early.")
                return

            for post in posts:
                user_input_results = score_input(post.body)
                for result in user_input_results:
                    processed_result = {}
                    for user_team, score in result.items():
                        matched_team, _ = process.extractOne(user_team, known_teams)
                        processed_result[matched_team] = score

                    team1, team2 = processed_result.keys()
                    pred_score1, pred_score2 = processed_result[team1], processed_result[team2]
                    actual_result = next((item for item in scraped_data_list if team1 in item and team2 in item), None)

                    if not actual_result:
                        continue

                    act_score1, act_score2 = actual_result[team1], actual_result[team2]
                    points_to_add = calculate_points(pred_score1, pred_score2, act_score1, act_score2)
                    user_result = UserResults.query.filter_by(author_id=post.author_id, group_id=group_id).first()
                    if not user_result:
                        user_result = UserResults(author_id=post.author_id, points=0, group_id=group_id)
                        db.session.add(user_result)

                    user_result.points += points_to_add
                    try:
                        db.session.commit()
                        db.session.refresh(user_result)
                    except Exception as e:
                        db.session.rollback()
                        app.logger.error("Error during commit: %s", str(e))

        except Exception as e:
            app.logger.exception("An error occurred during the compare_and_update process.")
            raise e
