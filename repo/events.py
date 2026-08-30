"""成员事件流水写入（按 telegram_event_id 去重）。"""
from datetime import datetime

from sqlalchemy import select

from database import MemberEvent, session_scope


async def add_event(
    channel_id: int,
    user_id: int,
    event_type: str,
    event_time: datetime,
    *,
    inviter_id: int | None = None,
    invite_link: str | None = None,
    telegram_event_id: int | None = None,
) -> bool:
    """新增一条成员事件。若 telegram_event_id 已存在则跳过，返回是否写入。"""
    async with session_scope() as session:
        if telegram_event_id is not None:
            exists = await session.scalar(
                select(MemberEvent.id).where(
                    MemberEvent.telegram_event_id == telegram_event_id
                )
            )
            if exists:
                return False

        session.add(
            MemberEvent(
                channel_id=channel_id,
                user_id=user_id,
                event_type=event_type,
                event_time=event_time,
                inviter_id=inviter_id,
                invite_link=invite_link,
                telegram_event_id=telegram_event_id,
            )
        )
        await session.commit()
        return True
