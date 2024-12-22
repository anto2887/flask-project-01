from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.services.group_service import GroupService
from app.services.permission_service import PermissionService
from app.services.analytics_service import AnalyticsService
from app.models import Group, GroupMember, MemberRole

group_bp = Blueprint('group', __name__, url_prefix='/group')

@group_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        try:
            name = request.form['name']
            league = request.form['league']
            privacy_type = request.form['privacy_type']
            description = request.form.get('description')
            tracked_teams = request.form.getlist('tracked_teams')

            group, error = GroupService.create_group(
                name=name,
                league=league,
                creator_id=current_user.id,
                privacy_type=privacy_type,
                description=description,
                tracked_team_ids=tracked_teams
            )

            if error:
                return jsonify({'status': 'error', 'message': error}), 400

            return jsonify({
                'status': 'success',
                'redirect_url': url_for('group.manage', group_id=group.id)
            })

        except Exception as e:
            current_app.logger.error(f"Error creating group: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Failed to create group'}), 500

    return render_template('group/create.html')

@group_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join_group():
    if request.method == 'POST':
        try:
            data = request.get_json()
            invite_code = data.get('invite_code')

            success, message = GroupService.join_group(invite_code, current_user.id)

            if success:
                return jsonify({'status': 'success', 'message': message})
            return jsonify({'status': 'error', 'message': message}), 400

        except Exception as e:
            current_app.logger.error(f"Error joining group: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Failed to join group'}), 500

    return render_template('group/join.html')

@group_bp.route('/<int:group_id>/manage')
@login_required
def manage_group(group_id):
    try:
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.ADMIN):
            return redirect(url_for('index'))

        group = Group.query.get_or_404(group_id)
        analytics_service = AnalyticsService()
        
        return render_template('group/admin_dashboard.html',
            group=group,
            members=GroupService.get_group_members(group_id),
            pending_requests=GroupService.get_pending_requests(group_id),
            analytics=analytics_service.generate_group_analytics(group_id),
            member_count=len(group.users)
        )

    except Exception as e:
        current_app.logger.error(f"Error accessing group management: {str(e)}")
        return redirect(url_for('index'))

@group_bp.route('/api/teams/<league>')
@login_required
def get_league_teams(league):
    try:
        teams = GroupService.get_league_teams(league)
        return jsonify({'status': 'success', 'teams': teams})
    except Exception as e:
        current_app.logger.error(f"Error fetching teams: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch teams'}), 500

# Admin actions
@group_bp.route('/<int:group_id>/members', methods=['POST'])
@login_required
def manage_members(group_id):
    try:
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.ADMIN):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        data = request.get_json()
        action = data.get('action')
        user_ids = data.get('user_ids', [])

        success, message, results = GroupService.bulk_member_action(
            group_id=group_id,
            admin_id=current_user.id,
            user_ids=user_ids,
            action=action
        )

        return jsonify({
            'status': 'success' if success else 'error',
            'message': message,
            'results': results
        })

    except Exception as e:
        current_app.logger.error(f"Error managing members: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Operation failed'}), 500

@group_bp.route('/<int:group_id>/regenerate-code', methods=['POST'])
@login_required
def regenerate_code(group_id):
    try:
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.ADMIN):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        new_code = GroupService.regenerate_invite_code(group_id)
        return jsonify({'status': 'success', 'invite_code': new_code})

    except Exception as e:
        current_app.logger.error(f"Error regenerating invite code: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to regenerate code'}), 500