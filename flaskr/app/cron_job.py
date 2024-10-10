from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app import app
from app.date_utils import daily_update

def scheduler():
    sched = BackgroundScheduler(timezone='US/Central')
    
    def task_with_callback():
        with app.app_context():
            try:
                daily_update()
                app.logger.info("Daily update completed successfully.")
            except Exception as e:
                app.logger.error("Error during daily update:", exc_info=e)

    # Schedule daily_update to run every day at 8:00 AM
    sched.add_job(task_with_callback, CronTrigger(hour=8, minute=0))
    
    sched.start()
    app.logger.info("Scheduler started.")


# The below line of code is an infinite loop that broke my code the first time I tested it
    # try:
    #     # This is here to simulate application activity (which keeps the main thread alive).
    #     while True:
    #         pass
    # except (KeyboardInterrupt, SystemExit):
    #     # Shut down the scheduler gracefully on exit
    #     sched.shutdown()

# # Start the scheduler when the script runs
# if __name__ == "__main__":
#     scheduler()
