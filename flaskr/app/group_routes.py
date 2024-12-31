from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
from flask_login import login_required, current_user
from flask_wtf.csrf import generate_csrf
from app.services.group_service import GroupService
from app.services.permission_service import PermissionService
from app.services.analytics_service import AnalyticsService
from app.models import Group, GroupMember, MemberRole, GroupPrivacyType

group_bp = Blueprint('group', __name__, url_prefix='/group')

@group_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if request.method == 'POST':
        try:
            current_app.logger.debug('Headers received: %s', dict(request.headers))
            current_app.logger.debug('Form data received: %s', request.form)
            current_app.logger.debug('Files received: %s', request.files)
            
            # Get form data
            name = request.form['name']
            league = request.form['league']
            privacy_type_str = request.form['privacy_type']
            description = request.form.get('description')
            tracked_teams = request.form.getlist('tracked_teams')
            
            current_app.logger.debug('Parsed form data: name=%s, league=%s, privacy=%s, teams=%s', 
                                   name, league, privacy_type_str, tracked_teams)

            # Validate required fields
            if not name or not league:
                current_app.logger.warning('Missing required fields: name=%s, league=%s', name, league)
                return jsonify({
                    'status': 'error',
                    'message': 'Name and league are required'
                }), 400

            # Convert privacy_type string to enum
            try:
                privacy_type = GroupPrivacyType[privacy_type_str]
                current_app.logger.debug('Privacy type converted: %s -> %s', privacy_type_str, privacy_type)
            except KeyError:
                current_app.logger.error(f"Invalid privacy_type value: {privacy_type_str}")
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid privacy type selected'
                }), 400

            # Create group
            current_app.logger.debug('Attempting to create group with data: %s', {
                'name': name,
                'league': league,
                'creator_id': current_user.id,
                'privacy_type': privacy_type,
                'description': description,
                'tracked_teams': tracked_teams
            })

            group, error = GroupService.create_group(
                name=name,
                league=league,
                creator_id=current_user.id,
                privacy_type=privacy_type,
                description=description,
                tracked_team_ids=tracked_teams
            )

            if error:
                current_app.logger.error(f"Error creating group: {error}")
                return jsonify({'status': 'error', 'message': error}), 400

            current_app.logger.info(f"Group '{name}' created successfully by user {current_user.id}")
            redirect_url = url_for('group.manage', group_id=group.id)
            current_app.logger.debug('Redirecting to: %s', redirect_url)
            
            return jsonify({
                'status': 'success',
                'redirect_url': redirect_url
            })

        except Exception as e:
            current_app.logger.error(f"Error creating group: {str(e)}", exc_info=True)
            return jsonify({
                'status': 'error',
                'message': 'An unexpected error occurred while creating the group'
            }), 500

    # For GET requests, pass CSRF token
    return render_template('group/create.html', csrf_token=generate_csrf())

@group_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join_group():
    if request.method == 'POST':
        try:
            data = request.get_json()
            invite_code = data.get('invite_code')

            if not invite_code:
                return jsonify({
                    'status': 'error',
                    'message': 'Invite code is required'
                }), 400

            success, message = GroupService.join_group(invite_code, current_user.id)

            if success:
                current_app.logger.info(f"User {current_user.id} successfully joined group with code {invite_code}")
                return jsonify({'status': 'success', 'message': message})
            
            current_app.logger.warning(f"Failed join attempt for code {invite_code} by user {current_user.id}: {message}")
            return jsonify({'status': 'error', 'message': message}), 400

        except Exception as e:
            current_app.logger.error(f"Error joining group: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'An unexpected error occurred while joining the group'
            }), 500

    return render_template('group/join.html', csrf_token=generate_csrf())

@group_bp.route('/<int:group_id>/manage')
@login_required
def manage_group(group_id):
    try:
        # Check admin permissions
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.ADMIN):
            current_app.logger.warning(f"Unauthorized access attempt to manage group {group_id} by user {current_user.id}")
            return redirect(url_for('index'))

        group = Group.query.get_or_404(group_id)
        analytics_service = AnalyticsService()
        
        return render_template('group/admin_dashboard.html',
            group=group,
            members=GroupService.get_group_members(group_id),
            pending_requests=GroupService.get_pending_requests(group_id),
            analytics=analytics_service.generate_group_analytics(group_id),
            member_count=len(group.users),
            csrf_token=generate_csrf()
        )

    except Exception as e:
        current_app.logger.error(f"Error accessing group management: {str(e)}")
        return redirect(url_for('index'))

@group_bp.route('/api/teams/<league>')
@login_required
def get_league_teams(league):
    try:
        team_service = current_app.config.get('TEAM_SERVICE')
        if not team_service:
            current_app.logger.error("Team service not initialized")
            return jsonify({'status': 'error', 'message': 'Service unavailable'}), 500

        teams = team_service.get_league_teams(league)
        current_app.logger.debug(f"Teams data structure for {league}: {teams}")
        current_app.logger.debug(f"Number of teams retrieved: {len(teams) if teams else 0}")
        if teams and len(teams) > 0:
            current_app.logger.debug(f"Sample team structure: {teams[0]}")
        
        if not teams:
            current_app.logger.warning(f"No teams found for league: {league}")
            return jsonify({'status': 'error', 'message': 'No teams found for the given league'}), 404

        response_data = {'status': 'success', 'teams': teams}
        return jsonify(response_data)

    except Exception as e:
        current_app.logger.error(f"Error fetching teams: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch teams'
        }), 500

@group_bp.route('/<int:group_id>/members', methods=['POST'])
@login_required
def manage_members(group_id):
    try:
        # Check admin permissions
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.ADMIN):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        data = request.get_json()
        action = data.get('action')
        user_ids = data.get('user_ids', [])

        if not action or not user_ids:
            return jsonify({
                'status': 'error',
                'message': 'Action and user IDs are required'
            }), 400

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
        return jsonify({
            'status': 'error',
            'message': 'Operation failed'
        }), 500

@group_bp.route('/<int:group_id>/regenerate-code', methods=['POST'])
@login_required
def regenerate_code(group_id):
    try:
        # Check admin permissions
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.ADMIN):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        new_code = GroupService.regenerate_invite_code(group_id)
        if not new_code:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate new invite code'
            }), 500

        current_app.logger.info(f"Invite code regenerated for group {group_id} by user {current_user.id}")
        return jsonify({'status': 'success', 'invite_code': new_code})

    except Exception as e:
        current_app.logger.error(f"Error regenerating invite code: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to regenerate code'
        }), 500