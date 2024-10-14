from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app

def init_scheduler(app):
    scheduler = BackgroundScheduler(timezone='US/Central')
    
    @scheduler.scheduled_job('cron', hour=8, minute=0)
    def scheduled_task():
        with app.app_context():
            current_app.logger.info("Starting scheduled daily update")
            try:
                from app.date_utils import daily_update
                daily_update()
                current_app.logger.info("Daily update completed successfully")
            except Exception as e:
                current_app.logger.error(f"Error during daily update: {str(e)}")

    scheduler.start()
    current_app.logger.info("Scheduler started successfully")