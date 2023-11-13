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
    db.create_all()

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def close_db(e=None):
    """Close the database session if it exists."""
    db_session = g.pop('db', None)
    
    if db_session is not None:
        db_session.remove()

def init_app(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
