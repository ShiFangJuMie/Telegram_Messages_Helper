import schedule
import time
import os


def job_cleanup():
    os.system("python /app/script_cleanup.py >> /app/cron.log 2>&1")


def job_sync_wechat():
    os.system("python /app/script_sync_wechat.py >> /app/cron.log 2>&1")


def job_aggregated():
    os.system("python /app/script_aggregated.py >> /app/cron.log 2>&1")


def job_aigc():
    os.system("python /app/script_aigc.py >> /app/cron.log 2>&1")


# 每天0点运行
schedule.every().day.at("00:00").do(job_cleanup)
schedule.every().day.at("00:00").do(job_sync_wechat)

# 每天0点5分运行
schedule.every().day.at("00:05").do(job_aggregated)

# 每2小时运行一次，防止接口异常/限频等情况导致遗漏
schedule.every(2).hours.at(":15").do(job_aigc)


# 持续运行守护进程
while True:
    schedule.run_pending()
    time.sleep(60)
