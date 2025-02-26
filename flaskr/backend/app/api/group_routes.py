from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from flask_wtf.csrf import generate_csrf

from app.models import Group, db

group_bp = Blueprint('groups', __name__, url_prefix='/groups')

@group_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    """Render the create group page."""
    if request.method == 'POST':
        data = request.form
        
        if not data or 'name' not in data or 'league' not in data:
            flash('Missing required fields', 'error')
            return render_template('group/create.html', csrf_token=generate_csrf())

        # Create new group
        new_group = Group(
            name=data['name'],
            league=data['league'],
            admin_id=current_user.id
        )
        
        db.session.add(new_group)
        
        # Add creator as first member
        new_group.members.append(current_user)
        
        db.session.commit()

        return redirect(url_for('groups.invite', group_id=new_group.id))
        
    # Pass the CSRF token as a variable to the template
    return render_template('group/create.html', csrf_token=generate_csrf())

@group_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join_group():
    """Handle group joining functionality."""
    if request.method == 'POST':
        invite_code = request.form.get('invite_code')
        if not invite_code:
            return render_template('group/join.html', error='Invite code is required', csrf_token=generate_csrf())
        
        # Find group by invite code
        group = Group.query.filter_by(invite_code=invite_code).first()
        
        if not group:
            return render_template('group/join.html', error='Invalid invite code', csrf_token=generate_csrf())

        # Check if user is already a member
        if current_user in group.members:
            return render_template('group/join.html', error='You are already a member of this group', csrf_token=generate_csrf())

        # Add user to group
        group.members.append(current_user)
        db.session.commit()
        
        return render_template('group/join.html', success='Successfully joined group', csrf_token=generate_csrf())
    
    # For GET requests, just render the join form
    return render_template('group/join.html', csrf_token=generate_csrf())

@group_bp.route('/<int:group_id>/invite', methods=['GET'])
@login_required
def invite(group_id):
    """Display invite code for a newly created group."""
    group = Group.query.get_or_404(group_id)
    
    # Verify user is admin
    if group.admin_id != current_user.id:
        return redirect(url_for('index'))
        
    return render_template('group/invite.html', group=group, csrf_token=generate_csrf())

@group_bp.route('/<int:group_id>/manage', methods=['GET'])
@login_required
def manage(group_id):
    """Group management page."""
    group = Group.query.get_or_404(group_id)
    
    # Verify user is admin
    if group.admin_id != current_user.id:
        return redirect(url_for('index'))
        
    members = []
    for member in group.members:
        members.append({
            'id': member.id,
            'username': member.username,
            'is_admin': member.id == group.admin_id
        })
        
    return render_template(
        'group/admin_dashboard.html', 
        group=group, 
        members=members, 
        member_count=len(members), 
        csrf_token=generate_csrf()
    )