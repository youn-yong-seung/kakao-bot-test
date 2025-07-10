import pytz
from apscheduler.schedulers.background import BackgroundScheduler

# 전역 스케줄러 생성
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Seoul'))
scheduler.start()

def background_schedule_cron(func, hour=0, minute=0, job_id=None):
    scheduler.add_job(
        func,
        trigger='cron',
        hour=hour,
        minute=minute,
        id=job_id,
        replace_existing=True  # 동일 ID 있으면 덮어쓰기
    )

def background_schedule_interval(func, seconds=0, minutes=0, hours=0, job_id=None):
    scheduler.add_job(
        func,
        trigger='interval',
        seconds=seconds,
        minutes=minutes,
        hours=hours,
        id=job_id,
        replace_existing=True  # 동일 ID 있으면 덮어쓰기
    )