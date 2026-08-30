"""报表聚合：今日/周期日报、来源分组、新增/退出用户列表。"""
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select

from database import DailyStat, MemberEvent, Message, session_scope
from repo import daily as daily_repo
from repo import members as members_repo

JOIN_TYPES = ("JOIN", "INVITE")
LEAVE_TYPES = ("LEAVE", "KICK")


def _day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min)
    return start, start + timedelta(days=1)


async def _count_events(channel_id: int, event_types, start: datetime, end: datetime) -> int:
    async with session_scope() as session:
        result = await session.scalar(
            select(func.count())
            .select_from(MemberEvent)
            .where(
                MemberEvent.channel_id == channel_id,
                MemberEvent.event_type.in_(event_types),
                MemberEvent.event_time >= start,
                MemberEvent.event_time < end,
            )
        )
        return int(result or 0)


async def _content_stats(channel_id: int, start: datetime, end: datetime):
    """当日发文的消息快照聚合：返回 (posts, views, forwards, reactions)。"""
    async with session_scope() as session:
        rows = await session.execute(
            select(Message).where(
                Message.channel_id == channel_id,
                Message.date >= start,
                Message.date < end,
            )
        )
        messages = rows.scalars().all()
        return (
            len(messages),
            sum(m.views or 0 for m in messages),
            sum(m.forwards or 0 for m in messages),
            sum(m.reactions or 0 for m in messages),
        )


async def get_source_breakdown(channel_id: int, day: date) -> list[tuple[str, int]]:
    """按邀请来源统计当日新增，返回 [(来源, 人数)]。"""
    start, end = _day_bounds(day)
    async with session_scope() as session:
        rows = await session.execute(
            select(MemberEvent.invite_link, func.count())
            .where(
                MemberEvent.channel_id == channel_id,
                MemberEvent.event_type.in_(JOIN_TYPES),
                MemberEvent.event_time >= start,
                MemberEvent.event_time < end,
            )
            .group_by(MemberEvent.invite_link)
            .order_by(func.count().desc())
        )
        return [(link or "其他", int(cnt)) for link, cnt in rows.all()]


async def get_recent_events(
    channel_id: int, event_types, day: date, limit: int = 20
) -> list[MemberEvent]:
    start, end = _day_bounds(day)
    async with session_scope() as session:
        rows = await session.execute(
            select(MemberEvent)
            .where(
                MemberEvent.channel_id == channel_id,
                MemberEvent.event_type.in_(event_types),
                MemberEvent.event_time >= start,
                MemberEvent.event_time < end,
            )
            .order_by(MemberEvent.event_time.desc())
            .limit(limit)
        )
        return list(rows.scalars().all())


async def get_today_report(channel_id: int) -> dict:
    """组装今日日报数据。"""
    today = date.today()
    start, end = _day_bounds(today)
    new_members = await _count_events(channel_id, JOIN_TYPES, start, end)
    left_members = await _count_events(channel_id, LEAVE_TYPES, start, end)
    posts, views, forwards, reactions = await _content_stats(channel_id, start, end)
    current = await members_repo.count_members(channel_id, "member")
    sources = await get_source_breakdown(channel_id, today)

    return {
        "date": today,
        "current": current,
        "new": new_members,
        "left": left_members,
        "net": new_members - left_members,
        "posts": posts,
        "views": views,
        "forwards": forwards,
        "reactions": reactions,
        "sources": sources,
    }


async def generate_daily(channel_id: int, day: date) -> dict:
    """计算某日日报并写入 daily_stats。"""
    start, end = _day_bounds(day)
    new_members = await _count_events(channel_id, JOIN_TYPES, start, end)
    left_members = await _count_events(channel_id, LEAVE_TYPES, start, end)
    posts, views, forwards, reactions = await _content_stats(channel_id, start, end)
    net = new_members - left_members

    await daily_repo.upsert_daily(
        day,
        channel_id,
        new_members=new_members,
        left_members=left_members,
        net_growth=net,
        total_views=views,
        total_forwards=forwards,
        total_reactions=reactions,
        posts=posts,
    )
    return {
        "date": day,
        "new": new_members,
        "left": left_members,
        "net": net,
        "posts": posts,
        "views": views,
        "forwards": forwards,
        "reactions": reactions,
    }


async def get_period_report(channel_id: int, days: int) -> list[DailyStat]:
    start = date.today() - timedelta(days=days - 1)
    async with session_scope() as session:
        rows = await session.execute(
            select(DailyStat)
            .where(DailyStat.channel_id == channel_id, DailyStat.date >= start)
            .order_by(DailyStat.date)
        )
        return list(rows.scalars().all())
