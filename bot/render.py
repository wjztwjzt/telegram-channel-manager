"""报表文案排版。"""
from database import DailyStat, MemberEvent, Message, User
from utils import fmt_dt, fmt_num

LINE = "━━━━━━━━━━━━"


def _display_name(user: User | None, user_id: int | None = None) -> str:
    if user and user.username:
        return f"@{user.username}"
    if user and user.full_name:
        return user.full_name
    return f"ID {user_id}"


def render_today(data: dict, title: str) -> str:
    lines = [
        f"📊 频道日报 — {title}",
        LINE,
        "",
        "👥 成员",
        f"当前：{fmt_num(data['current'])}",
        f"新增：{fmt_num(data['new'])}",
        f"退出：{fmt_num(data['left'])}",
        f"净增：{data['net']:+d}",
        "",
        "👀 内容",
        f"文章：{fmt_num(data['posts'])}",
        f"浏览：{fmt_num(data['views'])}",
        f"转发：{fmt_num(data['forwards'])}",
        f"Reaction：{fmt_num(data['reactions'])}",
    ]
    if data.get("sources"):
        lines += ["", "🔗 来源"]
        lines += [f"{name}：{fmt_num(cnt)}" for name, cnt in data["sources"]]
    lines += [LINE, f"统计日期：{data['date']}"]
    return "\n".join(lines)


def render_sources(sources: list[tuple[str, int]], title: str) -> str:
    if not sources:
        return f"🔗 邀请来源 — {title}\n{LINE}\n暂无数据"
    lines = [f"🔗 邀请来源 — {title}", LINE, ""]
    for name, cnt in sources:
        lines.append(f"{name}：{fmt_num(cnt)}")
    return "\n".join(lines)


def render_member_events(
    events: list[MemberEvent],
    users_map: dict[int, User],
    label: str,
    title: str,
) -> str:
    if not events:
        return f"{label} — {title}\n{LINE}\n暂无数据"
    lines = [f"{label} — {title}", LINE, ""]
    for i, ev in enumerate(events, 1):
        user = users_map.get(ev.user_id)
        inviter = users_map.get(ev.inviter_id) if ev.inviter_id else None
        lines.append(f"{i}. {_display_name(user, ev.user_id)}")
        lines.append(f"   ID: {ev.user_id}")
        lines.append(f"   时间: {fmt_dt(ev.event_time)}")
        if inviter:
            lines.append(f"   邀请人: {_display_name(inviter, ev.inviter_id)}")
        if ev.invite_link:
            lines.append(f"   来源: {ev.invite_link}")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_posts(messages: list[Message], title: str) -> str:
    if not messages:
        return f"📝 文章统计 — {title}\n{LINE}\n暂无数据"
    lines = [f"📝 文章统计 Top{len(messages)} — {title}", LINE, ""]
    for i, m in enumerate(messages, 1):
        preview = (m.text or "")[:40].replace("\n", " ")
        lines.append(f"{i}. #{m.message_id}  {fmt_num(m.views)} 浏览")
        lines.append(f"   👍{fmt_num(m.reactions)}  🔁{fmt_num(m.forwards)}")
        if preview:
            lines.append(f"   {preview}")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_period(rows: list[DailyStat], days: int, title: str) -> str:
    lines = [f"📊 {days}日报表 — {title}", LINE, ""]
    if not rows:
        lines.append("暂无数据（请等待日报定时任务生成）")
        return "\n".join(lines)

    total_new = total_left = total_views = 0
    for r in rows:
        total_new += r.new_members or 0
        total_left += r.left_members or 0
        total_views += r.total_views or 0
        lines.append(
            f"{r.date}  ➕{fmt_num(r.new_members)} ➖{fmt_num(r.left_members)} "
            f"📈{r.net_growth:+d}"
        )
    lines += [
        "",
        f"累计新增：{fmt_num(total_new)}",
        f"累计退出：{fmt_num(total_left)}",
        f"累计浏览：{fmt_num(total_views)}",
    ]
    return "\n".join(lines)


def render_user_manage(data: dict, title: str) -> str:
    return "\n".join(
        [
            f"👥 用户管理 — {title}",
            LINE,
            "",
            f"当前成员：{fmt_num(data['current'])}",
            f"今日新增：{fmt_num(data['new'])}",
            f"今日退出：{fmt_num(data['left'])}",
        ]
    )
