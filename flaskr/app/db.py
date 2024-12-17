from flask import current_app, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, text, inspect
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
        if current_app.config.get('DROP_EXISTING_TABLES'):
            current_app.logger.info("Dropping existing tables and sequences...")
            with db.engine.connect() as conn:
                # Get current user
                result = conn.execute(text("SELECT CURRENT_USER"))
                current_user = result.scalar()
                current_app.logger.info(f"Initializing database as user: {current_user}")

                # Drop and recreate schema
                conn.execute(text("""
                    DROP SCHEMA IF EXISTS public CASCADE;
                    CREATE SCHEMA public;
                """))
                
                # Grant privileges to current user
                conn.execute(text(f"GRANT ALL ON SCHEMA public TO {current_user}"))
                conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
                
                # Commit changes
                conn.execute(text("COMMIT"))
                current_app.logger.info("Schema reset completed")
        
        # Create tables
        db.create_all()
        current_app.logger.info("Database initialized successfully")
    except Exception as e:
        current_app.logger.error(f"Database initialization failed: {str(e)}")
        raise

def close_db(e=None):
    """Close the database session if it exists."""
    db_session = g.pop('db', None)
    if db_session is not None:
        db_session.remove()

def init_app(app):
    """Initialize the database with the Flask app."""
    db.init_app(app)
    app.teardown_appcontext(close_db)