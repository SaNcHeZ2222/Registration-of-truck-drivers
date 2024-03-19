import sqlite3
from aiogram import *
import json


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

    cursor.execute(f'SELECT id, name_auto, color, number, status FROM trucks')
    trucks = cursor.fetchall()

    connection.commit()
    connection.close()

    return trucks


def ex_get_trailer_list():
    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT id, number_trailer FROM trailer')
    trucks = cursor.fetchall()

    connection.commit()
    connection.close()

    return trucks


def ex_get_active_drive():
    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT id, fio FROM users WHERE active = 1')
    trucks = cursor.fetchall()

    connection.commit()
    connection.close()

    return trucks 


def get_main_menu_markup() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Выбрать авто")
    return markup


def get_id_driver(chat_id):
    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT id FROM users WHERE telegram_id = {chat_id}')
    id = cursor.fetchall()[0][0]

    connection.commit()
    connection.close()

    return id 

def get_id_truck(chat_id) -> int:
    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT id_truck FROM users WHERE telegram_id = {chat_id}')
    id = cursor.fetchall()[0][0]

    connection.commit()
    connection.close()

    return id 

def get_one_param_db(param, chat_id):
    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT {param} FROM users WHERE telegram_id = {chat_id}')
    param = cursor.fetchall()[0][0]

    connection.commit()
    connection.close()

    return param 

def get_one_param_truks(param, id_truck):
    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT {param} FROM trucks WHERE id = {id_truck}')
    param = cursor.fetchall()[0][0]

    connection.commit()
    connection.close()

    return param 


def get_one_param_trailer(param, id_trailer):
    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT {param} FROM trailer WHERE id = {id_trailer}')
    param = cursor.fetchall()[0][0]

    connection.commit()
    connection.close()

    return param

def read_json_file(id_driver, time_start_period, current_dir) -> dict:
    with open(f'drive/{id_driver}/{time_start_period}/{current_dir}/info.json', "r") as f:
        data = json.load(f)
        f.close()
        return data
    
def write_json_file(id_driver, time_start_period, current_dir, data) -> None:
    with open(f'drive/{id_driver}/{time_start_period}/{current_dir}/info.json', "w") as f:
        json.dump(data, f)
        f.close()


def read_order() -> dict:
    with open(f'order.json', "r") as f:
        data = json.load(f)
        f.close()
        return data
    
def write_order(data) -> None:
    with open(f'order.json', "w") as f:
        json.dump(data, f)
        f.close()


def get_all_obj(chat_id):
    connection = sqlite3.connect(f'base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(
        f'SELECT id, telegram_id, stage, fio, phone, id_truck, id_trailer, from_where, time_start_period, current_dir, type_drive, start_mileage, dot_start, d, s, v, weight, count_photo_download, dot_end, end_mileage, empty_race, active, name_gruz, total_lenght, total_height FROM users WHERE telegram_id = {chat_id}')
    a = cursor.fetchall()[0]

    connection.commit()
    connection.close()

    keys = ['id', 'telegram_id', 'stage', 'fio', 'phone', 'id_truck', 'id_trailer', 'from_where', 'time_start_period',
            'current_dir', 'type_drive', 'start_mileage', 'dot_start', 'd', 's', 'v', 'weight', 'count_photo_download',
            'dot_end', 'end_mileage', 'empty_race', 'active', 'name_gruz', 'total_lenght', 'total_height']

    # Создание словаря из списков
    result_dict = dict(zip(keys, a))

    return result_dict


def get_number_and_price_trailer(id):
    connection = sqlite3.connect(f'base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT number_trailer, price_1_km FROM trailer WHERE id = {id}')
    a = cursor.fetchall()[0]

    connection.commit()
    connection.close()

    return a


def get_number_name_color_truck(id):
    connection = sqlite3.connect(f'base.db', check_same_thread=True)
    cursor = connection.cursor()

    cursor.execute(f'SELECT name_auto, number, color FROM trucks WHERE id = {id}')
    a = cursor.fetchall()[0]

    connection.commit()
    connection.close()

    return a