"""Contains message handlers for common commands"""


from aiogram import Dispatcher, types
from app.qb_instance import qb
from app.user_checker import user_checker
import app.replies as repl


async def start(message: types.Message):
    try:
        user_checker(message)
    except PermissionError as err:
        await message.answer(err)
    else:
        await message.answer(f"Welcome, {message.from_user.first_name}!")


async def torrent_info(message: types.Message):
    try:
        user_checker(message)
        torrent_name = message.get_args()
        data = qb.torrent_info(torrent_name)
    except (ValueError, PermissionError) as err:
        await message.answer(err)
    else:
        await message.answer(repl.info.format(*data))


async def list_group(message: types.Message):
    try:
        user_checker(message)
        group = message.get_args()
        for entry in qb.list_group(group):
            await message.answer(entry)
    except (ValueError, PermissionError) as err:
        await message.answer(err)
    else:
        count = sum(1 for _ in qb.list_group(group))
        total = sum(1 for _ in qb.list_group("all"))
        await message.answer(f"{group}: {count} of {total} torrents")


async def torrent_contents(message: types.Message):
    try:
        user_checker(message)
        torrent_name = message.get_args()
        for file in qb.torrent_contents(torrent_name):
            await message.answer(repl.contents.format(*file))
    except (ValueError, PermissionError) as err:
        await message.answer(err)
    else:
        count = sum(1 for _ in qb.torrent_contents(torrent_name))
        await message.answer(f"Total: {count} files")


async def traffic_stats(message: types.Message):
    try:
        user_checker(message)
    except PermissionError as err:
        await message.answer(err)
    else:
        data = qb.traffic_stats()
        await message.answer(repl.stats.format(*data))


async def pause_resume(message: types.Message):
    try:
        user_checker(message)
        full_cmd = message.get_full_command()
        # Action for one torrent
        if len(full_cmd) > 1:
            result = qb.pause_resume(
                torrent_name=full_cmd[1], action=full_cmd[0][1:]
            )
        # Action for all torrents (no torrent name was passed as argument)
        else:
            result = qb.pause_resume(action=full_cmd[0][1:])

    except (ValueError, PermissionError) as err:
        await message.answer(err)
    else:
        await message.answer(result)


def register_handlers_common(dp: Dispatcher):
    dp.register_message_handler(start, commands="start", state="*")
    dp.register_message_handler(torrent_info, commands="info", state="*")
    dp.register_message_handler(list_group, commands="list", state="*")
    dp.register_message_handler(torrent_contents, commands="files", state="*")
    dp.register_message_handler(traffic_stats, commands="stats", state="*")
    dp.register_message_handler(
        pause_resume, commands=["pause", "resume"], state="*"
    )
