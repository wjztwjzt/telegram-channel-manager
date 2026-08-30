"""成员事件监控：轮询管理员日志，抓 JOIN/LEAVE/KICK/INVITE。"""
from datetime import datetime

from telethon.tl.types import (
    ChannelAdminLogEventActionParticipantInvite,
    ChannelAdminLogEventActionParticipantJoin,
    ChannelAdminLogEventActionParticipantJoinByInvite,
    ChannelAdminLogEventActionParticipantLeave,
    ChannelAdminLogEventActionParticipantToggleBan,
)

from repo import events as events_repo
from repo import invite_links as invite_repo
from repo import members as members_repo
from services import user_sync
from utils import get_logger

logger = get_logger("member_monitor")

# 每个频道已处理到的管理员日志事件 ID（内存游标，重启后靠唯一索引去重兜底）
_last_event_id: dict[int, int] = {}


def _peer_user_id(peer) -> int | None:
    if peer is None:
        return None
    if isinstance(peer, int):
        return peer
    return getattr(peer, "user_id", None)


def _parse_event(ev):
    """解析一条管理员日志事件，返回 (event_type, user_id, inviter_id, invite_link)。"""
    action = ev.action

    if isinstance(action, ChannelAdminLogEventActionParticipantJoin):
        return "JOIN", ev.user_id, None, None

    if isinstance(action, ChannelAdminLogEventActionParticipantLeave):
        return "LEAVE", ev.user_id, None, None

    if isinstance(action, ChannelAdminLogEventActionParticipantInvite):
        user_id = _peer_user_id(getattr(action, "participant_id", None))
        return "INVITE", user_id, ev.user_id, None

    if isinstance(action, ChannelAdminLogEventActionParticipantJoinByInvite):
        invite = getattr(action, "invite", None)
        link = getattr(invite, "link", None) or getattr(invite, "invite_link", None)
        return "JOIN", ev.user_id, None, link

    if isinstance(action, ChannelAdminLogEventActionParticipantToggleBan):
        new_participant = getattr(action, "new_participant", None)
        if getattr(new_participant, "banned_rights", None):
            return "KICK", _peer_user_id(getattr(new_participant, "peer", None)), ev.user_id, None
        return None, None, None, None

    return None, None, None, None


async def _handle_event(client, channel_id: int, ev) -> bool:
    event_type, user_id, inviter_id, invite_link = _parse_event(ev)
    if not event_type or not user_id:
        return False

    # 同步事件携带的用户对象（actor）
    await user_sync.sync_user(getattr(ev, "user", None), seen_at=ev.date)

    event_time = ev.date if ev.date else datetime.now()

    written = await events_repo.add_event(
        channel_id,
        user_id,
        event_type,
        event_time,
        inviter_id=inviter_id,
        invite_link=invite_link,
        telegram_event_id=ev.id,
    )
    if not written:
        return False

    if invite_link:
        await invite_repo.record_link(channel_id, invite_link)

    # 同步更新成员状态
    if event_type in ("JOIN", "INVITE"):
        await members_repo.mark_joined(
            channel_id, user_id, joined_at=event_time, inviter_id=inviter_id, source=invite_link
        )
    elif event_type in ("LEAVE", "KICK"):
        await members_repo.mark_left(
            channel_id, user_id, left_at=event_time, status="kicked" if event_type == "KICK" else "left"
        )
    return True


async def monitor_channel(client, channel_id: int, limit: int = 100) -> int:
    """拉取并处理某频道最近的管理员日志，返回本次处理事件数。"""
    min_id = _last_event_id.get(channel_id, 0)
    events = await client.get_admin_log(
        channel_id,
        join=True,
        leave=True,
        invite=True,
        kick=True,
        limit=limit,
        min_id=min_id,
    )

    processed = 0
    max_id = min_id
    for ev in events:
        if ev.id > max_id:
            max_id = ev.id
        if ev.id <= min_id:
            continue
        try:
            if await _handle_event(client, channel_id, ev):
                processed += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("处理频道 %s 事件 %s 失败：%s", channel_id, ev.id, exc)

    _last_event_id[channel_id] = max_id
    return processed
