"""邀请链接来源追踪。"""
from telethon import functions

from repo import invite_links as invite_repo
from utils import get_logger

logger = get_logger("invite_links")


async def sync_invite_links(client, channel_id: int) -> int:
    """拉取频道所有导出邀请链接并入库，返回链接数。"""
    me = await client.get_me()
    result = await client(
        functions.messages.GetExportedChatInvitesRequest(
            peer=channel_id,
            admin=me,
            revoked=False,
            limit=100,
        )
    )
    invites = getattr(result, "invites", []) or []
    for inv in invites:
        link = getattr(inv, "link", None)
        name = getattr(inv, "title", None) or link
        if link:
            await invite_repo.record_link(channel_id, link, name)
    logger.info("频道 %s 邀请链接同步完成：%s 条", channel_id, len(invites))
    return len(invites)
