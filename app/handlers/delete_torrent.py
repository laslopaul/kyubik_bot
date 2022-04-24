"""Contains message handlers for deleting torrents"""


from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from app.qb_instance import qb
from app.user_checker import user_checker


# FSM state class for /del command
class DeleteTorrent(StatesGroup):
    waiting_for_torrent_name = State()
    waiting_for_confirmation = State()
    waiting_to_delete_files = State()


async def enter_torrent_name(message: types.Message):
    try:
        user_checker(message)
    except PermissionError as err:
        await message.answer(err)
    else:
        await message.answer("Enter a torrent name:")
        await DeleteTorrent.waiting_for_torrent_name.set()


async def ask_about_torrent(message: types.Message, state: FSMContext):
    """Function called to confirm removal of a selected torrent"""
    try:
        torrent = qb.torrent_info(message.text)[0]
    except ValueError as err:
        await message.answer(err)
        await state.finish()
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        answers = ["Yes", "No"]
        keyboard.add(*answers)
        message = await message.answer(
            f"Are you sure you want to delete {torrent}?",
            reply_markup=keyboard,
        )

        await state.update_data(name=torrent)
        await DeleteTorrent.next()


async def ask_about_files(message: types.Message, state: FSMContext):
    """
    Function that is called to confirm removal of downloaded torrent files
    """
    if message.text.capitalize() not in ["Yes", "No"]:
        await message.answer("Please try again:")
        return

    if message.text.capitalize() == "Yes":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        answers = ["Yes", "No"]
        keyboard.add(*answers)

        await message.answer(
            "Do you want to delete downloaded files?",
            reply_markup=keyboard,
        )

        await DeleteTorrent.next()

    elif message.text.capitalize() == "No":
        await state.finish()


async def final_cmd(message: types.Message, state: FSMContext):
    """
    Exeecutes command for torrent deletion
    """
    flag = False
    if message.text.capitalize() not in ["Yes", "No"]:
        await message.answer("Please try again:")
        return
    if message.text.capitalize() == "Yes":
        flag = True

    torrent = await state.get_data()
    result = qb.delete_torrent(torrent["name"], flag)
    await message.answer(result)


def register_handlers_delete(dp: Dispatcher):
    dp.register_message_handler(enter_torrent_name, commands="del", state="*")
    dp.register_message_handler(
        ask_about_torrent, state=DeleteTorrent.waiting_for_torrent_name
    )
    dp.register_message_handler(
        ask_about_files, state=DeleteTorrent.waiting_for_confirmation
    )
    dp.register_message_handler(
        final_cmd, state=DeleteTorrent.waiting_to_delete_files
    )
