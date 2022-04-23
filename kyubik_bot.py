#!venv/bin/python
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from app.qb_instance import cfg
from app.handlers.common import register_handlers_common
from app.handlers.delete_torrent import register_handlers_delete


logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=cfg["Token"])
    dp = Dispatcher(bot, storage=MemoryStorage())

    register_handlers_common(dp)
    register_handlers_delete(dp)

    await dp.skip_updates()
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
