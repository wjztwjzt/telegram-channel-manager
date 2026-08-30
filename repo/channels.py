"""频道读写。"""
from database import Channel, session_scope


async def upsert_channel(
    channel_id: int,
    *,
    access_hash: int | None = None,
    username: str | None = None,
    title: str | None = None,
    participants_count: int | None = None,
):
    async with session_scope() as session:
        channel = await session.get(Channel, channel_id)
        if channel is None:
            channel = Channel(id=channel_id)
            session.add(channel)
        if access_hash is not None:
            channel.access_hash = access_hash
        if username is not None:
            channel.username = username
        if title is not None:
            channel.title = title
        if participants_count is not None:
            channel.participants_count = participants_count
        await session.commit()
