import re
from flask import current_app
from fuzzywuzzy import process

# Define team_name_mapping
team_name_mapping = {
    "Premier League": {
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
    },
    "La Liga": {
        # Add La Liga teams here
    },
    "UEFA Champions League": {
        # Add Champions League teams here
    }
}

def standardize_team_name(name, league):
    if league not in team_name_mapping:
        return name
    
    # First try exact match
    for standard, variations in team_name_mapping[league].items():
        if name in variations:
            return standard
    
    # If no exact match, try fuzzy matching
    all_variations = [(standard, var) 
                     for standard, vars in team_name_mapping[league].items() 
                     for var in vars]
    
    match = process.extractOne(name, [var for _, var in all_variations], score_cutoff=85)
    if match:
        matched_variation = match[0]
        return next(standard for standard, var in all_variations if var == matched_variation)
    
    return name

def score_input(input_str, league):
    lines = re.split(r'[\n,]', input_str.strip())
    if len(lines) > 5:
        raise ValueError("Input can have a maximum of 5 match results.")
    results = []
    for line in lines:
        match = re.match(r"(.+?)\s+(\d+:\d+)\s+(.+)", line.strip())
        if match:
            team1 = standardize_team_name(match.group(1).strip(), league)
            score1, score2 = map(int, match.group(2).split(':'))
            team2 = standardize_team_name(match.group(3).strip(), league)
            results.append({team1: score1, team2: score2})
    return results

def get_latest_prediction(user_id, league, week, season):
    with current_app.app_context():
        from app.models import Post, Group
        
        group = Group.query.filter_by(league=league).first()
        if not group:
            return None
        
        latest_post = Post.query.filter_by(
            author_id=user_id,
            group_id=group.id,
            week=week,
            season=season
        ).order_by(Post.created.desc()).first()
        
        if not latest_post:
            return None
        
        return score_input(latest_post.body, league)