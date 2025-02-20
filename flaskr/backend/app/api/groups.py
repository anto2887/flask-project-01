from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from http import HTTPStatus

from app.api import login_required_api
from app.models import Group, GroupPrivacyType, MemberRole, db
from app.services.group_service import GroupService
from app.services.permission_service import PermissionService
from app.services.analytics_service import AnalyticsService
from app.services.team_service import TeamService

bp = Blueprint('groups', __name__, url_prefix='/groups')

@bp.route('', methods=['POST'])
@login_required_api
def create_group():
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'league' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), HTTPStatus.BAD_REQUEST

        privacy_type = GroupPrivacyType[data.get('privacy_type', 'PRIVATE')]
        group, error = GroupService.create_group(
            name=data['name'],
            league=data['league'],
            creator_id=current_user.id,
            privacy_type=privacy_type,
            description=data.get('description'),
            tracked_team_ids=data.get('tracked_teams', [])
        )

        if error:
            return jsonify({
                'status': 'error',
                'message': error
            }), HTTPStatus.BAD_REQUEST

        return jsonify({
            'status': 'success',
            'data': {
                'group_id': group.id,
                'name': group.name,
                'league': group.league,
                'invite_code': group.invite_code,
                'tracked_teams': GroupService.get_tracked_teams(group.id)
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error creating group: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error creating group'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/teams/<league>', methods=['GET'])
@login_required_api
def get_teams_by_league(league):
    """Get available teams for a league."""
    try:
        team_service = current_app.config.get('TEAM_SERVICE')
        if not team_service:
            return jsonify({
                'status': 'error',
                'message': 'Team service not initialized'
            }), HTTPStatus.INTERNAL_SERVER_ERROR

        # Validate league
        valid_leagues = {
            "PL": "Premier League",
            "LL": "La Liga",
            "UCL": "UEFA Champions League"
        }
        
        if league not in valid_leagues:
            return jsonify({
                'status': 'error',
                'message': 'Invalid league selected'
            }), HTTPStatus.BAD_REQUEST

        teams = team_service.get_league_teams(valid_leagues[league])
        return jsonify({
            'status': 'success',
            'data': teams
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching teams: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching teams'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('', methods=['GET'])
@login_required_api
def get_groups():
    try:
        groups = Group.query.join(
            Group.member_roles
        ).filter(
            Group.member_roles.any(user_id=current_user.id)
        ).all()

        return jsonify({
            'status': 'success',
            'data': [{
                'id': group.id,
                'name': group.name,
                'league': group.league,
                'description': group.description,
                'privacy_type': group.privacy_type.value,
                'member_count': len(group.users),
                'created_at': group.created.isoformat(),
                'role': next(
                    (mr.role.value for mr in group.member_roles if mr.user_id == current_user.id),
                    None
                )
            } for group in groups]
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching groups: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching groups'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:group_id>', methods=['GET'])
@login_required_api
def get_group(group_id):
    try:
        group = Group.query.get(group_id)
        if not group:
            return jsonify({
                'status': 'error',
                'message': 'Group not found'
            }), HTTPStatus.NOT_FOUND

        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.MEMBER):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

        analytics_service = AnalyticsService()
        analytics = analytics_service.generate_group_analytics(group_id)

        return jsonify({
            'status': 'success',
            'data': {
                'id': group.id,
                'name': group.name,
                'league': group.league,
                'description': group.description,
                'privacy_type': group.privacy_type.value,
                'invite_code': group.invite_code,
                'member_count': len(group.users),
                'created_at': group.created.isoformat(),
                'role': next(
                    (mr.role.value for mr in group.member_roles if mr.user_id == current_user.id),
                    None
                ),
                'analytics': analytics,
                'tracked_teams': GroupService.get_tracked_teams(group_id)
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching group: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching group details'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:group_id>', methods=['PUT'])
@login_required_api
def update_group(group_id):
    try:
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.ADMIN):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

        data = request.get_json()
        group = Group.query.get(group_id)
        if not group:
            return jsonify({
                'status': 'error',
                'message': 'Group not found'
            }), HTTPStatus.NOT_FOUND

        if 'name' in data:
            group.name = data['name']
        if 'description' in data:
            group.description = data['description']
        if 'privacy_type' in data:
            group.privacy_type = GroupPrivacyType[data['privacy_type']]
        if 'tracked_teams' in data:
            success, error = GroupService.update_tracked_teams(group_id, data['tracked_teams'])
            if not success:
                return jsonify({
                    'status': 'error',
                    'message': error
                }), HTTPStatus.BAD_REQUEST

        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Group updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating group: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error updating group'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/join', methods=['POST'])
@login_required_api
def join_group():
    try:
        data = request.get_json()
        if not data or 'invite_code' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Invite code is required'
            }), HTTPStatus.BAD_REQUEST

        success, message = GroupService.join_group(data['invite_code'], current_user.id)

        if not success:
            return jsonify({
                'status': 'error',
                'message': message
            }), HTTPStatus.BAD_REQUEST

        return jsonify({
            'status': 'success',
            'message': message
        })

    except Exception as e:
        current_app.logger.error(f"Error joining group: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error joining group'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:group_id>/members', methods=['GET'])
@login_required_api
def get_group_members(group_id):
    try:
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.MEMBER):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

        members = GroupService.get_group_members(group_id)
        return jsonify({
            'status': 'success',
            'data': members
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching group members: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching group members'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:group_id>/members', methods=['POST'])
@login_required_api
def manage_members(group_id):
    try:
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.ADMIN):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

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
            'data': results
        })

    except Exception as e:
        current_app.logger.error(f"Error managing members: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error managing members'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:group_id>/members/<int:user_id>', methods=['DELETE'])
@login_required_api
def remove_member(group_id, user_id):
    try:
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.ADMIN):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

        success, message = GroupService.remove_member(group_id, user_id)

        if not success:
            return jsonify({
                'status': 'error',
                'message': message
            }), HTTPStatus.BAD_REQUEST

        return jsonify({
            'status': 'success',
            'message': 'Member removed successfully'
        })

    except Exception as e:
        current_app.logger.error(f"Error removing member: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error removing member'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:group_id>/regenerate-code', methods=['POST'])
@login_required_api
def regenerate_invite_code(group_id):
    try:
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.ADMIN):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

        new_code = GroupService.regenerate_invite_code(group_id)
        if not new_code:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate new invite code'
            }), HTTPStatus.INTERNAL_SERVER_ERROR

        return jsonify({
            'status': 'success',
            'data': {
                'invite_code': new_code
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error regenerating invite code: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error regenerating invite code'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:group_id>/members/<int:user_id>/role', methods=['PUT'])
@login_required_api
def update_member_role(group_id: int, user_id: int):
    """Update a member's role in the group"""
    try:
        # Check if user is admin
        if not GroupService.is_group_admin(current_user.id, group_id):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized - Admin access required'
            }), HTTPStatus.FORBIDDEN

        data = request.get_json()
        if not data or 'role' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Role is required'
            }), HTTPStatus.BAD_REQUEST

        try:
            new_role = MemberRole[data['role']]
        except KeyError:
            return jsonify({
                'status': 'error',
                'message': 'Invalid role'
            }), HTTPStatus.BAD_REQUEST

        success, message = GroupService.update_member_role(group_id, user_id, new_role)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message
            })
        
        return jsonify({
            'status': 'error',
            'message': message
        }), HTTPStatus.BAD_REQUEST

    except Exception as e:
        current_app.logger.error(f"Error updating member role: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update member role'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:group_id>/audit-log', methods=['GET'])
@login_required_api
def get_audit_log(group_id: int):
    """Get group audit log"""
    try:
        # Check if user has permission to view audit log
        if not GroupService.is_group_admin(current_user.id, group_id):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized - Admin access required'
            }), HTTPStatus.FORBIDDEN

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        audit_logs = GroupService.get_audit_logs(group_id, page, per_page)
        return jsonify({
            'status': 'success',
            'data': audit_logs
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching audit log: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch audit log'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/<int:group_id>/members/activity', methods=['GET'])
@login_required_api
def get_member_activity(group_id: int):
    """Get member activity statistics"""
    try:
        # Check if user has access to group
        if not PermissionService.check_group_permission(current_user.id, group_id, MemberRole.MEMBER):
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

        activity = GroupService.get_member_activity(group_id)
        return jsonify({
            'status': 'success',
            'data': activity
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching member activity: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to fetch member activity'
        }), HTTPStatus.INTERNAL_SERVER_ERROR