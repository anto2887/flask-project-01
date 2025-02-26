import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, current_app, render_template, redirect, url_for, send_from_directory, jsonify
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from sqlalchemy import create_engine
from flask.cli import with_appcontext

from app.db import db
from app.models import Users, Post, UserResults, Fixture
from app.monitoring import CloudWatchHandler, CustomJSONFormatter, RateLimiter, ApplicationMonitor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

def configure_logging(app):
    """Configure application logging"""
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
            from app.api_client import initialize_services, get_secret
            from app.services.team_service import TeamService
            from app.services.football_api import FootballAPIService
            from app.services.match_monitor import MatchMonitorService
            from app.services.task_scheduler import TaskScheduler
            from app.services.score_processing import ScoreProcessingService
            from app.models import MatchStatus, GroupPrivacyType, MemberRole, PredictionStatus
            
            app.logger.info("Starting API services initialization...")
            
            # First get the API key
            api_key = get_secret()
            if not api_key:
                app.logger.error("Failed to retrieve API key")
                raise ValueError("Failed to retrieve API key")

            # Initialize Football API Service
            app.logger.info("Initializing FootballAPIService...")
            football_api = FootballAPIService(api_key)
            app.logger.info("FootballAPIService initialized successfully")

            # Initialize Team Service
            app.logger.info("Initializing TeamService...")
            team_service = TeamService(football_api)
            app.logger.info("TeamService initialized successfully")
            
            # Store services in app config for global access
            app.config['FOOTBALL_API_SERVICE'] = football_api
            app.config['TEAM_SERVICE'] = team_service
            
            # Initialize score processor based on environment variable
            processor_type = os.environ.get('SCORE_PROCESSOR_TYPE', 'default')
            app.logger.info(f"Initializing ScoreProcessingService with type: {processor_type}")
            score_processor = ScoreProcessingService(processor_type)
            app.config['SCORE_PROCESSOR'] = score_processor
            app.logger.info("ScoreProcessingService initialized successfully")
            
            # Initialize match monitoring
            match_monitor = MatchMonitorService(
                football_api_service=app.config['FOOTBALL_API_SERVICE'],
                score_processor=app.config['SCORE_PROCESSOR']
            )
            
            # Initialize and start task scheduler
            task_scheduler = TaskScheduler(match_monitor)
            if not app.debug:  # Only schedule in production
                task_scheduler.schedule_match_monitoring()
            
            # Store monitoring services in app config
            app.config['MATCH_MONITOR'] = match_monitor
            app.config['TASK_SCHEDULER'] = task_scheduler
            
            # Register custom JSON encoders for enums
            from flask.json.provider import JSONProvider
            class CustomJSONProvider(JSONProvider):
                def dumps(self, obj, **kwargs):
                    import json
                    return json.dumps(obj, default=self.default, **kwargs)

                def loads(self, s, **kwargs):
                    import json
                    return json.loads(s, **kwargs)

                def default(self, obj):
                    if isinstance(obj, (MatchStatus, GroupPrivacyType, MemberRole, PredictionStatus)):
                        return obj.name
                    return super().default(obj)
                    
            app.json_provider_class = CustomJSONProvider
            app.json = CustomJSONProvider(app)
            
            # Verify services are properly initialized
            app.logger.info("Verifying service initialization...")
            if not app.config.get('TEAM_SERVICE'):
                app.logger.error("TeamService not found in app config after initialization")
                raise RuntimeError("TeamService initialization verification failed")
            
            if not app.config.get('FOOTBALL_API_SERVICE'):
                app.logger.error("FootballAPIService not found in app config after initialization")
                raise RuntimeError("FootballAPIService initialization verification failed")

            app.logger.info("All API services and enum handlers initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Failed to initialize API services: {str(e)}", exc_info=True)
            raise

def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Add CORS support for all /api routes
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Configure logging
    configure_logging(app)
    app.logger.info('Flaskr startup')

    # Configure application
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
        DROP_EXISTING_TABLES=os.environ.get("DROP_EXISTING_TABLES") == 'True',
        # CSRF settings
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_CHECK_DEFAULT=True,
        WTF_CSRF_TIME_LIMIT=3600,  # 1 hour token expiration
        # React configuration
        REACT_COMPONENTS_PATH=os.path.join(app.static_folder, 'js', 'components')
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # Initialize database
    db.init_app(app)

    # Setup login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))

    # Add React component handler
    @app.route('/static/js/components/<path:filename>')
    def serve_react_component(filename):
        return send_from_directory(app.config['REACT_COMPONENTS_PATH'], filename)

    with app.app_context():
        # Create database tables if needed
        if app.config.get('CREATE_TABLES_ON_STARTUP'):
            db.create_all()
            app.logger.info("Database tables created successfully")
        
        # Initialize services
        init_services(app)

    # Register routes
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

    @app.route('/api/health')
    def health():
        try:
            # Check database connection
            from sqlalchemy.sql import text
            db.session.execute(text('SELECT 1'))
            
            # Check services
            if not app.config.get('TEAM_SERVICE'):
                return jsonify({'status': 'error', 'message': 'Team Service Unavailable'}), 503
            if not app.config.get('FOOTBALL_API_SERVICE'):
                return jsonify({'status': 'error', 'message': 'Football API Service Unavailable'}), 503
                
            return jsonify({'status': 'success', 'message': 'OK'}), 200
        except Exception as e:
            app.logger.error(f"Health check failed: {str(e)}")
            return jsonify({'status': 'error', 'message': 'Service Unavailable'}), 503

    try:
        # Register web blueprints
        from app.api.group_routes import group_bp
        # ... other web blueprints ...
        
        app.register_blueprint(group_bp, url_prefix='/groups')
        # ... register other web blueprints ...
        
        # Register API blueprints with /api prefix
        from app.api.auth import bp as auth_bp
        from app.api.group_api import group_api_bp
        from app.api.matches import bp as matches_bp
        from app.api.predictions import bp as predictions_bp
        from app.api.users import bp as users_bp
        
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(group_api_bp, url_prefix='/api/groups')
        app.register_blueprint(matches_bp, url_prefix='/api/matches')
        app.register_blueprint(predictions_bp, url_prefix='/api/predictions')
        app.register_blueprint(users_bp, url_prefix='/api/users')
        
        # Register error handlers
        from app.error_handlers import register_api_error_handlers, register_error_handlers
        register_api_error_handlers(app)
        register_error_handlers(app)
        
        app.logger.info("All blueprints registered successfully")
    except ImportError as e:
        app.logger.error(f"Error importing modules: {str(e)}", exc_info=True)
        raise

    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return render_template('base.html')

    return app