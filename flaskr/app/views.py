from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from app.models import Users, Group, db
from app.forms import CreateGroupForm
from app.blog import user_points

group_bp = Blueprint('group', __name__, url_prefix='/group')

@group_bp.route('/manage', methods=['GET', 'POST'])
@login_required
def manage_groups():
    try:
        created_groups = Group.query.filter_by(creator_id=current_user.id).all()
        
        if request.method == 'POST':
            group_id = request.form.get('group_id')
            group = Group.query.get_or_404(group_id)
            
            if group.creator_id != current_user.id:
                flash('You are not authorized to manage this group.', 'danger')
                return redirect(url_for('group.manage_groups'))
            
            form = CreateGroupForm(obj=group)
            if form.validate_on_submit():
                group.name = form.name.data
                group.league = form.league.data
                selected_users = Users.query.filter(Users.id.in_(request.form.getlist('selected_users'))).all()
                group.users = selected_users
                if current_user not in group.users:
                    group.users.append(current_user)
                db.session.commit()
                flash('Group updated successfully!', 'success')
                return redirect(url_for('group.manage_groups'))
        
        return render_template('blog/manage_group.html', groups=created_groups)
    except Exception as e:
        current_app.logger.error(f"Error in manage_groups: {str(e)}")
        return f"An error occurred: {str(e)}", 500

@group_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    try:
        form = CreateGroupForm()
        users = Users.query.all()

        if form.validate_on_submit():
            group_name = form.name.data
            league = form.league.data
            
            # Check if the group already exists
            existing_group = Group.query.filter_by(name=group_name, league=league).first()
            if existing_group:
                flash(f'A group named "{group_name}" in {league} already exists.', 'warning')
                return render_template('blog/create_group.html', form=form, users=users, user_points=user_points)

            new_group = Group(name=group_name, league=league, creator_id=current_user.id)
            db.session.add(new_group)
            db.session.flush()  # This will assign an ID to new_group without committing

            selected_user_ids = request.form.getlist('selected_users')
            selected_users = Users.query.filter(Users.id.in_(selected_user_ids)).all()

            # Add the current user to the group if not already selected
            if str(current_user.id) not in selected_user_ids:
                selected_users.append(current_user)

            # Add users to the group, checking for existing memberships
            for user in selected_users:
                if not user.groups.filter_by(id=new_group.id).first():
                    new_group.users.append(user)

            db.session.commit()
            flash('Group created successfully!', 'success')
            return redirect(url_for('group.manage_groups'))

        return render_template('blog/create_group.html', form=form, users=users, user_points=user_points)
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"IntegrityError in create_group: {str(e)}")
        flash('An error occurred while creating the group. The group name might already be taken.', 'danger')
        return render_template('blog/create_group.html', form=form, users=users, user_points=user_points)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in create_group: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'danger')
        return render_template('blog/create_group.html', form=form, users=users, user_points=user_points), 500