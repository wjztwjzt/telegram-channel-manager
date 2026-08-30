"""消息快照与统计时间序列读写。"""
from datetime import datetime

from sqlalchemy import select

from database import Message, MessageStat, session_scope


async def upsert_message_snapshot(
    channel_id: int,
    message_id: int,
    *,
    date: datetime | None = None,
    author_id: int | None = None,
    text: str | None = None,
    views: int = 0,
    forwards: int = 0,
    reactions: int = 0,
):
    async with session_scope() as session:
        msg = await session.get(Message, (channel_id, message_id))
        if msg is None:
            msg = Message(channel_id=channel_id, message_id=message_id)
            session.add(msg)
        msg.date = date
        msg.author_id = author_id
        msg.text = text
        msg.views = views
        msg.forwards = forwards
        msg.reactions = reactions
        msg.updated_at = datetime.now()
        await session.commit()


async def add_message_stat(
    channel_id: int,
    message_id: int,
    captured_at: datetime,
    views: int,
    forwards: int,
    reactions: int,
):
    async with session_scope() as session:
        stat = await session.get(
            MessageStat, (channel_id, message_id, captured_at)
        )
        if stat is None:
            stat = MessageStat(
                channel_id=channel_id,
                message_id=message_id,
                captured_at=captured_at,
            )
            session.add(stat)
        stat.views = views
        stat.forwards = forwards
        stat.reactions = reactions
        await session.commit()


async def get_top_messages(channel_id: int, limit: int = 10) -> list[Message]:
    """按浏览数取频道最新快照 Top N 消息。"""
    async with session_scope() as session:
        rows = await session.execute(
            select(Message)
            .where(Message.channel_id == channel_id)
            .order_by(Message.views.desc())
            .limit(limit)
        )
        return list(rows.scalars().all())
