"""用户资料读写：首次 INSERT，资料变化才 UPDATE。"""
from datetime import datetime

from sqlalchemy import select

from database import User, session_scope

# 可被 upsert 覆盖的资料字段
_UPDATABLE = (
    "username",
    "first_name",
    "last_name",
    "full_name",
    "phone",
    "is_bot",
    "is_premium",
    "language_code",
    "dc_id",
    "access_hash",
)


async def upsert_user(user_id: int, seen_at: datetime | None = None, **fields) -> bool:
    """写入/更新用户。返回是否产生了数据库变更。"""
    now = seen_at or datetime.now()
    async with session_scope() as session:
        user = await session.get(User, user_id)
        if user is None:
            session.add(
                User(
                    id=user_id,
                    first_seen=now,
                    last_seen=now,
                    **{k: v for k, v in fields.items() if v is not None},
                )
            )
            await session.commit()
            return True

        changed = False
        for attr in _UPDATABLE:
            value = fields.get(attr)
            if value is not None and getattr(user, attr) != value:
                setattr(user, attr, value)
                changed = True

        # 无显式 full_name 时，用 名+姓 兜底
        if not user.full_name and (user.first_name or user.last_name):
            user.full_name = " ".join(
                filter(None, [user.first_name, user.last_name])
            ).strip() or None
            changed = True

        user.last_seen = now
        await session.commit()
        return changed


async def get_user(user_id: int) -> User | None:
    async with session_scope() as session:
        return await session.get(User, user_id)


async def get_users_map(user_ids: set[int]) -> dict[int, User]:
    """批量取用户，返回 {user_id: User}。"""
    if not user_ids:
        return {}
    async with session_scope() as session:
        result = await session.execute(
            select(User).where(User.id.in_(user_ids))
        )
        return {u.id: u for u in result.scalars().all()}
