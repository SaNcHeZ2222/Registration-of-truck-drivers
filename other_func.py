import sqlite3
from aiogram import *


def ex_update(zapros: str):
    connection = sqlite3.connect('my_database.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(zapros)

    connection.commit()
    connection.close()


def ex_get_stage(chat_id: int) -> str:
    connection = sqlite3.connect('my_database.db', timeout=5, check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT stage FROM users WHERE telegram_id = {chat_id}')
    stage = cursor.fetchall()[0][0]

    connection.commit()
    connection.close()

    return stage 



# def get_start_markup() -> types.ReplyKeyboardMarkup:
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     markup.add("Познакомимся?")
#     markup.add("Видео презентации")
#     markup.add("Денежные потоки")
#     markup.add("Мои соц сети")
#     markup.add("Написать мне")
#     return markup

