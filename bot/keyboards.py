"""内联键盘。"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import registry


def _btn(text: str, callback: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback)


def channel_picker() -> InlineKeyboardMarkup:
    """主菜单：选择频道。"""
    rows = [
        [_btn(f"📈 {title}", f"menu:{cid}")]
        for cid, title in registry.channels.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channel_menu(cid: int, title: str) -> InlineKeyboardMarkup:
    """某频道的统计菜单。"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_btn("📈 今日数据", f"today:{cid}")],
            [
                _btn("👥 用户管理", f"users:{cid}"),
                _btn("➕ 新增用户", f"new:{cid}"),
            ],
            [
                _btn("➖ 退出用户", f"left:{cid}"),
                _btn("📝 文章统计", f"posts:{cid}"),
            ],
            [
                _btn("🔗 邀请来源", f"sources:{cid}"),
                _btn("📊 7日报表", f"report7:{cid}"),
            ],
            [
                _btn("📊 30日报表", f"report30:{cid}"),
            ],
            [_btn("⬅️ 返回频道列表", "back")],
        ]
    )
