from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from http import HTTPStatus

from app.models import Users, db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({
            'status': 'error',
            'message': 'Already logged in'
        }), HTTPStatus.BAD_REQUEST

    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Missing username or password'
        }), HTTPStatus.BAD_REQUEST

    try:
        user = Users.query.filter_by(username=data['username']).first()
        if user and check_password_hash(user.password, data['password']):
            login_user(user)
            return jsonify({
                'status': 'success',
                'data': {
                    'id': user.id,
                    'username': user.username
                }
            })
        
        return jsonify({
            'status': 'error',
            'message': 'Invalid username or password'
        }), HTTPStatus.UNAUTHORIZED

    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error during login'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return jsonify({
            'status': 'error',
            'message': 'Already logged in'
        }), HTTPStatus.BAD_REQUEST

    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Missing username or password'
        }), HTTPStatus.BAD_REQUEST

    try:
        if Users.query.filter_by(username=data['username']).first():
            return jsonify({
                'status': 'error',
                'message': 'Username already exists'
            }), HTTPStatus.CONFLICT

        user = Users(
            username=data['username'],
            password=generate_password_hash(data['password'])
        )
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Registration successful'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Error during registration'
        }), HTTPStatus.INTERNAL_SERVER_ERROR

@bp.route('/logout', methods=['POST'])
def logout():
    if current_user.is_authenticated:
        logout_user()
        return jsonify({
            'status': 'success',
            'message': 'Logged out successfully'
        })
    
    return jsonify({
        'status': 'error',
        'message': 'Not logged in'
    }), HTTPStatus.BAD_REQUEST

@bp.route('/status', methods=['GET'])
def auth_status():
    if current_user.is_authenticated:
        return jsonify({
            'status': 'success',
            'data': {
                'authenticated': True,
                'user': {
                    'id': current_user.id,
                    'username': current_user.username
                }
            }
        })
    
    return jsonify({
        'status': 'success',
        'data': {
            'authenticated': False
        }
    })