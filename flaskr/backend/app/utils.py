from sqlalchemy import func
from app.models import UserResults, db

def user_points():
    """Fetch user points."""
    points_query = db.session.query(
        UserResults.author_id,
        func.sum(UserResults.points).label('total_points')
    ).group_by(UserResults.author_id).all()
    
    return {up.author_id: up.total_points for up in points_query}
