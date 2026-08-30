"""异步数据库引擎与会话。"""
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import DB_URL
from database.models import Base

engine = create_async_engine(
    DB_URL,
    pool_size=10,
    pool_recycle=3600,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


@asynccontextmanager
async def session_scope():
    """异步会话上下文管理器。"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """按模型建表（兜底）。正式建表请优先导入 schema.sql。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
