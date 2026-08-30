"""频道成员关系读写。"""
from datetime import datetime

from sqlalchemy import func, select

from database import ChannelMember, session_scope


async def _get_or_create(session, channel_id: int, user_id: int) -> ChannelMember:
    member = await session.get(ChannelMember, (channel_id, user_id))
    if member is None:
        member = ChannelMember(channel_id=channel_id, user_id=user_id)
        session.add(member)
    return member


async def mark_joined(
    channel_id: int,
    user_id: int,
    *,
    joined_at: datetime,
    inviter_id: int | None = None,
    source: str | None = None,
):
    """成员加入：写 joined_at、来源，清空 left_at 并置为 member。"""
    async with session_scope() as session:
        member = await _get_or_create(session, channel_id, user_id)
        member.joined_at = joined_at
        member.left_at = None
        member.status = "member"
        if inviter_id is not None:
            member.inviter_id = inviter_id
        if source is not None:
            member.source = source
        member.updated_at = datetime.now()
        await session.commit()


async def mark_left(
    channel_id: int, user_id: int, *, left_at: datetime, status: str = "left"
):
    """成员退出：写 left_at 与状态。"""
    async with session_scope() as session:
        member = await _get_or_create(session, channel_id, user_id)
        member.left_at = left_at
        member.status = status
        member.updated_at = datetime.now()
        await session.commit()


async def ensure_active(channel_id: int, user_id: int):
    """全量同步用：确保成员处于活跃态（不覆盖已有 joined_at）。"""
    async with session_scope() as session:
        member = await session.get(ChannelMember, (channel_id, user_id))
        if member is None:
            member = ChannelMember(
                channel_id=channel_id,
                user_id=user_id,
                status="member",
                joined_at=datetime.now(),
            )
            session.add(member)
        elif member.status != "member":
            member.status = "member"
            member.left_at = None
        member.updated_at = datetime.now()
        await session.commit()


async def get_active_member_ids(channel_id: int) -> set[int]:
    async with session_scope() as session:
        result = await session.execute(
            select(ChannelMember.user_id).where(
                ChannelMember.channel_id == channel_id,
                ChannelMember.status == "member",
            )
        )
        return {row[0] for row in result.all()}


async def count_members(channel_id: int, status: str = "member") -> int:
    async with session_scope() as session:
        result = await session.scalar(
            select(func.count())
            .select_from(ChannelMember)
            .where(ChannelMember.channel_id == channel_id, ChannelMember.status == status)
        )
        return int(result or 0)
