"""aiogram Bot 与 Dispatcher 组装。"""
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
from bot.handlers import router

dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)


async def start_bot():
    """启动轮询（阻塞直至进程结束）。"""
    bot = Bot(token=config.BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
