# Telegram 频道数据统计与人员管理机器人

基于 **Telethon（MTProto）+ aiogram 3 + MySQL** 的频道运营数据统计机器人，实现成员
监控、用户资料同步、文章级统计、邀请来源追踪与日报，并提供 Telegram Bot 管理界面。

## 功能

- **用户数据库**：同步 Telegram 用户资料（首次 INSERT，资料变化才 UPDATE）。
- **加入 / 退出监控**：轮询频道管理员日志，抓取 `JOIN / LEAVE / KICK / INVITE` 事件。
- **邀请来源追踪**：记录用户加入所经邀请链接，日报按来源（广告A/广告B/官网…）分组。
- **文章级统计**：定时抓取消息的 `views / forwards / reactions`，保存时间序列曲线。
- **日报 / 周期报表**：每日凌晨生成 `daily_stats`，支持今日 / 7 日 / 30 日报表。
- **Bot 管理界面**：内联键盘菜单，一键查看数据，无需 Web 后台。

## 架构

```
Telegram (MTProto)
   │
   ▼
Telethon 用户客户端 (userbot)          aiogram Bot
   ├─ 用户资料同步                        └─ 管理员命令/内联键盘
   ├─ 成员事件监控
   ├─ 全量成员 diff
   ├─ 邀请链接追踪
   └─ 消息统计
             │                              │
             └──────────┬───────────────────┘
                        ▼
              MySQL (SQLAlchemy + aiomysql)
                        ▲
                        │
              APScheduler 定时任务
```

## 环境要求

- Python 3.12+
- MySQL 8.0+（或 26.x）
- 一个 **Telegram 用户账号**（需设为被监控频道的**管理员**）
- 一个 **Telegram Bot**（在 [@BotFather](https://t.me/BotFather) 创建）

## 安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 创建数据库与表
mysql -u root -p < schema.sql

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API_ID / API_HASH / BOT_TOKEN / 频道 / MySQL 等

# 4. 启动
python main.py
```

首次运行会交互式要求输入手机号与验证码，登录成功后生成 `session` 文件（已加入
`.gitignore`，不会提交）。

## 配置说明（.env）

| 变量 | 说明 |
| --- | --- |
| `API_ID` / `API_HASH` | 在 https://my.telegram.org 申请 |
| `PHONE` | 用户账号手机号（首次登录用） |
| `SESSION_NAME` | 登录态文件名，默认 `session` |
| `BOT_TOKEN` | 管理机器人 Token（@BotFather） |
| `ADMIN_IDS` | 允许使用机器人的管理员用户 ID，逗号分隔 |
| `CHANNELS` | 被监控频道，逗号分隔（`@username` 或 `-100xxx`） |
| `MYSQL_*` | 数据库连接信息 |
| `MEMBER_MONITOR_INTERVAL` | 成员事件轮询间隔（秒，默认 60） |
| `MEMBER_SYNC_INTERVAL` | 全量成员同步间隔（秒，默认 3600） |
| `MESSAGE_STATS_INTERVAL` | 消息统计采集间隔（秒，默认 3600） |
| `DAILY_REPORT_HOUR/MINUTE` | 每日日报生成时间（默认 00:05） |

## 数据库表

| 表 | 用途 |
| --- | --- |
| `channels` | 被监控频道 |
| `users` | 用户资料 |
| `channel_members` | 频道成员关系 |
| `member_events` | 成员事件流水（JOIN/LEAVE/KICK/INVITE） |
| `messages` | 消息最新快照 |
| `message_stats` | 消息统计时间序列 |
| `invite_links` | 邀请链接清单 |
| `daily_stats` | 频道日报快照 |

## 使用

对机器人发送 `/start` 或 `/menu`，选择频道后即可查看：

- 📈 今日数据
- 👥 用户管理 / ➕ 新增用户 / ➖ 退出用户
- 📝 文章统计（按浏览 Top10）
- 🔗 邀请来源
- 📊 7 日报表 / 30 日报表

## 注意事项

- 监控账号必须是频道**管理员**，否则读不到管理员日志，无法追踪邀请来源。
- 文章级浏览数只能拿到 **总量与增量**，无法做到「某用户看了某文章 N 秒」这种逐用户
  行为日志（Telegram API 不提供）。
- 「活跃 / 沉默」分层只能基于可观测事件近似，请勿把「未见某条消息」误判为「不活跃」。
- 请遵守 Telegram 服务条款，勿滥用本工具进行批量采集或骚扰。
