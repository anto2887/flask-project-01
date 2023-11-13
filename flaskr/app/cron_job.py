from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.date_utils import date_init
from app import app


# The function to schedule tasks
def scheduler():
    sched = BackgroundScheduler(timezone='US/Central')  # Set timezone to Central Time
    
    # Adding the callback to our date_init function
    def task_with_callback():
        with app.app_context():
            try:
                scraped_data = date_init()
                if scraped_data is not None:
                    app.logger.info("Running compare_and_update function.")
                    from app.compare import compare_and_update
                    compare_and_update()
                else:
                    app.logger.info("No data scraped today, skipping compare_and_update.")
            except Exception as e:
                app.logger.error("Error during scheduled task:", exc_info=e)

    # Schedule date_init to run every day at 8:00 AM
    sched.add_job(task_with_callback, CronTrigger(hour=8, minute=0))
    
    # Start the scheduler
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
