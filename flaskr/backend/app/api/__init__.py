from flask import Blueprint, jsonify
from flask_cors import CORS
from functools import wraps
from flask_login import current_user
from http import HTTPStatus

api = Blueprint('api', __name__, url_prefix='/api')
CORS(api, supports_credentials=True)

def login_required_api(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), HTTPStatus.UNAUTHORIZED
        return f(*args, **kwargs)
    return decorated_function

@api.errorhandler(400)
def bad_request_error(error):
    return jsonify({
        'status': 'error',
        'message': str(error.description)
    }), HTTPStatus.BAD_REQUEST

@api.errorhandler(401)
def unauthorized_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Authentication required'
    }), HTTPStatus.UNAUTHORIZED

@api.errorhandler(403)
def forbidden_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Insufficient permissions'
    }), HTTPStatus.FORBIDDEN

@api.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Resource not found'
    }), HTTPStatus.NOT_FOUND

@api.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), HTTPStatus.INTERNAL_SERVER_ERROR

# Import and register API routes
from app.api import auth, matches, predictions, groups, users

api.register_blueprint(auth.bp)
api.register_blueprint(matches.bp)
api.register_blueprint(predictions.bp)
api.register_blueprint(groups.bp)
api.register_blueprint(users.bp)