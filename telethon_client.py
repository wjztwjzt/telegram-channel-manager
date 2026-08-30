"""Telethon 用户客户端（userbot）连接与频道解析。"""
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat

import config
from utils import get_logger

logger = get_logger("telethon")

_client: TelegramClient | None = None


def get_client() -> TelegramClient:
    """惰性构造并复用 TelegramClient（避免导入期校验密钥）。"""
    global _client
    if _client is None:
        _client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)
    return _client


async def start_client() -> TelegramClient:
    """启动并登录用户账号。首次运行会交互式要求手机号/验证码。"""
    client = get_client()
    await client.start(phone=config.PHONE or None)
    me = await client.get_me()
    logger.info("Telethon 已登录：%s (id=%s)", getattr(me, "first_name", ""), me.id)
    return client


async def resolve_channel(ref: str):
    """把用户名/ID 解析为频道实体；返回 (channel_id, entity)。"""
    client = get_client()
    if ref.startswith("-100") or (ref.lstrip("-").isdigit() and ref.startswith("-")):
        channel_id = int(ref)
        entity = await client.get_entity(channel_id)
    else:
        entity = await client.get_entity(ref)
        channel_id = entity.id
    if not isinstance(entity, (Channel, Chat)):
        raise ValueError(f"{ref} 不是频道/群组")
    return channel_id, entity


async def resolve_all_channels() -> list[tuple[int, object]]:
    """解析配置里所有待监控频道。"""
    result = []
    for ref in config.CHANNELS:
        try:
            channel_id, entity = await resolve_channel(ref)
            result.append((channel_id, entity))
            logger.info("已解析频道：%s -> %s", ref, getattr(entity, "title", channel_id))
        except Exception as exc:  # noqa: BLE001
            logger.error("解析频道 %s 失败：%s", ref, exc)
    return result
