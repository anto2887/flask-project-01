from flask import render_template, jsonify, request, current_app
from werkzeug.exceptions import HTTPException
from http import HTTPStatus


def register_api_error_handlers(app):
    @app.errorhandler(400)
    def bad_request_error(error):
        app.logger.error(f"400 Error: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': str(error)
        }), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        app.logger.error(f"401 Unauthorized Error: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': 'Authentication required'
        }), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.error(f"403 Forbidden Error: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': 'Access denied'
        }), 403

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error(f"404 Not Found Error: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': 'Resource not found'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 Internal Server Error: {str(error)}")
        return jsonify({
            'status': 'error',
            'message': 'An internal server error occurred'
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.error(f"An unexpected error occurred: {str(error)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request_error(error):
        current_app.logger.error(f"400 Error: {str(error)}")
        if request_wants_json():
            return jsonify({
                'status': 'error',
                'message': str(error)
            }), 400
        return render_template('errors/400.html', error=error), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        current_app.logger.error(f"403 Forbidden Error: {str(error)}")
        if request_wants_json():
            return jsonify({
                'status': 'error',
                'message': 'Forbidden'
            }), HTTPStatus.FORBIDDEN
        return render_template('errors/403.html', error=error), 403

    @app.errorhandler(404)
    def not_found_error(error):
        current_app.logger.error(f"404 Not Found Error: {str(error)}")
        if request_wants_json():
            return jsonify({
                'status': 'error',
                'message': 'Resource not found'
            }), HTTPStatus.NOT_FOUND
        return render_template('errors/404.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        current_app.logger.error(f"500 Internal Server Error: {str(error)}")
        if request_wants_json():
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), HTTPStatus.INTERNAL_SERVER_ERROR
        return render_template('errors/500.html', error=error), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        current_app.logger.error(f"An unexpected error occurred: {str(error)}", exc_info=True)
        if request_wants_json():
            return jsonify({
                'status': 'error',
                'message': 'An unexpected error occurred'
            }), 500
        return render_template('errors/500.html', error=error), 500


def request_wants_json():
    """Check if the request prefers JSON response."""
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and request.accept_mimetypes[best] > request.accept_mimetypes['text/html']
