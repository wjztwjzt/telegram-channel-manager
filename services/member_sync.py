"""全量成员同步：拉取当前成员，与库内活跃成员做 diff。"""
from datetime import datetime

from repo import members as members_repo
from services import user_sync
from utils import get_logger

logger = get_logger("member_sync")


async def full_sync(client, channel_id: int) -> tuple[int, int]:
    """返回 (当前成员数, 本次发现退出数)。"""
    current_ids: set[int] = set()
    async for participant in client.iter_participants(channel_id):
        current_ids.add(participant.id)
        await user_sync.sync_user(participant)
        await members_repo.ensure_active(channel_id, participant.id)

    db_ids = await members_repo.get_active_member_ids(channel_id)
    left_ids = db_ids - current_ids
    now = datetime.now()
    for user_id in left_ids:
        await members_repo.mark_left(channel_id, user_id, left_at=now, status="left")

    logger.info(
        "频道 %s 全量同步：当前 %s 人，新发现退出 %s 人",
        channel_id,
        len(current_ids),
        len(left_ids),
    )
    return len(current_ids), len(left_ids)
