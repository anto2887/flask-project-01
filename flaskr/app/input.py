from app import app
import re
from app.models import Post, db

# Define team_name_mapping
team_name_mapping = {
    "Manchester City": ["Manchester City", "Man City", "Manchester City FC"],
    "Arsenal": ["Arsenal FC", "Arsenal"],
    "Liverpool": ["Liverpool", "Liverpool FC"],
    "Chelsea": ["Chelsea FC", "Chelsea"],
    "Manchester United": ["Manchester Utd", "Man Utd", "Manchester United FC"],
    "Newcastle United": ["Newcastle United", "Newcastle", "Newcastle Utd"],
    "Tottenham Hotspur": ["Tottenham", "Spurs", "Tottenham Hotspur FC"],
    "Aston Villa": ["Aston Villa", "Villa", "Aston Villa FC"],
    "Brighton and Hove Albion": ["Brighton", "Brighton & Hove Albion", "Brighton and Hove"],
    "Burnley": ["Burnley FC", "Burnley"],
    "West Ham United": ["West Ham", "West Ham United", "West Ham Utd"],
    "Crystal Palace": ["Crystal Palace", "Crystal Palace FC"],
    "Everton": ["Everton FC", "Everton"],
    "AFC Bournemouth": ["Bournemouth", "AFC Bournemouth"],
    "Brentford": ["Brentford FC", "Brentford"],
    "Fulham": ["Fulham FC", "Fulham"],
    "Wolverhampton Wanderers": ["Wolves", "Wolverhampton", "Wolverhampton Wanderers"],
    "Nottingham Forest": ["Nottingham Forest", "Nott'm Forest", "Forest", "Nott'ham Forest"],
    "Luton Town": ["Luton Town", "Luton"],
    "Sheffield United": ["Sheffield United", "Sheffield Utd"]
    # Add other teams and variations as necessary
}

# Function to standardize team names
def standardize_team_name(name):
    for standard, variations in team_name_mapping.items():
        if name in variations:
            return standard
    return name  # Return the original name if no match is found

def score_input(input_str=None):
    with app.app_context():
        # Fetch the latest 'body' entry from the 'post' table
        latest_post = db.session.query(Post).order_by(Post.created.desc()).first()

        if not latest_post:
            return None  # No entry found

        # If no input_str is provided, fetch from the latest post
        if input_str is None:
            input_str = latest_post.body

        # Splitting the input by lines and commas
        if '\n' in input_str:
            lines = input_str.strip().split('\n')
        else:
            lines = input_str.strip().split(',')

        # Ensure we don't process more than 5 lines
        if len(lines) > 5:
            raise ValueError("Input can have a maximum of 5 match results.")

        results = []

        for line in lines:
            match = re.match(r"(.+?)\s+(\d+:\d+)\s+(.+)", line.strip())
            if match:
                team1 = standardize_team_name(match.group(1).strip())
                score1, score2 = map(int, match.group(2).split(':'))
                team2 = standardize_team_name(match.group(3).strip())

                results.append({team1: score1, team2: score2})

        return results
