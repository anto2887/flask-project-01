from flask import render_template, jsonify, request
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request_error(error):
        if request_wants_json():
            return jsonify({
                'status': 'error',
                'message': str(error)
            }), 400
        return render_template('errors/400.html', error=error), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        if request_wants_json():
            return jsonify({
                'status': 'error',
                'message': 'You do not have permission to perform this action'
            }), 403
        return render_template('errors/403.html', error=error), 403

    @app.errorhandler(404)
    def not_found_error(error):
        if request_wants_json():
            return jsonify({
                'status': 'error',
                'message': 'Resource not found'
            }), 404
        return render_template('errors/404.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        if request_wants_json():
            return jsonify({
                'status': 'error',
                'message': 'An internal server error occurred'
            }), 500
        return render_template('errors/500.html', error=error), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.error('An unexpected error occurred: %s', str(error))
        if request_wants_json():
            return jsonify({
                'status': 'error',
                'message': 'An unexpected error occurred'
            }), 500
        return render_template('errors/500.html', error=error), 500

def request_wants_json():
    """Check if the request prefers JSON response."""
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']