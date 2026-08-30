"""入口：初始化数据库 → 启动 userbot → 解析频道 → 调度器 → 管理机器人。"""
import asyncio

import config
import registry
from bot.client import start_bot
from database import init_db
from repo import channels as channels_repo
from scheduler import build_scheduler
from services import invite_links, member_sync
from telethon_client import get_client, resolve_channel, start_client
from utils import get_logger

logger = get_logger("main")


async def resolve_channels():
    """解析配置的频道，写入注册表与 channels 表。"""
    for ref in config.CHANNELS:
        try:
            channel_id, entity = await resolve_channel(ref)
            title = getattr(entity, "title", None) or ref
            registry.channels[channel_id] = title
            await channels_repo.upsert_channel(
                channel_id,
                access_hash=getattr(entity, "access_hash", None),
                username=getattr(entity, "username", None),
                title=title,
            )
            logger.info("频道已就绪：%s (id=%s)", title, channel_id)
        except Exception as exc:  # noqa: BLE001
            logger.error("解析频道 %s 失败：%s", ref, exc)


async def initial_sync():
    """后台执行首次全量同步与邀请链接抓取。"""
    for cid in list(registry.channels):
        try:
            await invite_links.sync_invite_links(get_client(), cid)
            await member_sync.full_sync(get_client(), cid)
        except Exception as exc:  # noqa: BLE001
            logger.error("频道 %s 初始化同步失败：%s", cid, exc)


async def main():
    await init_db()
    await start_client()
    await resolve_channels()

    scheduler = build_scheduler(list(registry.channels))
    scheduler.start()
    logger.info("调度器已启动，共监控 %s 个频道", len(registry.channels))

    asyncio.create_task(initial_sync())

    await start_bot()  # 阻塞直到退出


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("进程已退出")
