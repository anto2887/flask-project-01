import os
import sys
import logging
import threading
from logging.handlers import RotatingFileHandler

from flask import Flask, current_app, render_template, redirect, url_for, jsonify
from flask_login import LoginManager, current_user
from sqlalchemy import create_engine
from flask.cli import with_appcontext

from app.db import db
from app.models import Users, Post, UserResults, Fixture, InitializationStatus

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

def configure_logging(app):
    if not app.debug:
        log_dir = '/flaskr/logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'flaskr.log'),
            maxBytes=10_240_000,
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        # Also log to stderr for container logs
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        stream_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO)

def populate_data_async(app):
    with app.app_context():
        try:
            from app.api_client import populate_initial_data, is_initialization_complete
            if not is_initialization_complete():
                populate_initial_data()
            app.logger.info("Background data population completed successfully")
        except Exception as e:
            app.logger.error(f"Background data population failed: {str(e)}")

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        app.logger.error(f"Error creating instance path: {str(e)}")
    
    # Configure logging first
    configure_logging(app)
    app.logger.info('Flaskr startup')
    
    # Load configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(24)),
        SQLALCHEMY_DATABASE_URI=os.environ.get("SQLALCHEMY_DATABASE_URI"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CREATE_TABLES_ON_STARTUP=os.environ.get("CREATE_TABLES_ON_STARTUP") == 'True',
        POPULATE_DATA_ON_STARTUP=os.environ.get("POPULATE_DATA_ON_STARTUP") == 'True'
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.update(test_config)

    # Initialize database
    db.init_app(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return Users.query.get(int(user_id))

    # Create database tables if configured
    if app.config.get('CREATE_TABLES_ON_STARTUP'):
        with app.app_context():
            try:
                db.create_all()
                app.logger.info("Database tables created successfully")
            except Exception as e:
                app.logger.error(f"Error creating database tables: {str(e)}")
                raise

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Register routes
    @app.route('/hello')
    def hello():
        return 'Hello, World'

    @app.route('/health')
    def health():
        try:
            # Verify database connection
            db.session.execute('SELECT 1')
            return jsonify({'status': 'healthy'}), 200
        except Exception as e:
            app.logger.error(f"Health check failed: {str(e)}")
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

    @app.route('/initialization-status')
    def initialization_status():
        latest_status = InitializationStatus.query.order_by(
            InitializationStatus.timestamp.desc()
        ).first()
        if latest_status:
            return jsonify({
                'status': latest_status.status,
                'timestamp': latest_status.timestamp.isoformat(),
                'details': latest_status.details
            })
        return jsonify({'status': 'unknown'}), 404

    # Register blueprints
    try:
        from app import auth, blog, views
        app.register_blueprint(auth.bp)
        app.register_blueprint(blog.bp)
        app.register_blueprint(views.group_bp)
        
        # Initialize blog module
        blog.init_app(app)
    except ImportError as e:
        app.logger.error(f"Error importing modules: {str(e)}")
        raise

    @app.route('/')
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return render_template('base.html')

    @app.cli.command('init-scheduler')
    def initialize_scheduler_command():
        """Initialize the background task scheduler."""
        try:
            # Test database connection
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            with engine.connect() as connection:
                connection.execute('SELECT 1')
            app.logger.info("Connected to database successfully!")
            
            # Initialize scheduler
            from app.cron_job import init_scheduler
            init_scheduler(app)
            app.logger.info("Scheduler initialized successfully")
        except Exception as e:
            app.logger.error("Error initializing scheduler:", exc_info=e)
            raise

    # Start background data population if configured
    if app.config.get('POPULATE_DATA_ON_STARTUP'):
        population_thread = threading.Thread(
            target=populate_data_async,
            args=(app._get_current_object(),),
            daemon=True
        )
        population_thread.start()
        app.logger.info("Started background data population")

    return app