import asyncio
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

async def signal_job():
    """Run signal engine every hour"""
    from signals.alert_bot import run_signal_engine
    print(f"[{datetime.now()}] Running signal engine...")
    result = await run_signal_engine()
    if result.get("signals"):
        print(f"Signals found: {result['signals']}")
    else:
        print("No signals detected")

async def main():
    scheduler = AsyncIOScheduler()
    
    # Run every hour
    scheduler.add_job(
        signal_job,
        trigger=IntervalTrigger(hours=1),
        id="signal_engine",
        replace_existing=True
    )
    
    scheduler.start()
    print("✅ Signal scheduler started - running every hour")
    
    # Run once immediately
    await signal_job()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
