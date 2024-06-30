# views.py
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app.models import Users, Group, UserGroup, db
from app.forms import CreateGroupForm

group_bp = Blueprint('group', __name__, url_prefix='/group')

@group_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    form = CreateGroupForm()
    form.users.choices = [(user.id, user.username) for user in Users.query.all()]

    if form.validate_on_submit():
        group = Group(name=form.name.data, league=form.league.data, creator_id=current_user.id)
        db.session.add(group)
        db.session.commit()

        for user_id in form.users.data:
            user_group = UserGroup(user_id=user_id, group_id=group.id)
            db.session.add(user_group)

        db.session.commit()
        flash('Group created successfully!', 'success')
        return redirect(url_for('main.index'))

    return render_template('create_group.html', form=form)

@group_bp.route('/<int:group_id>/manage', methods=['GET', 'POST'])
@login_required
def manage_group(group_id):
    group = Group.query.get_or_404(group_id)

    if group.creator_id != current_user.id:
        flash('You are not authorized to manage this group.', 'danger')
        return redirect(url_for('main.index'))

    form = CreateGroupForm(obj=group)
    form.users.choices = [(user.id, user.username) for user in Users.query.all()]

    if form.validate_on_submit():
        group.name = form.name.data
        group.league = form.league.data
        db.session.commit()

        UserGroup.query.filter_by(group_id=group_id).delete()

        for user_id in form.users.data:
            user_group = UserGroup(user_id=user_id, group_id=group.id)
            db.session.add(user_group)

        db.session.commit()
        flash('Group updated successfully!', 'success')
        return redirect(url_for('main.index'))

    return render_template('manage_group.html', form=form, group=group)
