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

DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")  # Add this back

def configure_logging(app):
    # Keep your current logging configuration
    pass

def populate_data_async(app):
    with app.app_context():
        try:
            from app.api_client import populate_initial_data
            populate_initial_data()
            app.logger.info("Background data population completed successfully")
        except Exception as e:
            app.logger.error(f"Background data population failed: {str(e)}")

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
        CREATE_TABLES_ON_STARTUP=os.environ.get("CREATE_TABLES_ON_STARTUP") == 'True',
        POPULATE_DATA_ON_STARTUP=os.environ.get("POPULATE_DATA_ON_STARTUP") == 'True'
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

    # Create database tables if configured
    with app.app_context():
        if app.config.get('CREATE_TABLES_ON_STARTUP'):
            db.create_all()

    @app.route('/hello')
    def hello():
        return 'Hello, World'

    @app.route('/health')
    def health():
        return 'OK', 200

    @app.route('/population-status')  # Add this back
    def population_status():
        if hasattr(app, 'population_thread') and app.population_thread.is_alive():
            return 'Data population in progress', 202
        return 'Data population complete', 200

    # Register blueprints
    try:
        from app import auth, blog, views
        app.register_blueprint(auth.bp)
        app.register_blueprint(blog.bp)
        app.register_blueprint(views.group_bp)

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
    @with_appcontext  # Add this decorator back
    def initialize_scheduler_command():
        try:
            engine = create_engine(DATABASE_URI)
            connection = engine.connect()
            app.logger.info("Connected to database successfully!")
            connection.close()
        except Exception as e:
            app.logger.error("Error connecting to the database:", exc_info=e)
            return

        try:
            from app.cron_job import init_scheduler
            init_scheduler(app)
        except Exception as e:
            app.logger.error("Error starting the scheduler:", exc_info=e)

    # Start data population in background if configured
    if app.config.get('POPULATE_DATA_ON_STARTUP'):
        app.population_thread = threading.Thread(  # Store thread on app
            target=populate_data_async,
            args=(app,),  # Pass app directly
            daemon=True
        )
        app.population_thread.start()
        app.logger.info("Started background data population")

    return app