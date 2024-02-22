from aiogram import *
import sqlite3
from other_func import *
import os
import datetime
import json

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
            markup.add("Начать период")
            await bot.send_message(chat_id, f'Вы выбрили: {text}', reply_markup=markup)
        else:
            # TODO кнопка поддержки
            await bot.send_message(chat_id, 'Нет такого авто в списке, напиши в тех поддержку')
    # Начать поездку
    elif stage == 'go_per' and text == 'Начать период':
        # TODO сделать проверку на незакрытые периоды
        # TODO создать папку с водителем, если нет и добавить папку с периодом
        id_driver = get_id_driver(chat_id)
        id_truck = get_id_truck(chat_id)
        if str(id_driver) not in os.listdir('drive'):
            os.mkdir(f'drive/{id_driver}')
        time_now = datetime.datetime.now()
        os.mkdir(f'drive/{id_driver}/{time_now}')
        a = {"id_truck": id_truck}
        ex_update(f"UPDATE trucks SET status = 1 WHERE id = {id_truck}")
        ex_update(f"UPDATE users SET stage = 'from_where', time_start_period = '{time_now}' WHERE telegram_id = {chat_id}")
        with open(f'drive/{id_driver}/{time_now}/info.json', 'w') as file:
            json.dump(a, file)

        # TODO если заявка от логиста, то подсказка
        markup = types.ReplyKeyboardRemove()
        await bot.send_message(chat_id, "Выберите откуда - куда или напишите", reply_markup=markup)
    # Откуда - куда
    elif stage == 'from_where':
        # with open(f'drive/{id_driver}/{time_now}/info.json', 'r') as file:
        #     json.dump(a, file)
        ex_update(f"UPDATE users SET stage = 'type_drive', from_where = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Поездка с грузом')
        markup.add('Порожний перегон')
        markup.add("Заявка от логиста, пока не работает кнопка")
        await bot.send_message(chat_id, 'Выберите типо поездки', reply_markup=markup)
        # TODO Порожний перегон
    elif stage == 'type_drive' and text == 'Поездка с грузом':
        ex_update(f"UPDATE users SET stage = 'start_mileage', type_drive = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardRemove()
        await bot.send_message(chat_id, "Введите данные с одометра числом без пробелов", reply_markup=markup)
        # TODO Сделать проверка на ввод числа, если не так, то заново просить вписать
    elif stage == 'start_mileage':
        if text.isdigit():
            ex_update(f"UPDATE users SET stage = 'dot_start', start_mileage = {int(text)} WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Заявка от логиста, пока не работает кнопка")
            await bot.send_message(chat_id, 'Введите координаты (из яндекс карт)', reply_markup=markup)
        else:
            await bot.send_message(chat_id, "Вы ввели число некоректно, попробуйте ещё раз")
    elif stage == 'dot_start':
        ex_update(f"UPDATE users SET stage = 'dhv', dot_start = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Заявка от логиста, пока не работает кнопка")
        await bot.send_message(chat_id, "Введите Длинну Ширину Высоту через пробел (числа с разделением через точку) в милимметрах", reply_markup=markup)
    elif stage == 'dhv':
        ex_update(f"UPDATE users SET stage = 'weight', dhv = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Заявка от логиста, пока не работает кнопка")
        await bot.send_message(chat_id, "Введите вес в граммах", reply_markup=markup)
    elif stage == 'weight':
        ex_update(f"UPDATE users SET stage = 'photo_gruz', weight = '{text}' WHERE telegram_id = {chat_id}")
        # markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        # markup.add("Заявка от логиста, пока не работает кнопка")
        markup = types.ReplyKeyboardRemove()
        await bot.send_message(chat_id, "Отправьте одним альбомом 4 фотографии груза", reply_markup=markup)
    # TODO из фото обратно прыгнуть в текст

    
    # TODO сделать порожний перегон
    # Не знаю что ответить
    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')
    

@dp.message_handler(content_types='photo')
async def photo_handler(message):
    chat_id = message.chat.id
    stage = ex_get_stage(chat_id)
    count_photo_download = get_one_param_db('count_photo_download', chat_id)
    time_start_period = get_one_param_db('time_start_period', chat_id)
    id = get_one_param_db('id', chat_id)
    if stage == 'photo_gruz' and 0 <= count_photo_download <= 3:
        count_photo_download += 1
        ex_update(f"UPDATE users SET count_photo_download = count_photo_download + 1 WHERE telegram_id = {chat_id}")
        if 'photo_gruz' not in os.listdir(f'drive/{id}/{time_start_period}'):
            os.mkdir(f'drive/{id}/{time_start_period}/photo_gruz')
        await message.photo[-1].download(destination_file=f'drive/{id}/{time_start_period}/photo_gruz/{count_photo_download}.jpg')
        if count_photo_download == 4:
            ex_update(f"UPDATE users SET stage = 'end_photo_download' WHERE telegram_id = {chat_id}")
            await bot.send_message(chat_id, 'Фото успешно загружены, теперь отправьте документы - ТТН')

    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')


@dp.message_handler(content_types='document')
async def file_handler(message):
    chat_id = message.chat.id
    stage = ex_get_stage(chat_id)
    print(message)
    if stage == 'end_photo_download':
        # document = message.document
        # await bot.download(document)
        # file_id = message.document.file_id
        # file = await bot.get_file(file_id)
        # file_path = file.file_path
        # await bot.download_file(file_path, "text.txt")
        pass
    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')

    
executor.start_polling(dp, skip_updates=True)
