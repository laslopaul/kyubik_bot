"""Contains message handlers for adding torrents"""


from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.qb_instance import qb
from app.user_checker import user_checker


class AddTorrent(StatesGroup):
    save_torrent_url = State()
    waiting_for_seq_dl = State()
    exec_final_cmd = State()


# Regular expression for catching valid download links
re_links = r"(^http(s?)://\w+\.torrent)|(^magnet:)|(^bc://bt/(\d[A-F][a-f])+)"


async def catch_link(message: types.Message, state: FSMContext):
    """Catch valid torrent link in a message and enter save path"""
    try:
        user_checker(message)
    except PermissionError as err:
        await message.answer(err)
    else:
        await AddTorrent.save_torrent_url.set()
        await state.update_data(url=message.text)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("Default")
        await message.answer(
            "Enter save path or press 'Default' button:", reply_markup=keyboard
        )
        await AddTorrent.waiting_for_seq_dl.set()


async def enable_seq_dl(message: types.Message, state: FSMContext):
    """Ask to enable sequential download"""
    await state.update_data(path=message.text)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    answers = ["Yes", "No"]
    keyboard.add(*answers)
    await message.answer(
        "Do you want to enable sequential download?", reply_markup=keyboard
    )
    await AddTorrent.next()


async def final_cmd(message: types.Message, state: FSMContext):
    """Exeecutes command for torrent adding"""
    # Flag for sequential download
    flag = False
    if message.text.capitalize() not in ["Yes", "No"]:
        await message.answer("Please try again:")
        return
    if message.text.capitalize() == "Yes":
        flag = True

    torrent = await state.get_data()
    if torrent["path"] != "Default":
        result = qb.add_torrent(torrent["url"], torrent["path"], seq_dl=flag)
    else:
        result = qb.add_torrent(torrent["url"], seq_dl=flag)
    await message.answer(result)
    await state.finish()


def register_handlers_add(dp: Dispatcher):
    dp.register_message_handler(catch_link, regexp=re_links, state="*")
    dp.register_message_handler(
        enable_seq_dl, state=AddTorrent.waiting_for_seq_dl
    )
    dp.register_message_handler(final_cmd, state=AddTorrent.exec_final_cmd)
