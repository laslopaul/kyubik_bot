"""
Module user_checker - checks if the Telegram user is permitted to use the bot
"""


from app.qb_instance import cfg
from aiogram import types


def user_checker(message: types.Message):
    tg_username = message.from_user.username
    if tg_username != cfg["TelegramUser"]:
        raise PermissionError(f"Access denied for @{tg_username}")
