import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, current_app, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from sqlalchemy import create_engine
from flask.cli import with_appcontext

from app.db import db
from app.models import Users, Post, UserResults, Fixture

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

def configure_logging(app):
    if not app.debug:
        log_dir = '/flaskr/logs'
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        
        # Configure file handler
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'flaskr.log'),
            maxBytes=10_240_000,
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

        # Add CloudWatch handler if in AWS environment
        if os.environ.get('AWS_EXECUTION_ENV'):
            app.logger.info('Configuring CloudWatch logging')

def init_services(app):
    """Initialize API services within application context"""
    with app.app_context():
        try:
            from app.api_client import initialize_services
            from app.services.team_service import TeamService
            from app.models import MatchStatus, GroupPrivacyType, MemberRole, PredictionStatus
            
            # Register enum convertors for SQLAlchemy
            db.event.listen(db.session, 'before_flush', lambda session, ctx, instances: None)
            
            # Initialize services
            football_api, _ = initialize_services()
            if not football_api:
                app.logger.error("Failed to initialize FootballAPIService")
                return
                
            team_service = TeamService(football_api)
            
            # Store in app config for global access
            app.config['FOOTBALL_API_SERVICE'] = football_api
            app.config['TEAM_SERVICE'] = team_service
            
            # Register custom JSON encoders for enums
            from flask.json.provider import JSONProvider
            class CustomJSONProvider(JSONProvider):
                def default(self, obj):
                    if isinstance(obj, (MatchStatus, GroupPrivacyType, MemberRole, PredictionStatus)):
                        return obj.name
                    return super().default(obj)
                    
            app.json_provider_class = CustomJSONProvider
            app.json = CustomJSONProvider(app)
            
            app.logger.info("API services and enum handlers initialized successfully")
        except Exception as e:
            app.logger.error(f"Failed to initialize API services: {str(e)}")
            raise

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    configure_logging(app)
    app.logger.info('Flaskr startup')

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={
            'pool_size': 10,
            'pool_timeout': 30,
            'pool_recycle': 1800,
            'max_overflow': 2
        },
        CREATE_TABLES_ON_STARTUP=os.environ.get("CREATE_TABLES_ON_STARTUP") == 'True',
        POPULATE_DATA_ON_STARTUP=os.environ.get("POPULATE_DATA_ON_STARTUP") == 'True',
        DROP_EXISTING_TABLES=os.environ.get("DROP_EXISTING_TABLES") == 'True'
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))

    with app.app_context():
        if app.config.get('CREATE_TABLES_ON_STARTUP'):
            db.create_all()
            app.logger.info("Database tables created successfully")
        
        # Initialize services within app context
        init_services(app)

    @app.route('/populate-data')
    def populate_data():
        try:
            if app.config.get('POPULATE_DATA_ON_STARTUP'):
                from app.api_client import populate_initial_data
                populate_initial_data()
                app.logger.info("Data population completed successfully")
                return 'Data population complete', 200
            return 'Data population not enabled', 200
        except Exception as e:
            app.logger.error(f"Error during data population: {str(e)}")
            return 'Error during data population', 500

    @app.route('/hello')
    def hello():
        return 'Hello, World'

    @app.route('/health')
    def health():
        try:
            # Check database connection
            from sqlalchemy.sql import text
            db.session.execute(text('SELECT 1'))
            return 'OK', 200
        except Exception as e:
            app.logger.error(f"Health check failed: {str(e)}")
            return 'Service Unavailable', 503

    try:
        # Register blueprints
        from app import auth, blog
        from app.group_routes import group_bp
        from app.services.football_api import bp as football_api_bp
        from app.error_handlers import register_error_handlers
        
        app.register_blueprint(auth.bp)
        app.register_blueprint(blog.bp)
        app.register_blueprint(group_bp)
        app.register_blueprint(football_api_bp)
        register_error_handlers(app)
    except ImportError as e:
        app.logger.error(f"Error importing modules: {str(e)}")
        raise

    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return render_template('base.html')

    return app