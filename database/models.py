"""SQLAlchemy 模型（与 schema.sql 对应，共 8 张表）。"""
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Channel(Base):
    """被监控的频道。"""

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="频道 ID")
    access_hash: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="访问哈希")
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="公开用户名")
    title: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="频道标题")
    participants_count: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="成员数")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class User(Base):
    """Telegram 用户资料。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="用户 ID")
    access_hash: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="访问哈希")
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="@用户名")
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="名")
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="姓")
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="昵称")
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="手机号")
    is_bot: Mapped[bool] = mapped_column(default=False, comment="是否机器人")
    is_premium: Mapped[bool] = mapped_column(default=False, comment="是否 Premium")
    language_code: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="语言")
    dc_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="数据中心")
    first_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="首次发现")
    last_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="最近发现")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class ChannelMember(Base):
    """频道与用户的成员关系。"""

    __tablename__ = "channel_members"

    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="频道 ID")
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="用户 ID")
    joined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="加入时间")
    left_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="退出时间")
    status: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="状态：member/left/kicked")
    inviter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="邀请人 ID")
    source: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="来源（邀请链接/入口）")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class MemberEvent(Base):
    """成员事件流水：JOIN / LEAVE / KICK / INVITE / JOIN_REQUEST。"""

    __tablename__ = "member_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="自增 ID")
    channel_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="频道 ID")
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="用户 ID")
    event_type: Mapped[str] = mapped_column(String(30), comment="事件类型")
    event_time: Mapped[datetime] = mapped_column(DateTime, comment="事件时间")
    inviter_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="邀请人 ID")
    invite_link: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="邀请链接")
    telegram_event_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True, unique=True, comment="Telegram 管理员日志事件 ID（去重）"
    )


class Message(Base):
    """频道消息最新快照。"""

    __tablename__ = "messages"

    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="频道 ID")
    message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="消息 ID")
    date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="发布时间")
    author_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="作者 ID")
    text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文本摘要")
    views: Mapped[int] = mapped_column(BigInteger, default=0, comment="浏览")
    forwards: Mapped[int] = mapped_column(BigInteger, default=0, comment="转发")
    reactions: Mapped[int] = mapped_column(BigInteger, default=0, comment="反应")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class MessageStat(Base):
    """消息统计时间序列（按采集时间保存曲线）。"""

    __tablename__ = "message_stats"

    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="频道 ID")
    message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="消息 ID")
    captured_at: Mapped[datetime] = mapped_column(DateTime, primary_key=True, comment="采集时间")
    views: Mapped[int] = mapped_column(BigInteger, default=0, comment="浏览")
    forwards: Mapped[int] = mapped_column(BigInteger, default=0, comment="转发")
    reactions: Mapped[int] = mapped_column(BigInteger, default=0, comment="反应")


class InviteLink(Base):
    """邀请链接清单。"""

    __tablename__ = "invite_links"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="自增 ID")
    channel_id: Mapped[int] = mapped_column(BigInteger, index=True, comment="频道 ID")
    link: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="邀请链接")
    name: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="链接备注/来源名")
    creator_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment="创建者 ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), comment="创建时间")


class DailyStat(Base):
    """频道日报快照（每日一行）。"""

    __tablename__ = "daily_stats"

    date: Mapped[date] = mapped_column(Date, primary_key=True, comment="日期")
    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="频道 ID")
    new_members: Mapped[int] = mapped_column(Integer, default=0, comment="新增")
    left_members: Mapped[int] = mapped_column(Integer, default=0, comment="退出")
    net_growth: Mapped[int] = mapped_column(Integer, default=0, comment="净增长")
    total_views: Mapped[int] = mapped_column(BigInteger, default=0, comment="总浏览")
    total_forwards: Mapped[int] = mapped_column(BigInteger, default=0, comment="总转发")
    total_reactions: Mapped[int] = mapped_column(BigInteger, default=0, comment="总反应")
    posts: Mapped[int] = mapped_column(Integer, default=0, comment="发文数")
