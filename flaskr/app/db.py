from flask import current_app, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, MetaData, text
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
        # Drop all tables and sequences if environment variable is set
        if current_app.config.get('DROP_EXISTING_TABLES'):
            current_app.logger.info("Dropping existing tables and sequences...")
            # Drop sequences first
            with db.engine.connect() as conn:
                conn.execute(text("""
                    DO $$ 
                    DECLARE 
                        seq_name text;
                    BEGIN 
                        FOR seq_name IN (SELECT sequence_name 
                                       FROM information_schema.sequences 
                                       WHERE sequence_schema = 'public') 
                        LOOP 
                            EXECUTE 'DROP SEQUENCE IF EXISTS public.' || seq_name || ' CASCADE'; 
                        END LOOP; 
                    END $$;
                """))
                conn.commit()
            
            # Then drop all tables
            db.drop_all()
            current_app.logger.info("Tables and sequences dropped successfully")
        
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