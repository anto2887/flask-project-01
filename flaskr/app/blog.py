from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify
)
from werkzeug.exceptions import abort
from sqlalchemy import func

from app.auth import login_required
from app.models import Post, Users, UserResults, UserPredictions, Group, UserGroup, db
from app.season import get_current_season

bp = Blueprint('blog', __name__)

@bp.route('/')
@login_required
def index():
    # Get user's groups
    user_groups = Group.query.join(UserGroup).filter(UserGroup.user_id == g.user.id).all()

    # Get available seasons
    seasons = db.session.query(UserPredictions.season.distinct()).all()
    seasons = [season[0] for season in seasons]

    # Get the current group (you might want to add logic to determine the current group)
    current_group = user_groups[0] if user_groups else None

    # Get all users in the current group
    if current_group:
        users = Users.query.join(UserGroup).filter(UserGroup.group_id == current_group.id).all()
    else:
        users = [g.user]  # If no group, just show the current user

    # Get user points
    user_points = db.session.query(
        UserResults.author_id,
        func.sum(UserResults.points).label('total_points')
    ).group_by(UserResults.author_id).all()
    
    user_points = {up.author_id: up.total_points for up in user_points}

    # Get the most recent prediction
    recent_prediction = Post.query.filter_by(author_id=g.user.id).order_by(Post.created.desc()).first()

    return render_template('blog/index.html', 
                           users=users,
                           user_points=user_points,
                           recent_prediction=recent_prediction,
                           user_groups=user_groups,
                           seasons=seasons)

@bp.route('/get_filtered_results')
@login_required
def get_filtered_results():
    group_id = request.args.get('group_id')
    season = request.args.get('season')

    # Query to get filtered results
    query = db.session.query(
        Users.id,
        Users.username,
        func.coalesce(func.sum(UserResults.points), 0).label('total_points')
    ).join(UserGroup, Users.id == UserGroup.user_id)
    
    if group_id:
        query = query.filter(UserGroup.group_id == group_id)
    
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

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            new_post = Post(title=title, body=body, author_id=g.user.id)
            db.session.add(new_post)
            db.session.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = Post.query.join(Users).filter(Post.id == id).first()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post.author_id != g.user.id:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            post.title = title
            post.body = body
            db.session.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    post = get_post(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('blog.index'))