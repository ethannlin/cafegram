from apscheduler.schedulers.background import BlockingScheduler
import pytz

from app import create_app

sched = BlockingScheduler()
app = create_app()

@sched.scheduled_job('cron', day_of_week='mon-sun', hour=0, minute=0, second=0, timezone=pytz.timezone('US/Pacific'))
def update_playlists_job():
    with app.app_context():
        from app.models import Users, CustomPlaylists
        Users.update_playlists()
        CustomPlaylists.update_playlists()
        app.logger.info('Updated playlists for all users.')

sched.start()