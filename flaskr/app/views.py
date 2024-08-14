from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import current_user, login_required
from app.models import Users, Group, db
from app.forms import CreateGroupForm

group_bp = Blueprint('group', __name__, url_prefix='/group')

@group_bp.route('/manage', methods=['GET', 'POST'])
@login_required
def manage_groups():
    try:
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to manage groups.', 'warning')
            return redirect(url_for('auth.login'))

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
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Please log in to create a group.', 'warning')
            return redirect(url_for('auth.login'))

        form = CreateGroupForm()
        users = Users.query.all()

        if form.validate_on_submit():
            new_group = Group(name=form.name.data, league=form.league.data, creator_id=current_user.id)
            selected_users = Users.query.filter(Users.id.in_(request.form.getlist('selected_users'))).all()
            new_group.users = selected_users + [current_user]
            db.session.add(new_group)
            db.session.commit()
            flash('Group created successfully!', 'success')
            return redirect(url_for('group.manage_groups'))

        return render_template('blog/create_group.html', form=form, users=users)
    except Exception as e:
        current_app.logger.error(f"Error in create_group: {str(e)}")
        return f"An error occurred: {str(e)}", 500