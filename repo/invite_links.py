"""邀请链接清单读写。"""
from sqlalchemy import select

from database import InviteLink, session_scope


async def record_link(channel_id: int, link: str, name: str | None = None):
    async with session_scope() as session:
        existing = await session.scalar(
            select(InviteLink).where(
                InviteLink.channel_id == channel_id, InviteLink.link == link
            )
        )
        if existing:
            if name and existing.name != name:
                existing.name = name
                await session.commit()
            return
        session.add(InviteLink(channel_id=channel_id, link=link, name=name))
        await session.commit()


async def get_links(channel_id: int) -> list[InviteLink]:
    async with session_scope() as session:
        result = await session.execute(
            select(InviteLink).where(InviteLink.channel_id == channel_id)
        )
        return list(result.scalars().all())
