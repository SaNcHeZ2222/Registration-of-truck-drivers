from aiogram import *
import sqlite3
from other_func import *
from config import token
import os
import datetime
import json

token = token
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
    elif ((stage == 'end_registration' or stage == 'main') and text == 'Выбрать авто') or (stage == 'new_period' and text == 'Начать период'):
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
    elif (stage == 'go_per' and text == 'Начать период') or (text == 'Начать перевозку' and stage == 'end_poezdka'):
        # TODO сделать проверку на незакрытые периоды
        # TODO сделать открытие трака после закрытия периода
        time_start_period = get_one_param_db('time_start_period', chat_id)
        if time_start_period == None:
            id_truck = get_id_truck(chat_id)
            time_now = datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S")
            ex_update(f"UPDATE trucks SET status = 1 WHERE id = {id_truck}")
            ex_update(f"UPDATE users SET stage = 'from_where', time_start_period = '{time_now}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'from_where' WHERE telegram_id = {chat_id}")

        # TODO если заявка от логиста, то подсказка
        markup = types.ReplyKeyboardRemove()
        await bot.send_message(chat_id, "Выберите откуда - куда или напишите", reply_markup=markup)
    # Откуда - куда
    elif stage == 'from_where':
        id_driver = get_id_driver(chat_id)
        id_truck = get_id_driver(chat_id)
        # TODO сделать проверка на одинаковые имена на всякий случай)
        time_now = get_one_param_db('time_start_period', chat_id)
        current_dir = f'{text} {datetime.datetime.now().strftime(r"%d.%m.%y")}'
        if str(id_driver) not in os.listdir('drive'):
            os.mkdir(f'drive/{id_driver}')
        if time_now not in os.listdir(f'drive/{id_driver}'):
            os.mkdir(f'drive/{id_driver}/{time_now}')
        os.mkdir(f'drive/{id_driver}/{time_now}/{current_dir}')

        a = {"id_truck": id_truck} 
    
        with open(f'drive/{id_driver}/{time_now}/{current_dir}/info.json', 'w') as file:
            json.dump(a, file)

        ex_update(f"UPDATE users SET stage = 'type_drive', from_where = '{text}', current_dir = '{current_dir}', count_photo_download = 0 WHERE telegram_id = {chat_id}")
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
        # TODO сделать порожний перегон
    elif stage == 'start_mileage':
        if text.isdigit():
            ex_update(f"UPDATE users SET stage = 'dot_start', start_mileage = {int(text)} WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Заявка от логиста, пока не работает кнопка")
            await bot.send_message(chat_id, 'Введите координаты (из яндекс карт)', reply_markup=markup)
        else:
            await bot.send_message(chat_id, "Вы ввели число некоректно, попробуйте ещё раз")
    elif stage == 'dot_start':
        ex_update(f"UPDATE users SET stage = 'd', dot_start = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Заявка от логиста, пока не работает кнопка")
        await bot.send_message(chat_id, "Введите <b>длину</b> в метрах и сантиметры через точку, например 11 метров 25 см будет 11.25", reply_markup=markup, parse_mode='html')
    elif stage == 'd':
        ex_update(f"UPDATE users SET stage = 's', d = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Заявка от логиста, пока не работает кнопка")
        await bot.send_message(chat_id, "Введите <b>ширину</b> в метрах и сантиметры через точку, например 11 метров 25 см будет 11.25", reply_markup=markup, parse_mode='html')
    elif stage == 's':
        ex_update(f"UPDATE users SET stage = 'v', s = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Заявка от логиста, пока не работает кнопка")
        await bot.send_message(chat_id, "Введите <b>высоту</b> в метрах и сантиметры через точку, например 11 метров 25 см будет 11.25", reply_markup=markup, parse_mode='html')
    elif stage == 'v':
        ex_update(f"UPDATE users SET stage = 'weight', v = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Заявка от логиста, пока не работает кнопка")
        await bot.send_message(chat_id, "Введите вес в граммах", reply_markup=markup)
    elif stage == 'weight':
        ex_update(f"UPDATE users SET stage = 'photo_gruz', weight = '{text}' WHERE telegram_id = {chat_id}")
        # markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        # markup.add("Заявка от логиста, пока не работает кнопка")
        markup = types.ReplyKeyboardRemove()
        await bot.send_message(chat_id, "Отправьте одним альбомом 4 фотографии груза", reply_markup=markup)
    # TODO сделать порожний перегон
    elif stage == 'gruz_end' and text == 'Старт поездки':
        time_start_transit = datetime.datetime.now()
        id_driver = get_id_driver(chat_id)
        current_dir = get_one_param_db('current_dir', chat_id)
        time_start_period = get_one_param_db('time_start_period', chat_id)

        data = read_json_file(id_driver, time_start_period, current_dir)
        data['time_start_transit'] = str(time_start_transit)
        write_json_file(id_driver, time_start_period, current_dir, data)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Доп расходы')
        markup.add('Доп условия')
        markup.add('Форс-мажоры')
        markup.add('ПРИБЫЛ НА МЕСТО РАЗГРУЗКИ')
        ex_update(f"UPDATE users SET stage = 'in_transit' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, 'Добавляйте условия и тд, пока не приедете на место разгрузки', reply_markup=markup)
    # Доп расходы
    elif stage == 'in_transit' and text == 'Доп расходы':
        await bot.send_message(chat_id, 'Доп расходы пока не работают')
    # Доп условия
    elif stage == 'in_transit' and text == 'Доп условия':
        await bot.send_message(chat_id, 'Доп условия пока не работают')
    # Форс-мажоры
    elif stage == 'in_transit' and text == 'Форс-мажоры':
        await bot.send_message(chat_id, 'Форс-мажоры пока не работают')
    # Прибыл на место разгрузки 
    elif stage == 'in_transit' and text == 'ПРИБЫЛ НА МЕСТО РАЗГРУЗКИ':
        time_end_transit = datetime.datetime.now()

        id_driver = get_id_driver(chat_id)
        time_start_period = get_one_param_db('time_start_period', chat_id)
        current_dir = get_one_param_db('current_dir', chat_id)

        data = read_json_file(id_driver, time_start_period, current_dir)
        data['time_end_transit'] = str(time_end_transit)
        write_json_file(id_driver, time_start_period, current_dir, data)


        markup = types.ReplyKeyboardRemove()
        
        ex_update(f"UPDATE users SET stage = 'get_koor_finish' WHERE telegram_id = {chat_id}")

        await bot.send_message(chat_id, 'Укажите координаты финиша', reply_markup=markup)
    # Координаты финиша
    elif stage == 'get_koor_finish':
        ex_update(f"UPDATE users SET stage = 'end_mileage_km', dot_end = '{text}' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, 'Введите данные с одометра одним число без пробелов')
    elif stage == 'end_mileage_km':
        # TODO сделать проверку, что не может быть меньше, чем начальное
        if text.isdigit():
            ex_update(f"UPDATE users SET stage = 'info_unload', end_mileage = {text} WHERE telegram_id = {chat_id}")
            await bot.send_message(chat_id, 'Отправьте данные о разгурке')
            # TODO какие нах данные? хахахахах
        else:
            await bot.send_message(chat_id, 'Вы ввели число неправильно, введите число без пробелов и точек')
    elif stage == 'info_unload':

        id_driver = get_id_driver(chat_id)
        time_start_period = get_one_param_db('time_start_period', chat_id)
        current_dir = get_one_param_db('current_dir', chat_id)
        data = read_json_file(id_driver, time_start_period, current_dir)

        data['info_unload'] = str(text)

        write_json_file(id_driver, time_start_period, current_dir, data)

        ex_update(f"UPDATE users SET stage = 'additional_conditions' WHERE telegram_id = {chat_id}")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Пропустить')

        await bot.send_message(chat_id, 'Напишите какие-то дополнительные условия или нажмите кнопку пропустить', reply_markup=markup)
    elif stage == 'additional_conditions':
        if text != 'Пропустить':
            id_driver = get_id_driver(chat_id)
            current_dir = get_one_param_db('current_dir', chat_id)
            time_start_period = get_one_param_db('time_start_period', chat_id)
            data = read_json_file(id_driver, time_start_period, current_dir)

            data['additional_conditions'] = str(text)

            write_json_file(id_driver, time_start_period, current_dir, data)

        ex_update(f"UPDATE users SET stage = 'end_unload' WHERE telegram_id = {chat_id}")

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Разгрузка закончена")
        await bot.send_message(chat_id, 'Когда разгрузка будет закончена - нажмите кнопку', reply_markup=markup)
    elif stage == 'end_unload' and text == 'Разгрузка закончена':
        time_end_unload = datetime.datetime.now()

        id_driver = get_id_driver(chat_id)
        time_start_period = get_one_param_db('time_start_period', chat_id)
        current_dir = get_one_param_db('current_dir', chat_id)

        data = read_json_file(id_driver, time_start_period, current_dir)
        data['time_end_unload'] = str(time_end_unload)
        write_json_file(id_driver, time_start_period, current_dir, data)

        markup = types.ReplyKeyboardRemove()
        ex_update(f"UPDATE users SET stage = 'get_done_ttn' WHERE telegram_id = {chat_id}")
    
        # TODO сделать чтобы не перевиодился в unicode в json файле
        await bot.send_message(chat_id, 'Отправьте фото накладной (ТТН отмеченной получателем)', reply_markup=markup)
    elif stage == 'end_poezdka' and text == 'Закончить период':
        time_start_period = get_one_param_db('time_start_period', chat_id)
        time_end_period = datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S")
        id_driver = get_one_param_db('id', chat_id)
        os.rename(f'drive/{id_driver}/{time_start_period}', f'drive/{id_driver}/{time_start_period} - {time_end_period}')
        ex_update(f'UPDATE users SET time_start_period = NULL, stage = "new_period" WHERE telegram_id = {chat_id}')
        id_truck = get_one_param_db('id_truck', chat_id)
        ex_update(f'UPDATE trucks SET status = 0 WHERE id = {id_truck}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Начать период')
        await bot.send_message(chat_id, "Вы закончили период, нажмите чтобы начать новый", reply_markup=markup)
    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')
    

@dp.message_handler(content_types='photo')
async def photo_handler(message):
    chat_id = message.chat.id
    stage = ex_get_stage(chat_id)
    count_photo_download = get_one_param_db('count_photo_download', chat_id)
    time_start_period = get_one_param_db('time_start_period', chat_id)
    id = get_one_param_db('id', chat_id)
    current_dir = get_one_param_db('current_dir', chat_id)
    if stage == 'end_photo_download' or stage == 'doc_gruz':
        if 'files' not in os.listdir(f'drive/{id}/{time_start_period}/{current_dir}'):
            os.mkdir(f'drive/{id}/{time_start_period}/{current_dir}/files')
        if stage == 'end_photo_download':
            await message.photo[-1].download(destination_file=f"drive/{id}/{time_start_period}/{current_dir}/files/ТТН.jpg")
            ex_update(f"UPDATE users SET stage = 'doc_gruz' WHERE telegram_id = {chat_id}")
            await bot.send_message(chat_id, 'Отлично, теперь отправьте фото файла на груз')
        elif stage == 'doc_gruz':
            await message.photo[-1].download( destination_file=f"drive/{id}/{time_start_period}/{current_dir}/files/Доки груз.jpg")
            ex_update(f"UPDATE users SET stage = 'gruz_end' WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Старт поездки')
            await bot.send_message(chat_id, 'Отлично, все фото загружены, нажмите на кнопку, когда начнёте поездку', reply_markup=markup)
    elif stage == 'photo_gruz' and 0 <= count_photo_download <= 3:
        count_photo_download += 1
        ex_update(f"UPDATE users SET count_photo_download = count_photo_download + 1 WHERE telegram_id = {chat_id}")
        if 'photo_gruz' not in os.listdir(f'drive/{id}/{time_start_period}/{current_dir}'):
            os.mkdir(f'drive/{id}/{time_start_period}/{current_dir}/photo_gruz')
        await message.photo[-1].download(destination_file=f'drive/{id}/{time_start_period}/{current_dir}/photo_gruz/{count_photo_download}.jpg')
        if count_photo_download == 4:
            ex_update(f"UPDATE users SET stage = 'end_photo_download' WHERE telegram_id = {chat_id}")
            await bot.send_message(chat_id, 'Фото успешно загружены, теперь отправьте фото документов - ТТН')
    elif stage == 'get_done_ttn':
        
        await message.photo[-1].download(destination_file=f'drive/{id}/{time_start_period}/{current_dir}/photo_gruz/done_ttn.jpg')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Начать перевозку')
        markup.add('Закончить период')

        all_data = get_all_obj(chat_id)
        id_driver = get_id_driver(chat_id)
        data = read_json_file(id_driver, time_start_period, current_dir)
        data = {**data, **all_data}
        write_json_file(id_driver, time_start_period, current_dir, data)
        all_price = 0
        id_truck = get_id_truck(chat_id)
        price_1_km = get_one_param_truks('price_1_km', int(id_truck))
        one_krit = ''
        if price_1_km == 12:
            one_krit = 'Площадка 0,9 до 4х осей или Корыто до 3 осей -> <b>12 руб за 1 км</b>'
        elif price_1_km == 14:
            one_krit = '5, 6, 7 оснвые + корыто от 4 осей -> <b>14 руб за 1 км</b>'

        # TODO добавить заявку от логиста
        
        raz_km = get_one_param_db('end_mileage', chat_id) - get_one_param_db('start_mileage', chat_id)
        if raz_km <= 150:
            all_price += 5000
        elif 150 < raz_km <= 200:
            all_price += 4500
        elif 200 < raz_km <= 250:
            all_price += 4000
        elif 250 < raz_km <= 300:
            all_price += 3500
        elif 300 < raz_km <= 350:
            all_price += 3000
        elif 350 < raz_km <= 400:
            all_price += 2500
        elif 400 < raz_km <= 450:
            all_price += 2000
        elif 450 < raz_km <= 500:
            all_price += 1500
        elif 500 < raz_km <= 550:
            all_price += 1000
        elif 550 < raz_km <= 600:
            all_price += 500
        
        # TODO сохранить это в словарь


        two_krit = f'Надбавка за плечо -> <b>{all_price}</b>'

        total = price_1_km * raz_km + all_price

        s = f'1) {one_krit}\n2) {two_krit}\nИтоговая сумма без дополнительных условий: <b>{total}</b>'
        
            
        await bot.send_message(chat_id, f'Ваш чек\n{s}', parse_mode='html')
        # TODO формирование чека
        # TODO добавить отдых и тд
        ex_update(f"UPDATE users SET stage = 'end_poezdka' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, 'Фотография успешно сохранена теперь выбирайте, чем заняться дальше', reply_markup=markup)
    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')


# @dp.message_handler(content_types='location')
# async def location_handler(message):
#     print(message)
    # TODO локация так себе работает


executor.start_polling(dp, skip_updates=True)
