"""APScheduler 定时任务：成员监控、全量同步、消息统计、邀请链接、日报。"""
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from services import invite_links, member_monitor, member_sync, message_stats, report
from telethon_client import get_client
from utils import get_logger

logger = get_logger("scheduler")


async def _monitor(cid: int):
    try:
        n = await member_monitor.monitor_channel(get_client(), cid)
        if n:
            logger.info("频道 %s 成员监控：处理 %s 条事件", cid, n)
    except Exception as exc:  # noqa: BLE001
        logger.error("频道 %s 成员监控失败：%s", cid, exc)


async def _sync(cid: int):
    try:
        await member_sync.full_sync(get_client(), cid)
    except Exception as exc:  # noqa: BLE001
        logger.error("频道 %s 全量同步失败：%s", cid, exc)


async def _stats(cid: int):
    try:
        await message_stats.collect_message_stats(get_client(), cid, config.MESSAGE_STATS_LIMIT)
    except Exception as exc:  # noqa: BLE001
        logger.error("频道 %s 消息统计失败：%s", cid, exc)


async def _invites(cid: int):
    try:
        await invite_links.sync_invite_links(get_client(), cid)
    except Exception as exc:  # noqa: BLE001
        logger.error("频道 %s 邀请链接同步失败：%s", cid, exc)


async def _daily(cid: int):
    day = date.today() - timedelta(days=1)
    try:
        await report.generate_daily(cid, day)
        logger.info("频道 %s 已生成 %s 日报", cid, day)
    except Exception as exc:  # noqa: BLE001
        logger.error("频道 %s 日报生成失败：%s", cid, exc)


def build_scheduler(channel_ids: list[int]) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    for cid in channel_ids:
        scheduler.add_job(
            _monitor,
            "interval",
            seconds=config.MEMBER_MONITOR_INTERVAL,
            args=[cid],
            id=f"monitor_{cid}",
            max_instances=1,
            coalesce=True,
        )
        scheduler.add_job(
            _sync,
            "interval",
            seconds=config.MEMBER_SYNC_INTERVAL,
            args=[cid],
            id=f"sync_{cid}",
            max_instances=1,
            coalesce=True,
        )
        scheduler.add_job(
            _stats,
            "interval",
            seconds=config.MESSAGE_STATS_INTERVAL,
            args=[cid],
            id=f"stats_{cid}",
            max_instances=1,
            coalesce=True,
        )
        scheduler.add_job(
            _invites,
            "interval",
            hours=6,
            args=[cid],
            id=f"invites_{cid}",
            max_instances=1,
            coalesce=True,
        )
        scheduler.add_job(
            _daily,
            "cron",
            hour=config.DAILY_REPORT_HOUR,
            minute=config.DAILY_REPORT_MINUTE,
            args=[cid],
            id=f"daily_{cid}",
            max_instances=1,
            coalesce=True,
        )
    return scheduler
