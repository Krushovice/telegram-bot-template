from apscheduler.schedulers.asyncio import AsyncIOScheduler


def schedule_tasks(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    # Примеры:
    # scheduler.add_job(lambda: print("tick"), "interval", minutes=5)
    # scheduler.add_job(send_daily_report, trigger="cron", hour=7, minute=0, kwargs={"bot": bot})

    return scheduler
