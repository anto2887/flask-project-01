from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, jsonify, current_app, abort
)
from flask_login import current_user, login_required
from sqlalchemy import func
from datetime import datetime

from app.models import Post, Users, UserResults, UserPredictions, Group, user_groups, db
from app.season import get_current_season

bp = Blueprint('blog', __name__)

# Global variable to store user points
user_points = {}

def update_user_points():
    global user_points
    with current_app.app_context():
        user_points_query = db.session.query(
            UserResults.author_id,
            func.sum(UserResults.points).label('total_points')
        ).group_by(UserResults.author_id).all()
        
        user_points = {up.author_id: up.total_points for up in user_points_query}

def init_app(app):
    with app.app_context():
        update_user_points()

@bp.route('/')
@login_required
def index():
    user_groups_query = Group.query.join(user_groups).filter(user_groups.c.user_id == current_user.id).all()
    seasons = db.session.query(UserPredictions.season.distinct()).all()
    seasons = [season[0] for season in seasons]
    current_group = user_groups_query[0] if user_groups_query else None

    if current_group:
        users = Users.query.join(user_groups).filter(user_groups.c.group_id == current_group.id).all()
    else:
        users = [current_user]

    # Use the global user_points here
    global user_points
    
    recent_prediction = Post.query.filter_by(author_id=current_user.id).order_by(Post.created.desc()).first()
    matchdays = db.session.query(UserPredictions.week.distinct()).order_by(UserPredictions.week).all()
    matchdays = [matchday[0] for matchday in matchdays]
    current_week = max(matchdays) if matchdays else None
    top_performers = get_top_performers(current_week)
    previous_predictions = UserPredictions.query.filter_by(author_id=current_user.id).order_by(UserPredictions.week.desc()).limit(10).all()
    recent_prediction_processed = recent_prediction.processed if recent_prediction else False

    return render_template('blog/index.html', 
                           users=users,
                           user_points=user_points,
                           recent_prediction=recent_prediction,
                           user_groups=user_groups_query,
                           seasons=seasons,
                           matchdays=matchdays,
                           top_performers=top_performers,
                           previous_predictions=previous_predictions,
                           recent_prediction_processed=recent_prediction_processed)

@bp.route('/get_filtered_results')
@login_required
def get_filtered_results():
    group_id = request.args.get('group_id')
    season = request.args.get('season')

    query = db.session.query(
        Users.id,
        Users.username,
        func.coalesce(func.sum(UserResults.points), 0).label('total_points')
    ).join(user_groups, Users.id == user_groups.c.user_id)
    
    if group_id:
        query = query.filter(user_groups.c.group_id == group_id)
    
    if season:
        query = query.filter(UserResults.season == season)
    
    query = query.outerjoin(UserResults, Users.id == UserResults.author_id)
    query = query.group_by(Users.id, Users.username)
    query = query.order_by(func.sum(UserResults.points).desc())

    results = query.all()

    return jsonify([
        {'username': result.username, 'points': int(result.total_points)}
        for result in results
    ])

@bp.route('/get_top_performers')
@login_required
def get_top_performers_route():
    group_id = request.args.get('group_id')
    matchday = request.args.get('matchday')
    
    top_performers = get_top_performers(matchday, group_id)
    
    return jsonify(top_performers)

def get_top_performers(matchday=None, group_id=None):
    query = db.session.query(
        Users.username,
        func.sum(UserPredictions.points).label('total_points')
    ).join(UserPredictions, Users.id == UserPredictions.author_id)
    
    if group_id:
        query = query.join(user_groups, Users.id == user_groups.c.user_id)
        query = query.filter(user_groups.c.group_id == group_id)
    
    if matchday:
        query = query.filter(UserPredictions.week == matchday)
    
    query = query.group_by(Users.username)
    query = query.order_by(func.sum(UserPredictions.points).desc())
    query = query.limit(3)

    results = query.all()

    return [
        {'username': result.username, 'points': int(result.total_points)}
        for result in results
    ]

@bp.route('/get_previous_predictions')
@login_required
def get_previous_predictions():
    group_id = request.args.get('group_id')
    season = request.args.get('season')
    matchday = request.args.get('matchday')

    query = UserPredictions.query.filter_by(author_id=current_user.id)

    if group_id:
        query = query.join(user_groups, UserPredictions.author_id == user_groups.c.user_id)
        query = query.filter(user_groups.c.group_id == group_id)
    
    if season:
        query = query.filter(UserPredictions.season == season)
    
    if matchday:
        query = query.filter(UserPredictions.week == matchday)

    predictions = query.order_by(UserPredictions.week.desc()).all()

    return jsonify([
        {
            'team1': prediction.team1,
            'score1': prediction.score1,
            'team2': prediction.team2,
            'score2': prediction.score2,
            'points': prediction.points
        }
        for prediction in predictions
    ])

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    usergroup = Group.query.join(user_groups).filter(user_groups.c.user_id == current_user.id).all()
    
    if request.method == 'POST':
        body = request.form['body']
        group_id = request.form.get('group_id')
        error = None

        if not body:
            error = 'Prediction is required.'
        if not group_id:
            error = 'Group selection is required.'

        if error is None:
            group = Group.query.get(group_id)
            if group is None:
                error = 'Invalid group selected.'
            else:
                new_post = Post(
                    body=body, 
                    author_id=current_user.id,
                    group_id=group.id,
                    created=datetime.utcnow(),
                    week=get_current_week(),
                    season=get_current_season(group.league)
                )
                db.session.add(new_post)
                db.session.commit()
                flash('Your prediction has been created successfully.')
                return redirect(url_for('blog.index'))

        if error:
            flash(error)

    return render_template('blog/create.html', user_group=usergroup)

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if post.processed:
        flash('This prediction has already been processed and cannot be edited.')
        return redirect(url_for('blog.index'))

    if request.method == 'POST':
        body = request.form['body']
        error = None

        if not body:
            error = 'Prediction is required.'

        if error is not None:
            flash(error)
        else:
            post.body = body
            db.session.commit()
            flash('Your prediction has been updated.')
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = get_post(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('blog.index'))

def get_post(id, check_author=True):
    post = Post.query.get_or_404(id)

    if check_author and post.author_id != current_user.id:
        abort(403)

    return post

def get_current_week():
    # Implement logic to determine the current week
    # This could be based on the current date or retrieved from your database
    # For now, we'll just return a placeholder value
    return 1  # Replace this with actual logic to determine the current week