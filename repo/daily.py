"""日报快照读写。"""
from datetime import date

from database import DailyStat, session_scope


async def upsert_daily(
    day: date,
    channel_id: int,
    *,
    new_members: int = 0,
    left_members: int = 0,
    net_growth: int = 0,
    total_views: int = 0,
    total_forwards: int = 0,
    total_reactions: int = 0,
    posts: int = 0,
):
    async with session_scope() as session:
        row = await session.get(DailyStat, (day, channel_id))
        if row is None:
            row = DailyStat(date=day, channel_id=channel_id)
            session.add(row)
        row.new_members = new_members
        row.left_members = left_members
        row.net_growth = net_growth
        row.total_views = total_views
        row.total_forwards = total_forwards
        row.total_reactions = total_reactions
        row.posts = posts
        await session.commit()
