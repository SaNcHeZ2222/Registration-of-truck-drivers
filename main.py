from aiogram import *
import sqlite3
from other_func import *
import os

token = '7060673771:AAFQHaSSdi0Hl4BB2va9Zqln12XASKj67TE'
# trucks_delivery_bot

bot = Bot(token)
dp = Dispatcher(bot)

admin = [703194398]


@dp.message_handler(commands='start')
async def start_message(message: types.Message):
    chat_id = message.chat.id

    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    all_id_drivers = {i[0] for i in cursor.execute('SELECT telegram_id FROM users')}

    connection.commit()
    connection.close()
    # TODO Сделать проверку на start, чтобы при нажатии ничего не сбрасывалось

    if chat_id not in all_id_drivers:
        connection = sqlite3.connect('base.db', check_same_thread=True)
        cursor = connection.cursor()

        cursor.execute(f"INSERT INTO users(telegram_id, stage) VALUES ({chat_id}, 'start_registration')")

        connection.commit()
        connection.close()
        markup = types.ReplyKeyboardRemove()
        await bot.send_message(chat_id, 'Напиши ваше ФИО', reply_markup=markup)
    else:
        stage = ex_get_stage(chat_id)
        # TODO если не противоречит 
        # Если зарегался 
        ex_update(f'UPDATE users SET stage = "main" WHERE telegram_id = {chat_id}')
        if stage:
            markup = get_main_menu_markup()
            await bot.send_message(chat_id, 'Вы в главном меню', reply_markup=markup)
        else:
            await bot.send_message(chat_id, 'Вы не можете выйти в меню, тк везёте груз')
        # TODO Главное меню


@dp.message_handler(content_types='text')
async def text_handler(message: types.Message):
    chat_id = message.chat.id
    stage = ex_get_stage(chat_id)
    text = message.text
    # TODO сделать проверку, что можешь что-то сделать | phone != NULL
    # if chat_id: 
    #     return
    # Регистрация
    if stage == 'start_registration': # Запрос фамилии
        ex_update(f'UPDATE users SET stage = "phone_number", fio = "{text}" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, "Напишите ваш номер телефона")
    elif stage == 'phone_number':
        ex_update(f'UPDATE users SET stage = "end_registration", phone = "{text}" WHERE telegram_id = {chat_id}')
        markup = get_main_menu_markup()
        await bot.send_message(chat_id, "Спасибо, регистрацию завершена", reply_markup=markup)
    # Главное меню и выбор авто
    elif (stage == 'end_registration' or stage == 'main') and text == 'Выбрать авто':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        trucks = ex_get_trucks_list()
        for i in trucks:
            if i[3] == 0:
                markup.add(f'{i[0]} {i[1]} {i[2]}')
        ex_update(f"UPDATE users SET stage = 'avto' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, "Выберите авто из списка", reply_markup=markup)
    elif stage == 'avto':
        if text in {f'{i[0]} {i[1]} {i[2]}' for i in ex_get_trucks_list() if i[3] == 0}:
            id_truck = int(text.split()[0])
            ex_update(f"UPDATE users SET stage = 'go_per', id_truck = {id_truck} WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Начать перевозку")
            await bot.send_message(chat_id, f'Вы выбрили: {text}')
        else:
            # TODO кнопка поддержки
            await bot.send_message(chat_id, 'Нет такого авто в списке, напиши в тех поддержку')
    # Начать поездку
    elif stage == 'go_per' and text == 'Начать перевозку':
        # TODO создать папку с водителем, если нет и добавить папку с периодом
        id_driver = get_id_driver(chat_id)
        if id_driver not in os.listdir('drive'):
            os.mkdir(f'drive/{id_driver}')
    # Не знаю что ответить
    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')
    

    
    
executor.start_polling(dp, skip_updates=True)
