from apscheduler.schedulers.background import BackgroundScheduler
from app.date_utils import daily_update

def init_scheduler(app):
    scheduler = BackgroundScheduler(timezone='US/Central')
    
    @scheduler.scheduled_job('cron', hour=8, minute=0)
    def scheduled_task():
        with app.app_context():
            daily_update()

    scheduler.start()
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
