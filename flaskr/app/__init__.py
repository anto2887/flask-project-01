import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, current_app, render_template
from sqlalchemy import create_engine
from flask.cli import with_appcontext

from app.db import db
from app.models import Users, Post, UserResults

# from .views import group_bp
# app.register_blueprint(group_bp)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Logging configuration
    if not app.debug:
        log_dir = '/flaskr/logs'
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        file_handler = RotatingFileHandler(os.path.join(log_dir, 'flaskr.log'),
                                           maxBytes=10_240_000, backupCount=5)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Flaskr startup')

    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI=DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    app.config["CREATE_TABLES_ON_STARTUP"] = os.environ.get("CREATE_TABLES_ON_STARTUP") == 'True'

    # Initialize DB with app
    db.init_app(app)

    with app.app_context():
        if app.config.get('CREATE_TABLES_ON_STARTUP'):
            db.create_all()

    @app.route('/hello')
    def hello():
        return 'Hello, World'

    @app.route('/health')
    def health():
        return 'OK', 200

    from. import auth, blog, views
    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    app.register_blueprint(views.group_bp)

    @app.route('/')
    def index():
        return render_template('base.html')

    @app.cli.command('init-scheduler')
    @with_appcontext
    def initialize_scheduler_command():
        try:
            engine = create_engine(DATABASE_URI)
            connection = engine.connect()
            current_app.logger.info("Connected to database successfully!")
            connection.close()
        except Exception as e:
            current_app.logger.error("Error connecting to the database:", exc_info=e)
            return None
        try:
            from app.cron_job import scheduler  # Moved scheduler import inside the function
            scheduler()
            current_app.logger.info("Scheduler started successfully!")
        except Exception as e:
            current_app.logger.error("Error starting the scheduler:", exc_info=e)

    return app

app = create_app()
