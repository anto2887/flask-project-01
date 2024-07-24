from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Users, Group, db
from app.forms import CreateGroupForm

group_bp = Blueprint('group', __name__, url_prefix='/group')

@group_bp.route('/manage', methods=['GET', 'POST'])
@login_required
def manage_groups():
    created_groups = Group.query.filter_by(creator_id=current_user.id).all()
    
    if request.method == 'POST':
        group_id = request.form.get('group_id')
        group = Group.query.get_or_404(group_id)
        
        if group.creator_id != current_user.id:
            flash('You are not authorized to manage this group.', 'danger')
            return redirect(url_for('group.manage_groups'))
        
        form = CreateGroupForm(obj=group)
        if form.validate():
            group.name = form.name.data
            group.league = form.league.data
            selected_users = Users.query.filter(Users.id.in_(request.form.getlist('selected_users'))).all()
            group.users = selected_users
            if current_user not in group.users:
                group.users.append(current_user)
            db.session.commit()
            flash('Group updated successfully!', 'success')
            return redirect(url_for('group.manage_groups'))
    
    return render_template('manage_groups.html', groups=created_groups)

@group_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
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

    return render_template('create_group.html', form=form, users=users)