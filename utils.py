"""通用工具：日志、数字/时间格式化。"""
import logging
from datetime import datetime, timedelta


def get_logger(name: str = "channel-manager") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def fmt_num(n) -> str:
    """1234567 -> '1,234,567'"""
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return "0"


def fmt_dt(dt: datetime | None) -> str:
    if not dt:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def today() -> datetime.date:
    return datetime.now().date()


def days_ago(n: int) -> datetime.date:
    return datetime.now().date() - timedelta(days=n)
