"""消息统计：定时抓取 views/forwards/reactions 存时间序列。"""
from datetime import datetime

from repo import messages as messages_repo
from utils import get_logger

logger = get_logger("message_stats")


def _count_reactions(message) -> int:
    reactions = getattr(message, "reactions", None)
    results = getattr(reactions, "results", None) if reactions else None
    if not results:
        return 0
    return sum(getattr(r, "count", 0) or 0 for r in results)


def _text_of(message) -> str | None:
    text = getattr(message, "text", None) or getattr(message, "message", None)
    if not text:
        return None
    return text[:500]


async def collect_message_stats(client, channel_id: int, limit: int = 50) -> int:
    """抓取最近 N 条消息，刷新快照并写入一条时间序列样本。返回处理条数。"""
    messages = await client.get_messages(channel_id, limit=limit)
    captured_at = datetime.now()
    count = 0

    for message in messages:
        if message is None:
            continue
        views = getattr(message, "views", 0) or 0
        forwards = getattr(message, "forwards", 0) or 0
        reactions = _count_reactions(message)

        await messages_repo.upsert_message_snapshot(
            channel_id,
            message.id,
            date=getattr(message, "date", None),
            author_id=getattr(message, "sender_id", None),
            text=_text_of(message),
            views=views,
            forwards=forwards,
            reactions=reactions,
        )
        await messages_repo.add_message_stat(
            channel_id, message.id, captured_at, views, forwards, reactions
        )
        count += 1

    logger.info("频道 %s 消息统计采集完成：%s 条", channel_id, count)
    return count
