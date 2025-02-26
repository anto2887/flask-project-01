from flask import Blueprint, jsonify, request, current_app
from flask_login import current_user
from http import HTTPStatus

from app.api import login_required_api
from app.models import Group, Users, db

group_api_bp = Blueprint('groups_api', __name__, url_prefix='/groups')

@group_api_bp.route('/create', methods=['POST'])
@login_required_api
def create_group():
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'league' not in data or 'teams' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields'
            }), HTTPStatus.BAD_REQUEST

        # Create new group
        new_group = Group(
            name=data['name'],
            league=data['league'],
            admin_id=current_user.id,
            teams=data['teams']
        )
        
        db.session.add(new_group)
        
        # Add creator as first member
        new_group.members.append(current_user)
        
        db.session.commit()

        return jsonify({
            'status': 'success',
            'data': {
                'id': new_group.id,
                'name': new_group.name,
                'league': new_group.league,
                'invite_code': new_group.invite_code
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating group: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error creating group'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@group_api_bp.route('/join', methods=['POST'])
@login_required_api
def join_group():
    try:
        data = request.get_json()
        
        if not data or 'invite_code' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing invite code'
            }), HTTPStatus.BAD_REQUEST

        # Find group by invite code
        group = Group.query.filter_by(invite_code=data['invite_code']).first()
        
        if not group:
            return jsonify({
                'status': 'error',
                'message': 'Invalid invite code'
            }), HTTPStatus.NOT_FOUND

        # Check if user is already a member
        if current_user in group.members:
            return jsonify({
                'status': 'error',
                'message': 'Already a member of this group'
            }), HTTPStatus.CONFLICT

        # Add user to group
        group.members.append(current_user)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'data': {
                'id': group.id,
                'name': group.name,
                'league': group.league
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error joining group: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error joining group'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@group_api_bp.route('/manage/<int:group_id>', methods=['GET'])
@login_required_api
def get_group_management(group_id):
    try:
        group = Group.query.get_or_404(group_id)
        
        # Verify user is admin
        if group.admin_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

        return jsonify({
            'status': 'success',
            'data': {
                'id': group.id,
                'name': group.name,
                'league': group.league,
                'invite_code': group.invite_code,
                'members': [{
                    'id': member.id,
                    'username': member.username,
                    'is_admin': member.id == group.admin_id
                } for member in group.members]
            }
        })

    except Exception as e:
        current_app.logger.error(f"Error fetching group management: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching group management'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@group_api_bp.route('/manage/<int:group_id>/members/<int:user_id>', methods=['DELETE'])
@login_required_api
def remove_member(group_id, user_id):
    try:
        group = Group.query.get_or_404(group_id)
        
        # Verify user is admin
        if group.admin_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized access'
            }), HTTPStatus.FORBIDDEN

        # Cannot remove admin
        if user_id == group.admin_id:
            return jsonify({
                'status': 'error',
                'message': 'Cannot remove group admin'
            }), HTTPStatus.BAD_REQUEST

        user = Users.query.get_or_404(user_id)
        
        if user not in group.members:
            return jsonify({
                'status': 'error',
                'message': 'User not in group'
            }), HTTPStatus.NOT_FOUND

        group.members.remove(user)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Member removed successfully'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing member: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error removing member'
        }), HTTPStatus.INTERNAL_SERVER_ERROR 