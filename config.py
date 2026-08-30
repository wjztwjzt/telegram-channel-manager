"""全局配置：从 .env 读取，供所有模块复用。"""
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ---- Telegram 用户账号（userbot，需为频道管理员）----
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
PHONE = os.getenv("PHONE", "")
SESSION_NAME = os.getenv("SESSION_NAME", "session")

# ---- 管理机器人（aiogram Bot）----
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# 允许使用管理机器人的用户 ID，逗号分隔
ADMIN_IDS = {
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
}

# ---- 待监控频道，逗号分隔（用户名或数字 ID，如 "@mychannel" 或 "-1001234567890"）----
CHANNELS = [c.strip() for c in os.getenv("CHANNELS", "").split(",") if c.strip()]

# ---- MySQL ----
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "telegram_channel_manager")

# 异步驱动（aiomysql），与 Telethon / aiogram 同属 asyncio 生态
DB_URL = (
    f"mysql+aiomysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

# ---- 采集频率（秒）----
MEMBER_MONITOR_INTERVAL = int(os.getenv("MEMBER_MONITOR_INTERVAL", "60"))
MEMBER_SYNC_INTERVAL = int(os.getenv("MEMBER_SYNC_INTERVAL", "3600"))
MESSAGE_STATS_INTERVAL = int(os.getenv("MESSAGE_STATS_INTERVAL", "3600"))
MESSAGE_STATS_LIMIT = int(os.getenv("MESSAGE_STATS_LIMIT", "50"))
DAILY_REPORT_HOUR = int(os.getenv("DAILY_REPORT_HOUR", "0"))
DAILY_REPORT_MINUTE = int(os.getenv("DAILY_REPORT_MINUTE", "5"))
