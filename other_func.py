import sqlite3
from aiogram import *


def ex_update(zapros: str):
    connection = sqlite3.connect(f'base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(zapros)

    connection.commit()
    connection.close()


def ex_get_stage(chat_id: int) -> str:
    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT stage FROM users WHERE telegram_id = {chat_id}')
    stage = cursor.fetchall()[0][0]

    connection.commit()
    connection.close()

    return stage 

def ex_get_trucks_list():
    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT id, name_auto, number, status FROM trucks')
    trucks = cursor.fetchall()

    connection.commit()
    connection.close()

    return trucks 

def get_main_menu_markup() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Выбрать авто")
    return markup


def get_id_driver(chat_id) -> int:
    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT id FROM users WHERE telegram_id = {chat_id}')
    id = cursor.fetchall()[0][0]

    connection.commit()
    connection.close()

    return id 