"""用户资料同步：把 Telegram User 写入 users 表。"""
from datetime import datetime

from repo import users as users_repo
from utils import get_logger

logger = get_logger("user_sync")


def user_fields(user) -> dict:
    """从 Telethon User 提取可入库字段。"""
    return {
        "username": getattr(user, "username", None),
        "first_name": getattr(user, "first_name", None),
        "last_name": getattr(user, "last_name", None),
        "phone": getattr(user, "phone", None),
        "is_bot": bool(getattr(user, "bot", False)),
        "is_premium": bool(getattr(user, "premium", False)),
        "language_code": getattr(user, "lang_code", None),
        "dc_id": getattr(user, "dc_id", None),
        "access_hash": getattr(user, "access_hash", None),
    }


async def sync_user(user, seen_at: datetime | None = None):
    if user is None or getattr(user, "id", None) is None:
        return
    await users_repo.upsert_user(user.id, seen_at=seen_at, **user_fields(user))


async def sync_channel_participants(client, channel_id: int, limit: int | None = None) -> int:
    """遍历频道成员并同步资料，返回处理人数。"""
    count = 0
    async for participant in client.iter_participants(channel_id, limit=limit):
        await sync_user(participant)
        count += 1
    logger.info("频道 %s 用户资料同步完成：%s 人", channel_id, count)
    return count
