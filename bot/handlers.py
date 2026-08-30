"""命令与回调处理器。"""
from datetime import date

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import config
import registry
from bot import keyboards, render
from repo import messages as messages_repo
from repo import users as users_repo
from services import report

router = Router()


def _is_admin(user_id: int | None) -> bool:
    return user_id in config.ADMIN_IDS


def _cid(data: str) -> int:
    return int(data.split(":", 1)[1])


def _back(cid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ 返回", callback_data=f"menu:{cid}")]
        ]
    )


async def _safe_edit(message: Message, text: str, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest:
        pass


@router.message(CommandStart())
async def cmd_start(message: Message):
    if not _is_admin(message.from_user.id):
        return
    await message.answer("📊 频道管理", reply_markup=keyboards.channel_picker())


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    if not _is_admin(message.from_user.id):
        return
    await message.answer("📊 频道管理", reply_markup=keyboards.channel_picker())


@router.callback_query(F.data == "back")
async def cb_back(query: CallbackQuery):
    if not _is_admin(query.from_user.id):
        await query.answer("无权限")
        return
    await _safe_edit(query.message, "📊 频道管理", keyboards.channel_picker())
    await query.answer()


@router.callback_query(F.data.startswith("menu:"))
async def cb_menu(query: CallbackQuery):
    if not _is_admin(query.from_user.id):
        await query.answer("无权限")
        return
    cid = _cid(query.data)
    title = registry.channels.get(cid, str(cid))
    await _safe_edit(query.message, f"📊 {title} 管理", keyboards.channel_menu(cid, title))
    await query.answer()


@router.callback_query(F.data.startswith("today:"))
async def cb_today(query: CallbackQuery):
    if not _is_admin(query.from_user.id):
        await query.answer("无权限")
        return
    cid = _cid(query.data)
    title = registry.channels.get(cid, str(cid))
    data = await report.get_today_report(cid)
    await _safe_edit(query.message, render.render_today(data, title), _back(cid))
    await query.answer()


@router.callback_query(F.data.startswith("users:"))
async def cb_users(query: CallbackQuery):
    if not _is_admin(query.from_user.id):
        await query.answer("无权限")
        return
    cid = _cid(query.data)
    title = registry.channels.get(cid, str(cid))
    data = await report.get_today_report(cid)
    await _safe_edit(query.message, render.render_user_manage(data, title), _back(cid))
    await query.answer()


@router.callback_query(F.data.startswith("new:"))
async def cb_new(query: CallbackQuery):
    if not _is_admin(query.from_user.id):
        await query.answer("无权限")
        return
    cid = _cid(query.data)
    title = registry.channels.get(cid, str(cid))
    events = await report.get_recent_events(cid, report.JOIN_TYPES, date.today())
    ids = {e.user_id for e in events} | {e.inviter_id for e in events if e.inviter_id}
    users_map = await users_repo.get_users_map(ids)
    await _safe_edit(
        query.message, render.render_member_events(events, users_map, "➕ 新增用户", title), _back(cid)
    )
    await query.answer()


@router.callback_query(F.data.startswith("left:"))
async def cb_left(query: CallbackQuery):
    if not _is_admin(query.from_user.id):
        await query.answer("无权限")
        return
    cid = _cid(query.data)
    title = registry.channels.get(cid, str(cid))
    events = await report.get_recent_events(cid, report.LEAVE_TYPES, date.today())
    ids = {e.user_id for e in events} | {e.inviter_id for e in events if e.inviter_id}
    users_map = await users_repo.get_users_map(ids)
    await _safe_edit(
        query.message, render.render_member_events(events, users_map, "➖ 退出用户", title), _back(cid)
    )
    await query.answer()


@router.callback_query(F.data.startswith("posts:"))
async def cb_posts(query: CallbackQuery):
    if not _is_admin(query.from_user.id):
        await query.answer("无权限")
        return
    cid = _cid(query.data)
    title = registry.channels.get(cid, str(cid))
    messages = await messages_repo.get_top_messages(cid, 10)
    await _safe_edit(query.message, render.render_posts(messages, title), _back(cid))
    await query.answer()


@router.callback_query(F.data.startswith("sources:"))
async def cb_sources(query: CallbackQuery):
    if not _is_admin(query.from_user.id):
        await query.answer("无权限")
        return
    cid = _cid(query.data)
    title = registry.channels.get(cid, str(cid))
    sources = await report.get_source_breakdown(cid, date.today())
    await _safe_edit(query.message, render.render_sources(sources, title), _back(cid))
    await query.answer()


@router.callback_query(F.data.startswith("report7:"))
async def cb_report7(query: CallbackQuery):
    await _cb_period(query, 7)


@router.callback_query(F.data.startswith("report30:"))
async def cb_report30(query: CallbackQuery):
    await _cb_period(query, 30)


async def _cb_period(query: CallbackQuery, days: int):
    if not _is_admin(query.from_user.id):
        await query.answer("无权限")
        return
    cid = _cid(query.data)
    title = registry.channels.get(cid, str(cid))
    rows = await report.get_period_report(cid, days)
    await _safe_edit(query.message, render.render_period(rows, days, title), _back(cid))
    await query.answer()
