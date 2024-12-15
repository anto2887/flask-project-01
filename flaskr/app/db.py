from flask import current_app, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData
import click

# Set up the SQLAlchemy instance
db = SQLAlchemy()

def get_db():
    """Get the SQLAlchemy database instance."""
    if 'db' not in g:
        g.db = db
    return g.db

def init_db():
    """Initialize the database."""
    try:
        db.create_all()
        current_app.logger.info("Database initialized successfully")
    except Exception as e:
        current_app.logger.error(f"Database initialization failed: {str(e)}")
        raise

# Removed the Flask CLI command as we're not using it anymore
def close_db(e=None):
    """Close the database session if it exists."""
    db_session = g.pop('db', None)
    if db_session is not None:
        db_session.remove()

def init_app(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
    app.teardown_appcontext(close_db)