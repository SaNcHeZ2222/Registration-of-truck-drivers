import zipfile
from other_func import *
from config import token
import os
import datetime
import json
import pandas
import shutil
import pandas as pd


token = token
# trucks_delivery_bot

bot = Bot(token)
dp = Dispatcher(bot)

admin = [703194398, 576856227, 864436008]


@dp.message_handler(commands='start')
async def start_message(message: types.Message):
    chat_id = message.chat.id

    connection = sqlite3.connect('base.db', check_same_thread=True)
    cursor = connection.cursor()

    all_id_drivers = {i[0] for i in cursor.execute('SELECT telegram_id FROM users')}

    connection.commit()
    connection.close()

    if chat_id not in all_id_drivers:
        connection = sqlite3.connect('base.db', check_same_thread=True)
        cursor = connection.cursor()

        cursor.execute(f"INSERT INTO users(telegram_id, stage) VALUES ({chat_id}, 'start_registration')")

        connection.commit()
        connection.close()
        
        markup = types.ReplyKeyboardRemove()
        await bot.send_message(chat_id, 'Напиши ваше ФИО', reply_markup=markup)
    else:
        if chat_id in admin:
            ex_update(f'UPDATE users SET stage = "main" WHERE telegram_id = {chat_id}')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Создать заявку')
            markup.add('Активные поездки')
            markup.add('Предыдущие поездки')
            markup.add('Вопросы')
            await bot.send_message(chat_id, 'Главное меню', reply_markup=markup)
        else:
            await bot.send_message(chat_id, 'Вы не можете выйти в меню, тк везёте груз')


@dp.message_handler(content_types='text')
async def text_handler(message: types.Message):
    chat_id = message.chat.id
    stage = ex_get_stage(chat_id)
    text = message.text
    if stage == 'start_registration': # Запрос фамилии
        ex_update(f'UPDATE users SET stage = "phone_number", fio = "{text}" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, "Напишите ваш номер телефона")
    elif (text == 'Вернуться в главное меню' or text == 'Вернуться в меню')  and chat_id in admin:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Создать заявку')
        markup.add('Активные поездки')
        markup.add('Предыдущие поездки')
        markup.add('Вопросы')
        await bot.send_message(chat_id, 'Вы в главном меню', reply_markup=markup)
        ex_update(f'UPDATE users SET stage = "main" WHERE telegram_id = {chat_id}')
    elif stage == 'phone_number' or (stage == 'active_drive' and text == 'Вернуться в меню'):
        if text != 'Вернуться в меню':
            ex_update(f'UPDATE users SET stage = "end_registration", phone = "{text}" WHERE telegram_id = {chat_id}')
        else:
            ex_update(f'UPDATE users SET stage = "end_registration" WHERE telegram_id = {chat_id}')
        if chat_id in admin:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Создать заявку')
            markup.add('Активные поездки')
            markup.add('Предыдущие поездки')
            markup.add('Вопросы')
        else:
            markup = get_main_menu_markup()
        await bot.send_message(chat_id, "Спасибо, регистрацию завершена", reply_markup=markup)
    # Предыдущие поездки
    elif text == 'Предыдущие поездки' and chat_id in admin:
        ex_update(f'UPDATE users SET stage = "pred_drivers" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        connection = sqlite3.connect(f'base.db', check_same_thread=True)
        cursor = connection.cursor()

        all_id_drivers = {f'{i[0]} {i[1]}' for i in cursor.execute('SELECT id, fio FROM users')}

        connection.commit()
        connection.close()

        for i in all_id_drivers:
            markup.add(i)
        markup.add('Вернуться в меню')
        # TODO сделать проверку, чтобы в списке были только пользователи, который ездили уже
        # TODO сделать отбор только предыдущих поездок
        await bot.send_message(chat_id, 'Выберите пользователя, чьи поездки хотите посмотреть', reply_markup=markup)
    elif stage == 'pred_drivers':
        id_driver = text.split()[0]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        try:
            list_dir_period = os.listdir(f'drive/{id_driver}')

            for i in list_dir_period:
                markup.add(i)

            markup.add('Вернуться в меню')
            ex_update(f'UPDATE users SET stage = "pred_drivers_period", d = "{id_driver}" WHERE telegram_id = {chat_id}')
            await bot.send_message(chat_id, 'Выберите период', reply_markup=markup)
        except Exception as e:
            print(e)
    elif stage == 'pred_drivers_period':
        period = text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        id_driver = get_one_param_db('d', chat_id)
        list_dir_poezdka = os.listdir(f'drive/{id_driver}/{period}')
        for i in list_dir_poezdka:
            if os.path.isdir(f'drive/{id_driver}/{period}/{i}'):
                markup.add(i)
        if 'info.xlsx' in list_dir_poezdka:
            markup.add('Скачать info.xlsx')
        markup.add('Вернуться в меню')
        ex_update(f'UPDATE users SET stage = "pred_drivers_poezdka", s = "{period}" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, 'Выберите поездку или нажмите на кнопку скачать итог периода', reply_markup=markup)
    elif text == 'Скачать info.xlsx':
        id_driver = get_one_param_db('d', chat_id)
        period = get_one_param_db('s', chat_id)
        with open(f"drive/{id_driver}/{period}/info.xlsx", 'rb') as file:
            await bot.send_document(chat_id, (f'Итог периода {period}.xlsx', file))
    elif stage == 'pred_drivers_poezdka':
        ex_update(f'UPDATE users SET stage = "pred_drivers_done", v = "{text}" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Скачать папку поездки")
        markup.add('Изменить поездку')
        markup.add('Вернуться в меню')
        await bot.send_message(chat_id, 'Выберите действие', reply_markup=markup)
    elif text == 'Скачать папку поездки' and chat_id in admin:
        id_driver = get_one_param_db("d", chat_id)
        period = get_one_param_db("s", chat_id)
        poezdka = get_one_param_db("v", chat_id)
        if 'info.json' in os.listdir(f'drive/{id_driver}/{period}/{poezdka}'):
            # TODO формируем excel и потравляем и отправляем всю папку
            # TODO отправляем файлы и фото на груз
            # TODO сделать excel 
            with zipfile.ZipFile(f"drive/{id_driver}/{period}/{poezdka}/all_info.zip", 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for folder_name, subfolders, files in os.walk(f'drive/{id_driver}/{period}/{poezdka}'):
                    for file in files:
                        file_path = os.path.join(folder_name, file)
                        zip_file.write(file_path, os.path.relpath(file_path, f'drive/{id_driver}/{period}/{poezdka}'))
            with open(f"drive/{id_driver}/{period}/{poezdka}/all_info.zip", 'rb') as zip_file:
                await bot.send_document(chat_id, (f'Папка {id_driver}/{period}/{poezdka}.zip', zip_file))
            os.remove(f"drive/{id_driver}/{period}/{poezdka}/all_info.zip")
            await bot.send_message(chat_id, 'Вот все ваши данные о этой поездке')
    # Активные поездки
    elif text == 'Изменить поездку':
        ex_update(f'UPDATE users SET stage = "pred_drivers_edit" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Вернуться в меню")
        await bot.send_message(chat_id, "Отправьте excel с новыми данными")
    elif chat_id in admin and (stage == 'main' or stage == 'start_registration' or stage == 'end_registration') and text == 'Активные поездки':
        ex_update(f'UPDATE users SET stage = "active_drive" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        all_active_driver = ex_get_active_drive()
        for i in all_active_driver:
            markup.add(' '.join(map(str, i)))
            # TODO убрать admin_id
        markup.add('Вернуться в меню')
        await bot.send_message(chat_id, 'Выберите айди', reply_markup=markup)
    elif chat_id in admin and stage == 'active_drive' and text in (' '.join(map(str, i)) for i in ex_get_active_drive()):
        id_driver = str(text.split()[0])
        ex_update(f'UPDATE users SET stage = "dop_uslovia", active = "{id_driver}" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Добавить надбавку за поездку')
        markup.add('Удалить условия')
        markup.add('Вернуться в меню')
        current_dir = get_one_param_db_id('current_dir', int(id_driver))
        await bot.send_message(chat_id, f'Поездка: {current_dir}', reply_markup=markup)
    elif stage == 'dop_uslovia' and text == 'Добавить надбавку за поездку':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Вернуться в меню")
        ex_update(f'UPDATE users SET stage = "dop_uslovia_add" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, 'Напишите название надбавки', reply_markup=markup)
    elif stage == 'dop_uslovia_add':
        ex_update(f'UPDATE users SET stage = "dop_uslovia_price", s = "{text}" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, 'Напишите цену одним чисом\n-----------\nПример: 5000')
    elif stage == 'dop_uslovia_price':
        try:
            name_uslovie = get_one_param_db('s', chat_id)
            ex_update(f'UPDATE users SET stage = "dop_uslovia_price_done" WHERE telegram_id = {chat_id}')
            id_driver = get_one_param_db('active', chat_id)
            active_session = sorted(os.listdir(f'drive/{id_driver}'), reverse=True)[0]
            active_dir = sorted(os.listdir(f'drive/{id_driver}/{active_session}'), key=lambda x: os.path.getctime(f'drive/{id_driver}/{active_session}'), reverse=True)[0]
            data = read_json_file(id_driver, active_session, active_dir)
            data[f"dop {name_uslovie}"] = int(text)
            write_json_file(id_driver, active_session, active_dir, data)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Вернуться в меню')
            await bot.send_message(chat_id, f'Вы добавили <b>{name_uslovie}</b> с ценой <b>{text}</b>', parse_mode='html')
        except Exception as e:
            await bot.send_message(chat_id, "Вы ввели число неправильно!")



    elif stage == 'dop_uslovia' and text == 'Удалить условия':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        id_driver = get_one_param_db('active', chat_id)
        active_session = sorted(os.listdir(f'drive/{id_driver}'), reverse=True)[0]
        active_dir = sorted(os.listdir(f'drive/{id_driver}/{active_session}'), key=lambda x: os.path.getctime(f'drive/{id_driver}/{active_session}'), reverse=True)[0]
        data = read_json_file(id_driver, active_session, active_dir)
        all_uslovia = [i for i in data if 'dop' in i]
        for i in all_uslovia:
            markup.add(i)
        markup.add("Вернуться в главное меню")
        ex_update(f'UPDATE users SET stage = "dop_uslovia_remove" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, 'Нажмите, чтобы удалить условие', reply_markup=markup)
    elif stage == 'dop_uslovia_remove':
        id_driver = get_one_param_db('active', chat_id)
        active_session = sorted(os.listdir(f'drive/{id_driver}'), reverse=True)[0]
        active_dir = sorted(os.listdir(f'drive/{id_driver}/{active_session}'), key=lambda x: os.path.getctime(f'drive/{id_driver}/{active_session}'), reverse=True)[0]
        data = read_json_file(id_driver, active_session, active_dir)
        del data[text]
        all_uslovia = [i for i in data if 'dop' in i]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in all_uslovia:
            markup.add(i)
        markup.add("Вернуться в главное меню")
        write_json_file(id_driver, active_session, active_dir, data)
        ex_update(f'UPDATE users SET stage = "dop_uslovia_remove_done" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, f'Вы удалили {text}', reply_markup=markup)
    elif chat_id in admin and (stage == 'main' or stage == 'start_registration' or stage == 'end_registration') and text == 'Создать заявку':
        
        connection = sqlite3.connect('base.db', check_same_thread=True)
        cursor = connection.cursor()

        all_id_drivers = {f'{i[0]} {i[1]}' for i in cursor.execute('SELECT id, fio FROM users')}

        connection.commit()
        connection.close()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in all_id_drivers:
            markup.add(i)
        ex_update(f'UPDATE users SET stage = "select_id_order" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, 'Выберите водителя, которму хотите создать заявку', reply_markup=markup)
    elif stage == 'select_id_order' and chat_id in admin:
        markup = types.ReplyKeyboardRemove()
        help_id_truck = int(text.split()[0])

        data = read_order()

        if help_id_truck not in data.keys():
            data[str(help_id_truck)] = {}
        write_order(data)
        ex_update(f'UPDATE users SET stage = "select_where_order", help_id_truck = "{help_id_truck}" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, 'Введите откуда - куда должен поехать водитель или отправьте excel файл', reply_markup=markup)
    elif stage == 'select_where_order':
        id_help = get_one_param_db('help_id_truck', chat_id)
        data = read_order()

        data[id_help]['from_where_to_where'] = text

        write_order(data)

        ex_update(f'UPDATE users SET stage = "select_name_gruz" WHERE telegram_id = {chat_id}')
        
        await bot.send_message(chat_id, 'Введите имя груза')
    elif stage == 'select_name_gruz':
        id_help = get_one_param_db('help_id_truck', chat_id)
        data = read_order()

        data[id_help]['name_gruz'] = text

        write_order(data)

        ex_update(f'UPDATE users SET stage = "select_dhv_order" WHERE telegram_id = {chat_id}')
        
        await bot.send_message(chat_id, 'Введите длину, ширину, высоту через пробел\nПример 12м35см -> 12.35')
    elif stage == 'select_dhv_order':
        
        dhv = [i for i in text.split()]
        try: 
            float(dhv[0])
            float(dhv[1])
            float(dhv[2])
            id_help = get_one_param_db('help_id_truck', chat_id)
            data = read_order()

            data[id_help]['dhv'] = text

            write_order(data)

            ex_update(f'UPDATE users SET stage = "select_weight_order" WHERE telegram_id = {chat_id}')
            
            await bot.send_message(chat_id, 'Введите вес в тоннах\nПример 12т523кг -> 12.523')
        except Exception as e:
            await bot.send_message(chat_id, 'Вы ввели неправильно, 3 числа через пробел')
    elif stage == 'select_weight_order':
        # TODO сделать проверку на вес
        id_help = get_one_param_db('help_id_truck', chat_id)
        if '.' in text and text.split('.')[0].isdigit() and text.split('.')[1].isdigit():
            data = read_order()
            data[id_help]['weight'] = text
            write_order(data)

            ex_update(f'UPDATE users SET stage = "select_dop_uslovia_order" WHERE telegram_id = {chat_id}')
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            # TODO создание всех дополнительных условий
            markup.add('Выезд за границу РФ: 5000')
            markup.add('Завершить создание заявки')
            await bot.send_message(chat_id, r'Нажимайте на кнопки добавляя условия или нажмите на кнопку "Завершить создание заявки"', reply_markup=markup)
        else:
            await bot.send_message(chat_id, 'Вы ввели число неправильно')
    elif stage == 'select_dop_uslovia_order':
        if text == 'Завершить создание заявки':
            ex_update(f'UPDATE users SET stage = "end_create_order" WHERE telegram_id = {chat_id}')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Вернуться в меню')
            await bot.send_message(chat_id, 'Вы завершили создание заявки', reply_markup=markup)
        else:
            id_help = get_one_param_db('help_id_truck', chat_id)

            data = read_order()
            
            data[id_help][f'dop {text}'] = int(text.split(':')[-1])
            
            write_order(data)
            await bot.send_message(chat_id, f'Вы добавили {text}')

    # Главное меню и выбор авто
    elif ((stage == 'end_registration' or stage == 'main') and text == 'Выбрать авто') or (stage == 'new_period' and text == 'Новый период') or (stage == 'go_per' and text == "Вернуться к выбору тягача"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        trucks = ex_get_trucks_list()
        for i in trucks:
            if i[4] == 0:
                markup.add(f'{i[0]} {i[1]} {i[2]} {i[3]}')
        ex_update(f"UPDATE users SET stage = 'avto' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, "Выберите тягач", reply_markup=markup)
    elif stage == 'avto' or text == 'Вернуться к выбору полуприцепа':
        if text in {f'{i[0]} {i[1]} {i[2]} {i[3]}' for i in ex_get_trucks_list() if i[4] == 0} or text == 'Вернуться к выбору полуприцепа':
            if text != 'Вернуться к выбору полуприцепа':
                id_truck = int(text.split()[0])
                ex_update(f"UPDATE users SET stage = 'go_per', id_truck = {id_truck} WHERE telegram_id = {chat_id}")
            else:
                ex_update(f"UPDATE users SET stage = 'go_per' WHERE telegram_id = {chat_id}")

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            # markup.add("Новый период")
            trailer = ex_get_trailer_list()
            for i in trailer:
                markup.add(f"{i[0]} {i[1]}")
            markup.add("Вернуться к выбору тягача")
            await bot.send_message(chat_id, f'Вы выбрили: {text} тягач, теперь выберите полуприцеп', reply_markup=markup)
        else:
            # TODO кнопка поддержки
            await bot.send_message(chat_id, 'Нет такого авто в списке, напиши в тех поддержку')
    elif stage == 'go_per':
        # TODO надо ли делать стату у трейлера?
        if text in {f'{i[0]} {i[1]}' for i in ex_get_trailer_list()}:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            ex_update(f"UPDATE users SET stage = 'go_per1', id_trailer = {int(text.split()[0])} WHERE telegram_id = {chat_id}")
            markup.add("Новый период")
            markup.add("Вернуться к выбору полуприцепа")
            await bot.send_message(chat_id, f'Вы выбрали {text} трейлер', reply_markup=markup)
        else:
            # TODO кнопка поддержки
            await bot.send_message(chat_id, 'Нет такого авто в списке, напиши в тех поддержку')
    # Начать поездку
    elif (stage == 'go_per1' and text == 'Новый период') or (text == 'Начать перевозку' and stage == 'end_poezdka') or (text == 'Вернуться к пункту "Откуда - Куда"' and stage == 'type_drive1'):
        time_start_period = get_one_param_db('time_start_period', chat_id)
        if time_start_period == None:
            id_truck = get_id_truck(chat_id)
            time_now = datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S")
            ex_update(f"UPDATE trucks SET status = 1 WHERE id = {id_truck}")
            ex_update(f"UPDATE users SET stage = 'from_where1', time_start_period = '{time_now}', active = 1 WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'from_where1' WHERE telegram_id = {chat_id}")

        # TODO если заявка от логиста, то подсказка
        id_driver = str(get_id_driver(chat_id))
        data = read_order()
            
        if id_driver in data.keys():
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(data[id_driver]['from_where_to_where'])
        else:
            markup = types.ReplyKeyboardRemove()
        
        if text == 'Вернуться к пункту "Откуда - Куда"':
            current_dir = get_one_param_db('current_dir', chat_id) 
            id_driver = get_id_driver(chat_id)
            time_now = get_one_param_db('time_start_period', chat_id)
            if time_now in os.listdir(f'drive/{id_driver}') and current_dir in os.listdir(f'drive/{id_driver}/{time_now}'):
                shutil.rmtree(f'drive/{id_driver}/{time_now}/{current_dir}')
        await bot.send_message(chat_id, "Укажите маршрут (откуда - куда)", reply_markup=markup)
    # Откуда - куда
    elif stage == 'from_where1':
        id_driver = get_id_driver(chat_id)
        id_truck = get_id_truck(chat_id)
        # TODO сделать проверка на одинаковые имена на всякий случай)
        # TODO если есть не закрытый, то удалить
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

        ex_update(f"UPDATE users SET stage = 'type_drive1', from_where = '{text}', current_dir = '{current_dir}', count_photo_download = 0 WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Поездка с грузом')
        markup.add('Порожний перегон')
        markup.add('Вернуться к пункту "Откуда - Куда"')
        await bot.send_message(chat_id, 'Выберите тип поездки', reply_markup=markup)
        # TODO Порожний перегон
    # elif text == 'Порожний перегон':
    elif stage == 'start_mileage' and (text == 'Вернуться к выбору типа поездок' and stage == 'start_mileage'):
        if text != 'Вернуться к выбору типа поездок':
            ex_update(f"UPDATE users SET stage = 'type_drive1', from_where = '{text}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'type_drive1' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Поездка с грузом')
        markup.add('Порожний перегон')
        markup.add('Вернуться к пункту "Откуда - Куда"')
        await bot.send_message(chat_id, 'Выберите тип поездки', reply_markup=markup)
    elif (stage == 'type_drive1' and text == 'Поездка с грузом') or (text == 'Вернуться к вводу данных с одометра' and stage == 'dot_start1'):
        if text == 'Вернуться к вводу данных с одометра':
            ex_update(f"UPDATE users SET stage = 'start_mileage' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'start_mileage', type_drive = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться к выбору типа поездок')
        await bot.send_message(chat_id, "Введите данные с одометра числом без пробелов", reply_markup=markup)
    elif stage == 'start_mileage' or (text == 'Вернуться к вводу координат' and stage == 'dot_start2'):
        if text.isdigit() or text == 'Вернуться к вводу координат':
            if text != 'Вернуться к вводу координат':
                ex_update(f"UPDATE users SET stage = 'dot_start1', start_mileage = {int(text)} WHERE telegram_id = {chat_id}")
            else:
                ex_update(f"UPDATE users SET stage = 'dot_start1' WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton('Отправить геолокацию️', request_location=True))
            markup.add('Вернуться к вводу данных с одометра')

            await bot.send_message(chat_id, 'Введите координаты (из яндекс карт) или нажмите на кнопку отправки геолокации', reply_markup=markup)

        # Фото груза загружены, отправьте фото нагрузки на оси
        else:
            await bot.send_message(chat_id, "Вы ввели число некоректно, попробуйте ещё раз")
    elif stage == 'dot_start1' or (text == 'Вернуться к вводу имя груза' and stage == 'd'):
        if text != 'Вернуться к вводу имя груза':
            ex_update(f"UPDATE users SET stage = 'dot_start2', dot_start = '{text}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'dot_start2' WHERE telegram_id = {chat_id}")

        porog = get_one_param_db('porog', chat_id)
        if porog == 0:
            id_driver = str(get_one_param_db('id', chat_id))
            data = read_order()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            if id_driver in data.keys():
                markup.add(data[id_driver]['name_gruz'])
            markup.add('Вернуться к вводу координат')
            await bot.send_message(chat_id, "Введите <b>название груза</b>", reply_markup=markup, parse_mode='html')
        else:
            ex_update(f"UPDATE users SET stage = 'end_photo_download1' WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Закончить добавление')
            await bot.send_message(chat_id, 'Отправьте фото нагрузки на оси', reply_markup=markup)
    elif stage == 'dot_start2' or (text == 'Вернуться к вводу длины' and stage == 's'):
        if text != 'Вернуться к вводу длины':
            ex_update(f"UPDATE users SET stage = 'd', name_gruz = '{text}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'd' WHERE telegram_id = {chat_id}")
        id_driver = str(get_one_param_db('id', chat_id))
        data = read_order()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        if id_driver in data.keys():
            markup.add(data[id_driver]['dhv'].split()[0])
        markup.add('Вернуться к вводу имя груза')
        await bot.send_message(chat_id, "Померяйте <b>длину</b> груза и укажите\n————————————————\nПример: (12.01)", reply_markup=markup, parse_mode='html')
    elif stage == 'd' or (text == 'Вернуться к вводу ширины' and stage == 'v'):
        # TODO сделать проверку на длину через точку
        if text != 'Вернуться к вводу ширины':
            ex_update(f"UPDATE users SET stage = 's', d = '{text}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 's' WHERE telegram_id = {chat_id}")
        id_driver = str(get_one_param_db('id', chat_id))
        data = read_order()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if id_driver in data.keys():
            markup.add(data[id_driver]['dhv'].split()[1])
        markup.add('Вернуться к вводу длины')
        await bot.send_message(chat_id, "Померяйте <b>ширину</b> груза и укажите\n————————————————\nПример: (12.01)", reply_markup=markup, parse_mode='html')
    elif stage == 's' or (text == 'Вернуться к вводу высоты' and stage == 'weight'):
        # TODO сделать проверку на ввод ширины через точку
        if text != 'Вернуться к вводу высоты':
            ex_update(f"UPDATE users SET stage = 'v', s = '{text}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'v' WHERE telegram_id = {chat_id}")
        id_driver = str(get_one_param_db('id', chat_id))
        data = read_order()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        if id_driver in data.keys():
            markup.add(data[id_driver]['dhv'].split()[2])
        markup.add('Вернуться к вводу ширины')
        await bot.send_message(chat_id, "Померяйте <b>высоту</b> груза и укажите\n————————————————\nПример: (12.01)", reply_markup=markup, parse_mode='html')
    elif stage == 'v' or (text == 'Вернуться к вводу веса' and stage == 'dlina_avto'):
        # TODO сделать проверку на ввод высоты через точку
        if text != 'Вернуться к вводу веса':
            ex_update(f"UPDATE users SET stage = 'weight', v = '{text}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'weight' WHERE telegram_id = {chat_id}")
        data = read_order()
        id_driver = str(get_one_param_db('id', chat_id))
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        if id_driver in data.keys():
            markup.add(data[id_driver]['weight'])
        markup.add('Вернуться к вводу высоты')
        if text == 'Вернуться к вводу веса':
            pass
            # TODO сделать обнуление счётчика фото
        await bot.send_message(chat_id, "Померяйте <b>вес</b> груза и укажите\n————————————————\nПример: (12.123)", reply_markup=markup, parse_mode='html')
    elif stage == 'weight' or text == 'Вернуться к длины поезда':
        if text != 'Вернуться к длины поезда':
            ex_update(f"UPDATE users SET stage = 'dlina_avto', weight = '{text}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'dlina_avto' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Вернуться к вводу веса")
        await bot.send_message(chat_id, 'Померяйте общую <b>длину</b> автопоезда и укажите\n————————————————\nПример: (12.01)', reply_markup=markup, parse_mode='html')
        # TODO СДЕЛАТЬ 2 переменных
    elif stage == 'dlina_avto' or text == 'Вернуться к вводу общей высоты':
        if text != 'Вернуться к длины поезда':
            ex_update(f"UPDATE users SET stage = 'heigh_avto', total_lenght = '{text}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'heigh_avto WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Вернуться к длины поезда")
        await bot.send_message(chat_id, 'Померяйте общую <b>высоту</b> автопоезда и укажите\n————————————————\nПример: (12.01)', reply_markup=markup, parse_mode='html')
    elif stage == 'heigh_avto':
        # TODO сделать проверку на ввод веса в тоннах через точку
        ex_update(f"UPDATE users SET stage = 'photo_gruz', total_height = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться к вводу общей высоты')
        await bot.send_message(chat_id, "<b>Внимание вернуться к отправке фото нельзя, выбирайте фото внимательно!\n\n</b>Отправьте 4 фото груза с разных сторон", reply_markup=markup, parse_mode='html')
        # TODO сделать вернуться к вводу фото, нах не надо
    # TODO сделать порожний перегон
    elif stage == 'type_drive1' and text == 'Порожний перегон':
        if text == 'Вернуться к вводу данных с одометра':
            ex_update(f"UPDATE users SET stage = 'start_mileage' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'start_mileage', type_drive = '{text}', porog = 1 WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться к выбору типа поездок')
        await bot.send_message(chat_id, "Введите данные с одометра числом без пробелов", reply_markup=markup)
    elif (stage == 'gruz_end' and text == 'Старт поездки') or (stage == 'dop_razhod' and text == "Дальше"):
        if text != 'Дальше':
            time_start_transit = datetime.datetime.now()
            id_driver = get_id_driver(chat_id)
            current_dir = get_one_param_db('current_dir', chat_id)
            time_start_period = get_one_param_db('time_start_period', chat_id)

            data = read_json_file(id_driver, time_start_period, current_dir)
            data['time_start_transit'] = str(time_start_transit)
            write_json_file(id_driver, time_start_period, current_dir, data)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Доп расходы')
        markup.add('ПРИБЫЛ НА МЕСТО РАЗГРУЗКИ')
        ex_update(f"UPDATE users SET stage = 'in_transit' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, 'Добавляйте условия и тд, пока не приедете на место разгрузки', reply_markup=markup)
    # Доп расходы
    elif (stage == 'in_transit' and text == 'Доп расходы') or text == 'Вернуться в Доп расходы':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Добавить расход")
        markup.add("Удалить расход")
        markup.add("Дальше")
        ex_update(f"UPDATE users SET stage = 'dop_razhod' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, 'Вы в режиме дописания дополнительных рассходов, нажимайте на кнопки, чтобы добавить расход или нажмите на кнопку ДАЛЬШЕ', reply_markup=markup)
    elif stage == 'dop_razhod' and text == 'Добавить расход':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в Доп расходы')
        ex_update(f"UPDATE users SET stage = 'add_name_dop_razhod' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, "Напиши имя вашего расхода", reply_markup=markup)
    elif stage == 'add_name_dop_razhod':
        ex_update(f"UPDATE users SET stage = 'add_price_dop_razhod', name_dop_razhod = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в Доп расходы')
        await bot.send_message(chat_id, "Напишите цену расходы, без копеек, одним числом", reply_markup=markup)
    elif stage == 'add_price_dop_razhod':
        try:
            price = int(text)
            name_dop_razhod = get_one_param_db('name_dop_razhod', chat_id)

            id_driver = get_id_driver(chat_id)
            time_start_period = get_one_param_db('time_start_period', chat_id)
            current_dir = get_one_param_db('current_dir', chat_id)

            data = read_json_file(id_driver, time_start_period, current_dir)
            data[f"1dop {name_dop_razhod}"] = price
            write_json_file(id_driver, time_start_period, current_dir, data)
            ex_update(f"UPDATE users SET stage = 'dop_razhod' WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Добавить расход")
            markup.add("Удалить расход")
            markup.add("Дальше")
            await bot.send_message(chat_id, f"Вы добавили {name_dop_razhod} с ценой {price}", reply_markup=markup)
        except Exception as e:
            await bot.send_message(chat_id, "Вы ввели цену неправильно")
    elif stage == 'dop_razhod' and text == 'Удалить расход':
        id_driver = get_id_driver(chat_id)
        time_start_period = get_one_param_db('time_start_period', chat_id)
        current_dir = get_one_param_db('current_dir', chat_id)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        data = read_json_file(id_driver, time_start_period, current_dir)
        all_dop_uslovia = [f"{i}:{data[i]}" for i in data.keys() if '1dop' in i]
        for i in all_dop_uslovia:
            markup.add(i)
        markup.add('Вернуться в Доп расходы')
        # data = read_json_file(id_driver, time_start_period, current_dir)
        #             data[f"1dop {name_dop_razhod}"] = price
        #             write_json_file(id_driver, time_start_period, current_dir, data)
        ex_update(f"UPDATE users SET stage = 'remove_dop_uslovia' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, "Выберите какой расход хотите удалить", reply_markup=markup)
    elif stage == 'remove_dop_uslovia':
        key = text.split(':')[0]
        id_driver = get_id_driver(chat_id)
        time_start_period = get_one_param_db('time_start_period', chat_id)
        current_dir = get_one_param_db('current_dir', chat_id)
        try:
            data = read_json_file(id_driver, time_start_period, current_dir)
            del data[key]
            write_json_file(id_driver, time_start_period, current_dir, data)

            ex_update(f"UPDATE users SET stage = 'dop_razhod' WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Добавить расход")
            markup.add("Удалить расход")
            markup.add("Дальше")
            await bot.send_message(chat_id, f"Вы успешно удалили {text}", reply_markup=markup)
        except Exception as e:
            ex_update(f"UPDATE users SET stage = 'dop_razhod' WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Добавить расход")
            markup.add("Удалить расход")
            markup.add("Дальше")
            await bot.send_message(chat_id, "Что-то пошло не так вернитесь в меню", reply_markup=markup)


    # Прибыл на место разгрузки
    elif (stage == 'in_transit' and text == 'ПРИБЫЛ НА МЕСТО РАЗГРУЗКИ') or (text == 'Вернуться к вводу координат финиша' and stage == 'end_mileage_km'):
        if (text != 'Вернуться к вводу координат финиша'):
            time_end_transit = datetime.datetime.now()

            id_driver = get_id_driver(chat_id)
            time_start_period = get_one_param_db('time_start_period', chat_id)
            current_dir = get_one_param_db('current_dir', chat_id)

            data = read_json_file(id_driver, time_start_period, current_dir)
            data['time_end_transit'] = str(time_end_transit)
            write_json_file(id_driver, time_start_period, current_dir, data)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Отправить геолокацию", request_location=True))
        ex_update(f"UPDATE users SET stage = 'get_koor_finish' WHERE telegram_id = {chat_id}")

        await bot.send_message(chat_id, 'Укажите координаты финиша или нажмите на кнопку отправки геолокации', reply_markup=markup)
    # Координаты финиша
    elif stage == 'get_koor_finish' or (text == 'Вернуться к вводу данных с одометра' and stage == 'info_unload'):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться к вводу координат финиша')
        if text != 'Вернуться к вводу данных с одометра':
            ex_update(f"UPDATE users SET stage = 'end_mileage_km', dot_end = '{text}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'end_mileage_km' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, 'Введите данные с одометра одним число без пробелов', reply_markup=markup)
    elif stage == 'end_mileage_km':
        # TODO сделать проверку, что не может быть меньше, чем начальное
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться к вводу данных с одометра')
        if text.isdigit():
            ex_update(f"UPDATE users SET stage = 'additional_conditions', end_mileage = {text} WHERE telegram_id = {chat_id}")

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Добавить доп условия')
            markup.add('Удалить доп условия')
            markup.add('Разгрузка закончена')

            await bot.send_message(chat_id, 'Напишите какие-то дополнительные условия или нажмите кнопку разгрузки', reply_markup=markup)
        else:
            await bot.send_message(chat_id, 'Вы ввели число неправильно, введите число без пробелов и точек',
                               reply_markup=markup)
    elif text == 'Вернуться в меню разгрузки':
        ex_update(f"UPDATE users SET stage = 'additional_conditions' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Добавить доп условия')
        markup.add('Удалить доп условия')
        markup.add('Разгрузка закончена')
        await bot.send_message(chat_id, 'Напишите какие-то дополнительные условия или нажмите кнопку разгрузки', reply_markup=markup)
    elif stage == 'additional_conditions' and text == 'Удалить доп условия':
        id_driver = get_id_driver(chat_id)
        time_start_period = get_one_param_db('time_start_period', chat_id)
        current_dir = get_one_param_db('current_dir', chat_id)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        data = read_json_file(id_driver, time_start_period, current_dir)
        all_dop_uslovia = [f"{i}:{data[i]}" for i in data.keys() if '2dop' in i]
        for i in all_dop_uslovia:
            markup.add(i.replace('2dop ', ''))
        markup.add('Вернуться в меню разгрузки')
        ex_update(f"UPDATE users SET stage = 'remove_additional_conditions' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, "Выберите какое условие хотите удалить", reply_markup=markup)
    elif stage == 'remove_additional_conditions':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню разгрузки')
        key = text.split(':')[0]
        id_driver = get_id_driver(chat_id)
        time_start_period = get_one_param_db('time_start_period', chat_id)
        current_dir = get_one_param_db('current_dir', chat_id)
        try:
            data = read_json_file(id_driver, time_start_period, current_dir)
            del data['2dop ' + key]
            write_json_file(id_driver, time_start_period, current_dir, data)
            ex_update(f"UPDATE users SET stage = 'remove_done_additional_conditions' WHERE telegram_id = {chat_id}")
            await bot.send_message(chat_id, f"Вы успешно удалили {text}", reply_markup=markup)
        except Exception as e:
            await bot.send_message(chat_id, "Что-то пошло не так вернитесь в меню", reply_markup=markup)
    elif stage == 'additional_conditions' and text == 'Добавить доп условия':
        ex_update(f"UPDATE users SET stage = 'additional_conditions_dop' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню разгрузки')
        await bot.send_message(chat_id, 'Введите название условия', reply_markup=markup)
    elif stage == 'additional_conditions_dop':
        ex_update(f"UPDATE users SET stage = 'additional_conditions_dop_price', mega_dop_name = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню разгрузки')
        await bot.send_message(chat_id, "Напишите цену одним числом", reply_markup=markup)
    elif stage == 'additional_conditions_dop_price':
        try:
            mega_dop_name = get_one_param_db('mega_dop_name', chat_id)
    
            ex_update(f'UPDATE users SET stage = "dop_uslovia_price_done" WHERE telegram_id = {chat_id}')
            id_driver = get_id_driver(chat_id)
            time_start_period = get_one_param_db('time_start_period', chat_id)
            current_dir = get_one_param_db('current_dir', chat_id)
            data = read_json_file(id_driver, time_start_period, current_dir)
            data[f"2dop {mega_dop_name}"] = int(text)
            write_json_file(id_driver, time_start_period, current_dir, data)
            
            await bot.send_message(chat_id, f"Вы добавили <b>{mega_dop_name}</b> с ценой <b>{text}</b>", parse_mode='html')
        except Exception as e:
            await bot.send_message(chat_id, "Вы ввели число неправильно")
    elif (stage == 'end_poezdka' and text == 'Между поездками') or text == 'Вернуться в меню между поездками':
        ex_update(f'UPDATE users SET stage = "between_poezdka" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Ремонт')
        markup.add('Выходной')
        markup.add('Ожидание погрузки')
        markup.add('Вернуться')
        await bot.send_message(chat_id, "Выберите что хотите добавить", reply_markup=markup)
    # waiting_loading_day TEXT,
    # waiting_loading_price TEXT
    elif stage == 'between_poezdka' and text == 'Ожидание погрузки':
        ex_update(f'UPDATE users SET stage = "waiting_loading_day1" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню между поездками')
        await bot.send_message(chat_id, "Введите сколько дней ожидали погрузки", reply_markup=markup)
    elif stage == 'waiting_loading_day1':
        ex_update(f'UPDATE users SET stage = "waiting_loading_price1", waiting_loading_day = "{text}" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню между поездками')
        await bot.send_message(chat_id, "Введите сколько денег потратили в ожидании погрузки", reply_markup=markup)
    elif stage == 'waiting_loading_price1':
        ex_update(f'UPDATE users SET stage = "waiting_loading_price_end", waiting_loading_price = "{text}" WHERE telegram_id = {chat_id}')
        waiting_loading_day = get_one_param_db('waiting_loading_day', chat_id)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню между поездками')

        time_start_period = get_one_param_db('time_start_period', chat_id)
        id_driver = get_id_driver(chat_id)

        if 'between_poezdka.json' not in os.listdir(f'drive/{id_driver}/{time_start_period}'):
            with open(f'drive/{id_driver}/{time_start_period}/between_poezdka.json', 'w') as file:
                json.dump({f"Ожидание погрузки": [int(waiting_loading_day), int(text)]}, file)
                file.close()
        else:
            with open(f'drive/{id_driver}/{time_start_period}/between_poezdka.json', "r") as f:
                data = json.load(f)
                days = int(waiting_loading_day)
                price = int(text)
                if 'Ожидание погрузки' in data.keys():
                    days += int(data['Ожидание погрузки'][0])
                    price += int(data['Ожидание погрузки'][1])
                data['Ожидание погрузки'] = [days, price]
                f.close()
                with open(f'drive/{id_driver}/{time_start_period}/between_poezdka.json', 'w') as file:
                    json.dump(data, file)
                    file.close()
        await bot.send_message(chat_id, f"Отлично, вы добавили ожидание погрузки {waiting_loading_day} дней с ценой {text}",
                               reply_markup=markup)
    elif stage == 'between_poezdka' and text == 'Выходной':
        ex_update(f'UPDATE users SET stage = "weekend_day1" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню между поездками')
        await bot.send_message(chat_id, "Введите сколько дней потратили на выходной", reply_markup=markup)
    elif stage == 'weekend_day1':
        ex_update(f'UPDATE users SET stage = "weekend_price1", weekend_day = "{text}" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню между поездками')
        await bot.send_message(chat_id, "Введите сколько денег потратили на выходных одним числом", reply_markup=markup)
    elif stage == 'weekend_price1':
        ex_update(f'UPDATE users SET stage = "weeknd_end", weekend_price = "{text}" WHERE telegram_id = {chat_id}')
        weekend_day = get_one_param_db('weekend_day', chat_id)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню между поездками')

        time_start_period = get_one_param_db('time_start_period', chat_id)
        id_driver = get_id_driver(chat_id)

        if 'between_poezdka.json' not in os.listdir(f'drive/{id_driver}/{time_start_period}'):
            with open(f'drive/{id_driver}/{time_start_period}/between_poezdka.json', 'w') as file:
                json.dump({f"Выходные": [int(weekend_day), int(text)]}, file)
                file.close()
        else:
            with open(f'drive/{id_driver}/{time_start_period}/between_poezdka.json', "r") as f:
                data = json.load(f)
                days = int(weekend_day)
                price = int(text)
                if 'Выходные' in data.keys():
                    days += int(data['Выходные'][0])
                    price += int(data['Выходные'][1])
                f.close()
                data['Выходные'] = [days, price]
                with open(f'drive/{id_driver}/{time_start_period}/between_poezdka.json', 'w') as file:
                    json.dump(data, file)
                    file.close()
        await bot.send_message(chat_id, f"Отлично, вы добавили отдых {weekend_day} дней с ценой {text}",
                               reply_markup=markup)
    elif stage == 'between_poezdka' and text == 'Ремонт':
        ex_update(f'UPDATE users SET stage = "remont_day1" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню между поездками')
        await bot.send_message(chat_id, "Введите сколько дней потратили на ремонт", reply_markup=markup)
    elif stage == 'remont_day1':
        ex_update(f'UPDATE users SET stage = "remont_price1", remont_day = "{text}" WHERE telegram_id = {chat_id}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню между поездками')
        await bot.send_message(chat_id, "Введите сколько денег потратили на ремонт одним числом", reply_markup=markup)
    elif stage == 'remont_price1':
        ex_update(f'UPDATE users SET stage = "remont_end", remont_price = "{text}" WHERE telegram_id = {chat_id}')
        remont_day = get_one_param_db('remont_day', chat_id)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться в меню между поездками')

        time_start_period = get_one_param_db('time_start_period', chat_id)
        id_driver = get_id_driver(chat_id)

        if 'between_poezdka.json' not in os.listdir(f'drive/{id_driver}/{time_start_period}'):
            with open(f'drive/{id_driver}/{time_start_period}/between_poezdka.json', 'w') as file:
                json.dump({f"Ремонт": [int(remont_day), int(text)]}, file)
                file.close()
        else:
            with open(f'drive/{id_driver}/{time_start_period}/between_poezdka.json', "r") as f:
                data = json.load(f)
                days = int(remont_day)
                price =  int(text)
                if 'Ремонт' in data.keys():
                    days += int(data['Ремонт'][0])
                    price += int(data['Ремонт'][1])
                data['Ремонт'] = [days, price]
                f.close()
                with open(f'drive/{id_driver}/{time_start_period}/between_poezdka.json', 'w') as file:
                    json.dump(data, file)
                    file.close()
        await bot.send_message(chat_id, f"Отлично, вы добавили Ремонт {remont_day} дней с ценой {text}", reply_markup=markup)
    elif text == 'Вернуться' and stage == "between_poezdka":
        ex_update(f"UPDATE users SET stage = 'end_poezdka' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Начать перевозку')
        markup.add('Закончить период')
        markup.add('Между поездками')
        await bot.send_message(chat_id, "Вебирте, чем хотите заниматься дальше", reply_markup=markup)
    elif text == 'Пропустить' and stage == 'get_done_ttn':
        time_start_period = get_one_param_db('time_start_period', chat_id)
        current_dir = get_one_param_db('current_dir', chat_id)
    #     ---------------------------------------------------------------------------

        all_data = get_all_obj(chat_id)
        id_driver = str(get_id_driver(chat_id))
        data = read_json_file(id_driver, time_start_period, current_dir)
        data1 = {**data, **all_data}
        write_json_file(id_driver, time_start_period, current_dir, data1)

        with open(f'drive/{id_driver}/{time_start_period}/{current_dir}/info.json', "r") as f:
            info_json = json.load(f)
            f.close()

        truck = get_number_name_color_truck(info_json['id_truck'])
        trailer = get_number_and_price_trailer(info_json['id_trailer'])

        plecho = 0

        raz_km = int(info_json['end_mileage']) - int(info_json['start_mileage'])
        if raz_km <= 150:
            plecho += 5000
        elif 150 < raz_km <= 200:
            plecho += 4500
        elif 200 < raz_km <= 250:
            plecho += 4000
        elif 250 < raz_km <= 300:
            plecho += 3500
        elif 300 < raz_km <= 350:
            plecho += 3000
        elif 350 < raz_km <= 400:
            plecho += 2500
        elif 400 < raz_km <= 450:
            plecho += 2000
        elif 450 < raz_km <= 500:
            plecho += 1500
        elif 500 < raz_km <= 550:
            plecho += 1000
        elif 550 < raz_km <= 600:
            plecho += 500

        price_1_km = trailer[1]

        s = float(get_one_param_db('s', chat_id))

        # За ширину
        za_shirina = 0
        if 3.5 <= s <= 4.0:
            za_shirina += 2
        elif 4.1 <= s <= 4.5:
            za_shirina += 4
        elif 4.51 <= s <= 5.0:
            za_shirina += 6
        elif 5.0 < s:
            za_shirina += 8

        price_1_km += za_shirina

        # За высоту
        za_visota = 0
        total_height = float(get_one_param_db('total_height', chat_id))
        if 4.51 <= total_height <= 5.0:
            za_visota += 2
        elif 5.0 <= total_height:
            za_visota += 4

        price_1_km += za_visota

        # За длину
        za_dlina = 0
        total_lenght = float(get_one_param_db('total_lenght', chat_id))
        if total_lenght > 30:
            za_dlina += 4
        elif total_lenght > 25:
            za_dlina += 2

        price_1_km += za_dlina

        # За вес
        za_ves = 0
        weight = float(get_one_param_db('weight', chat_id))
        if 33 <= weight <= 44:
            za_ves += 2
        elif 45 <= weight <= 69:
            za_ves += 10
        elif 70 < weight:
            za_ves += 15

        price_1_km += za_ves

        info_excel = {"ФИО водителя": info_json['fio'],
                      "Номер водителя": info_json['phone'],
                      "Тягач": f"{truck[0]} {truck[1]} {truck[2]}",
                      "Полуприцеп": f"{trailer[0]}",
                      "Откуда - Куда": info_json['from_where'],
                      "Старт поездки": info_json['time_start_transit'],
                      "Конец поездки": info_json['time_end_transit'],
                      "Конец разгрузки": info_json['time_end_unload'],
                      "Тип поездки": info_json['type_drive'],
                      "Наименование груза": info_json['name_gruz'],
                      "Длина груза": info_json['d'],
                      "Ширина груза": info_json['s'],
                      "Высота груза": info_json['v'],
                      "Масса груза": info_json['weight'],
                      "Общая длина": info_json['total_lenght'],
                      "Общая высота": info_json['total_height'],
                      "Одометр начало": info_json['start_mileage'],
                      "Одометр конец": info_json['end_mileage'],
                      "Координаты старта": info_json['dot_start'],
                      "Координаты финиша": info_json['dot_end'],
                      "Заработал:": "",
                      "За км": f"{price_1_km * (raz_km)}",
                      "За плечо": plecho,
                      "Надбавки": ""
                      }

        all_price = int(info_excel['За км']) + int(info_excel['За плечо'])

        data = read_order()

        nadbavki_string = ''
        nadbavki_digit = 0

        dop_razhod_road_string = ''
        dop_razhod_road_digit = 0

        dop_razhod_razgruz_string = ''
        dop_razhod_razgruz_digit = 0

        if id_driver in data.keys():
            for key in data[id_driver].keys():
                if 'dop' in key:
                    info_excel[key.replace("dop ", "")] = data[id_driver][key]
                    all_price += int(data[id_driver][key])

                    info_excel[key.replace("dop ", "")] = data[id_driver][key]
                    nadbavki_string += f'{key.replace("dop ", "")} = {data[id_driver][key]}\n'
                    nadbavki_digit += int(data[id_driver][key])

        info_excel["Расходы"] = ""
        for key in info_json.keys():
            if '2dop' in key:
                # Разгрузка
                info_excel[key.replace("2dop ", "")] = info_json[key]
                all_price += int(info_json[key])
                dop_razhod_razgruz_string += f'{key.replace("2dop ", "")} = {info_json[key]}\n'
                dop_razhod_razgruz_digit += int(info_json[key])
            elif '1dop' in key:
                # Доп условия
                info_excel[key.replace("1dop ", "")] = info_json[key]
                all_price += int(info_json[key])
                dop_razhod_road_string += f'{key.replace("1dop ", "")} = {info_json[key]}\n'
                dop_razhod_road_digit += int(info_json[key])
            elif 'dop' in key:
                # Надбавки
                info_excel[key.replace("dop ", "")] = info_json[key]
                nadbavki_string += f'{key.replace("dop ", "")} = {info_json[key]}\n'
                nadbavki_digit += int(info_json[key])
                all_price += int(info_json[key])

        info_excel["Итого"] = all_price

        df1 = pd.DataFrame([info_excel]).transpose()

        if 'info.xlsx' not in os.listdir(f'drive/{id_driver}/{time_start_period}'):
            with pd.ExcelWriter(f'drive/{id_driver}/{time_start_period}/{current_dir}/info.xlsx', mode='w') as writer:
                try:
                    df1.to_excel(writer, sheet_name=f'Итог {current_dir}', index=True)
                except Exception as e:
                    print(e)
        else:
            # TODO сделать проверку, чтобы один раз только
            with pd.ExcelWriter(f'drive/{id_driver}/{time_start_period}/{current_dir}/info.xlsx', mode='a') as writer:
                try:
                    df1.to_excel(writer, sheet_name=f'Итог {current_dir}', index=True)
                except Exception as e:
                    print(e)

        check = f"""Ваш чек\n\n1) За километраж = {info_excel['За км']}\n1 км = {price_1_km}\nИз них:\nЗа высоту: {za_visota}\nЗа длину: {za_dlina}\nЗа ширину: {za_shirina}\nЗа вес: {za_ves}\n\n2)Надбвака за плечо: {plecho}\n\n3)Надбавки:\n{nadbavki_string}\n4)Доп. расходы в пути:\n{dop_razhod_road_string}\n5)Доп. расходы при разгрузке:\n{dop_razhod_razgruz_string}\n\nРасходы: {int(dop_razhod_road_digit) + int(dop_razhod_razgruz_digit)}\n\nЗаработано: {int(info_excel['За км']) + int(nadbavki_digit) + int(plecho)}"""

        data = read_order()
        if id_driver in data.keys():
            del data[id_driver]
            write_order(data)
        ex_update(
            f"UPDATE users SET stage = 'end_poezdka', active = 0, count_osi = 1, count_ttn = 1, count_doc = 1 WHERE telegram_id = {chat_id}")

        await bot.send_message(chat_id, check, parse_mode='html')

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Начать перевозку')
        markup.add('Закончить период')
        markup.add('Между поездками')

        await bot.send_message(chat_id, 'Выберите чем будете заниматься дальше', reply_markup=markup)
        # TODO добавить отдых и тд
    # --------------------------------------------------
    elif stage == 'additional_conditions' and text == 'Разгрузка закончена':
        time_end_unload = datetime.datetime.now()

        id_driver = get_id_driver(chat_id)
        time_start_period = get_one_param_db('time_start_period', chat_id)
        current_dir = get_one_param_db('current_dir', chat_id)

        data = read_json_file(id_driver, time_start_period, current_dir)
        data['time_end_unload'] = str(time_end_unload)
        write_json_file(id_driver, time_start_period, current_dir, data)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Пропустить")
        ex_update(f"UPDATE users SET stage = 'get_done_ttn' WHERE telegram_id = {chat_id}")
    
        # TODO сделать чтобы не перевиодился в unicode в json файле
        await bot.send_message(chat_id, 'Отправьте фото накладной (ТТН отмеченной получателем)', reply_markup=markup)
    elif stage == 'end_poezdka' and text == 'Закончить период':
        time_start_period = get_one_param_db('time_start_period', chat_id)
        time_end_period = datetime.datetime.now().strftime("%d.%m.%y %H:%M:%S")
        id_driver = str(get_one_param_db('id', chat_id))

        all_razhod = 0
        all_dohod = 0

        all_json = {}

        count = 0
        for current_dir in os.listdir(f'drive/{id_driver}/{time_start_period}'):
            if current_dir == 'between_poezdka.json' or current_dir == 'info.xlsx':
                continue
            count += 1
            with open(f'drive/{id_driver}/{time_start_period}/{current_dir}/info.json', "r") as f:
                info_json = json.load(f)
                f.close()

            truck = get_number_name_color_truck(info_json['id_truck'])
            trailer = get_number_and_price_trailer(info_json['id_trailer'])

            plecho = 0

            raz_km = int(info_json['end_mileage']) - int(info_json['start_mileage'])
            if raz_km <= 150:
                plecho += 5000
            elif 150 < raz_km <= 200:
                plecho += 4500
            elif 200 < raz_km <= 250:
                plecho += 4000
            elif 250 < raz_km <= 300:
                plecho += 3500
            elif 300 < raz_km <= 350:
                plecho += 3000
            elif 350 < raz_km <= 400:
                plecho += 2500
            elif 400 < raz_km <= 450:
                plecho += 2000
            elif 450 < raz_km <= 500:
                plecho += 1500
            elif 500 < raz_km <= 550:
                plecho += 1000
            elif 550 < raz_km <= 600:
                plecho += 500

            price_1_km = trailer[1]

            # TODO сделать отображение за что получает надбавку
            s = float(get_one_param_db('s', chat_id))

            # За ширину
            if 3.5 <= s <= 4.0:
                price_1_km += 2
            elif 4.1 <= s <= 4.5:
                price_1_km += 4
            elif 4.51 <= s <= 5.0:
                price_1_km += 6
            elif 5.0 < s:
                price_1_km += 8

            # За высоту
            total_height = float(get_one_param_db('total_height', chat_id))
            if 4.51 <= total_height <= 5.0:
                price_1_km += 2
            elif 5.0 <= total_height:
                price_1_km += 4

            # За длину
            total_lenght = float(get_one_param_db('total_lenght', chat_id))
            if total_lenght > 30:
                price_1_km += 4
            elif total_lenght > 25:
                price_1_km += 2

            # За вес
            weight = float(get_one_param_db('weight', chat_id))
            if 33 <= weight <= 44:
                price_1_km += 2
            elif 45 <= weight <= 69:
                price_1_km += 10
            elif 70 < weight:
                price_1_km += 15

            info_excel = {"ФИО водителя": info_json['fio'],
                         "Номер водителя": info_json['phone'],
                         "Тягач": f"{truck[0]} {truck[1]} {truck[2]}",
                         "Полуприцеп": f"{trailer[0]}",
                         "Откуда - Куда": info_json['from_where'],
                         "Старт поездки": info_json['time_start_transit'],
                         "Конец поездки": info_json['time_end_transit'],
                         "Конец разгрузки": info_json['time_end_unload'],
                         "Тип поездки": info_json['type_drive'],
                         "Наименование груза": info_json['name_gruz'],
                         "Длина груза": info_json['d'],
                         "Ширина груза": info_json['s'],
                         "Высота груза": info_json['v'],
                         "Масса груза": info_json['weight'],
                         "Общая длина": info_json['total_lenght'],
                         "Общая высота": info_json['total_height'],
                         "Одометр начало": info_json['start_mileage'],
                         "Одометр конец": info_json['end_mileage'],
                         "Координаты старта": info_json['dot_start'],
                         "Координаты финиша": info_json['dot_end'],
                         "Заработал:": "",
                         "За км": f"{price_1_km * (raz_km)}",
                         "За плечо": plecho,
                         "Надбавки": ""
                         }
            all_price = int(info_excel['За км']) + int(info_excel['За плечо'])

            data = read_order()

            if id_driver in data.keys():
                for key in data[id_driver].keys():
                    if 'dop' in key:
                        info_excel[key.replace("dop ", "")] = data[id_driver][key]
                        all_price += int(data[id_driver][key])

            info_excel["Расходы"] = ""
            for key in info_json.keys():
                if '2dop' in key:
                    info_excel[key.replace("2dop ", "")] = info_json[key]
                    all_price += int(info_json[key])
                    all_razhod += int(info_json[key])
                elif '1dop' in key:
                    info_excel[key.replace("1dop ", "")] = info_json[key]
                    all_price += int(info_json[key])
                    all_razhod += int(info_json[key])
                elif 'dop' in key:
                    info_excel[key.replace("dop ", "")] = info_json[key]
                    all_price += int(info_json[key])
                    all_razhod += int(info_json[key])

            info_excel["Итого"] = all_price

            all_dohod += int(all_price)

            df1 = pd.DataFrame([info_excel]).transpose()

            if 'info.xlsx' not in os.listdir(f'drive/{id_driver}/{time_start_period}'):
                with pd.ExcelWriter(f'drive/{id_driver}/{time_start_period}/info.xlsx', mode='w') as writer:
                    try:
                        df1.to_excel(writer, sheet_name=current_dir, index=True)
                    except Exception as e:
                        print(e)
            else:
                # TODO сделать проверку, чтобы один раз только
                with pd.ExcelWriter(f'drive/{id_driver}/{time_start_period}/info.xlsx', mode='a') as writer:
                    try:
                        df1.to_excel(writer, sheet_name=current_dir, index=True)
                    except Exception as e:
                        print(e)
            all_json[count] = info_excel

        # between_poezdka.json

        between_poezdka = {}
        if 'between_poezdka.json' in os.listdir(f'drive/{id_driver}/{time_start_period}'):
            with open(f'drive/{id_driver}/{time_start_period}/between_poezdka.json', 'r') as file:
                between_poezdka = json.load(file)
                file.close()


        itog_excel = {"Заработал": "",
                      "Заработал итого": all_dohod,
                      "Расходы": "",
                      }
        # Ожидание погрузки
        # Выходные
        # Ремонт
        if len(between_poezdka) != 0:
            if 'Выходные' in between_poezdka:
                itog_excel[f"Выходные {between_poezdka['Выходные'][0]} дней"] = between_poezdka['Выходные'][1]
                all_razhod += int(between_poezdka['Выходные'][1])
            if 'Ожидание погрузки' in between_poezdka:
                itog_excel[f"Выходные {between_poezdka['Ожидание погрузки'][0]} дней"] = between_poezdka['Ожидание погрузки'][1]
                all_razhod += int(between_poezdka['Ожидание погрузки'][1])
            if 'Ремонт' in between_poezdka:
                itog_excel[f"Выходные {between_poezdka['Ремонт'][0]} дней"] = between_poezdka['Ремонт'][1]
                all_razhod += int(between_poezdka['Ремонт'][1])

        itog_excel['Расходы итого'] = all_razhod

        itog_excel['Полный итог'] = ''

        itog_excel['Итог'] = all_dohod + all_razhod

        itog_excel_df = pd.DataFrame([itog_excel]).transpose()
        with pd.ExcelWriter(f'drive/{id_driver}/{time_start_period}/info.xlsx', mode='a') as writer:
            try:
                itog_excel_df.to_excel(writer, sheet_name='Итог', index=True)
            except Exception as e:
                print(e)


        with open(f'drive/{id_driver}/{time_start_period}/all_itog.json', "w") as f:
            json.dump(all_json, f)
            f.close()

        os.rename(f'drive/{id_driver}/{time_start_period}', f'drive/{id_driver}/{time_start_period} - {time_end_period}')
        ex_update(f'UPDATE users SET time_start_period = NULL, stage = "new_period" WHERE telegram_id = {chat_id}')
        id_truck = get_one_param_db('id_truck', chat_id)
        ex_update(f'UPDATE trucks SET status = 0 WHERE id = {id_truck}')
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Новый период')
        await bot.send_message(chat_id, "Вы закончили период, нажмите чтобы начать новый", reply_markup=markup)
    elif text == 'Закончить добавление' and stage == 'end_photo_download1':
        ex_update(f"UPDATE users SET stage = 'end_photo_download' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Закончить добавление')
        await bot.send_message(chat_id, 'Отлично, теперь отправьте фото <b>ТТН</b> или нажмите закончить добавление', parse_mode='html')
    elif text == 'Закончить добавление' and stage == 'end_photo_download':
        ex_update(f"UPDATE users SET stage = 'doc_gruz' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Закончить добавление')
        await bot.send_message(chat_id, 'Отлично, теперь отправьте фото <b>ДОКУМЕНТОВ НА ГРУЗ</b> или нажмите закончить добавление\n(ПСМ, СТС, товарная накладная)', reply_markup=markup, parse_mode='html')
    elif text == 'Закончить добавление' and stage == 'doc_gruz':
        ex_update(f"UPDATE users SET stage = 'gruz_end' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Старт поездки')
        await bot.send_message(chat_id, 'Отлично, все фото загружены, нажмите на кнопку, когда начнёте поездку', reply_markup=markup)
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
    count_osi = get_one_param_db('count_osi', chat_id)
    count_ttn = get_one_param_db('count_ttn', chat_id)
    count_doc = get_one_param_db('count_doc', chat_id)
    if  'end_photo_download' in stage or stage == 'doc_gruz':
        if 'files' not in os.listdir(f'drive/{id}/{time_start_period}/{current_dir}'):
            os.mkdir(f'drive/{id}/{time_start_period}/{current_dir}/files')
        #     отправьте фото ТТН
        if stage == 'end_photo_download1':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Закончить добавление')
            await message.photo[-1].download(
                destination_file=f"drive/{id}/{time_start_period}/{current_dir}/files/Нагрузка на ось {count_osi}.jpg")
            ex_update(f"UPDATE users SET count_osi = count_osi + 1 WHERE telegram_id = {chat_id}")
            await bot.send_message(chat_id, 'Фото загружено, отправьте ещё фото <b>НАГРУЗКИ НА ОСЬ</b> или нажмите на кнопку "Закончить добавление"', reply_markup=markup, parse_mode='html')
        elif stage == 'end_photo_download':
            await message.photo[-1].download(destination_file=f"drive/{id}/{time_start_period}/{current_dir}/files/ТТН {count_ttn}.jpg")
            ex_update(f"UPDATE users SET count_ttn = count_ttn + 1 WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Закончить добавление')
            await bot.send_message(chat_id, 'Фото загружено, отправьте ещё фото <b>ТТН</b> или нажмите закончить добавление', reply_markup=markup, parse_mode='html')
        elif stage == 'doc_gruz':
            await message.photo[-1].download( destination_file=f"drive/{id}/{time_start_period}/{current_dir}/files/Доки груз {count_doc}.jpg")
            ex_update(f"UPDATE users SET count_doc = count_doc + 1 WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Закончить добавление')
            await bot.send_message(chat_id, 'Фото загружено, отправьте ещё фото <b>ДОКУМЕНТОВ НА ГРУЗ</b> или или нажмите закончить добавление\n(ПСМ, СТС, товарная накладная)', reply_markup=markup, parse_mode='html')
    elif stage == 'photo_gruz' and 0 <= count_photo_download <= 3:
        count_photo_download += 1
        ex_update(f"UPDATE users SET count_photo_download = count_photo_download + 1 WHERE telegram_id = {chat_id}")
        if 'photo_gruz' not in os.listdir(f'drive/{id}/{time_start_period}/{current_dir}'):
            os.mkdir(f'drive/{id}/{time_start_period}/{current_dir}/photo_gruz')
        await message.photo[-1].download(destination_file=f'drive/{id}/{time_start_period}/{current_dir}/photo_gruz/{count_photo_download}.jpg')
        if count_photo_download == 4:
            ex_update(f"UPDATE users SET stage = 'end_photo_download1' WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Закончить добавление')
            await bot.send_message(chat_id, 'Фото груза загружены, отправьте фото нагрузки на оси', reply_markup=markup)
    elif stage == 'get_done_ttn':
        await message.photo[-1].download(destination_file=f'drive/{id}/{time_start_period}/{current_dir}/files/Подписанная ТТН.jpg')

        all_data = get_all_obj(chat_id)
        id_driver = str(get_id_driver(chat_id))
        data = read_json_file(id_driver, time_start_period, current_dir)
        data1 = {**data, **all_data}
        write_json_file(id_driver, time_start_period, current_dir, data1)

        with open(f'drive/{id_driver}/{time_start_period}/{current_dir}/info.json', "r") as f:
            info_json = json.load(f)
            f.close()

        truck = get_number_name_color_truck(info_json['id_truck'])
        trailer = get_number_and_price_trailer(info_json['id_trailer'])

        plecho = 0

        raz_km = int(info_json['end_mileage']) - int(info_json['start_mileage'])
        if raz_km <= 150:
            plecho += 5000
        elif 150 < raz_km <= 200:
            plecho += 4500
        elif 200 < raz_km <= 250:
            plecho += 4000
        elif 250 < raz_km <= 300:
            plecho += 3500
        elif 300 < raz_km <= 350:
            plecho += 3000
        elif 350 < raz_km <= 400:
            plecho += 2500
        elif 400 < raz_km <= 450:
            plecho += 2000
        elif 450 < raz_km <= 500:
            plecho += 1500
        elif 500 < raz_km <= 550:
            plecho += 1000
        elif 550 < raz_km <= 600:
            plecho += 500

        price_1_km = trailer[1]

        s = float(get_one_param_db('s', chat_id))

        # За ширину
        za_shirina = 0
        if 3.5 <= s <= 4.0:
            za_shirina += 2
        elif 4.1 <= s <= 4.5:
            za_shirina += 4
        elif 4.51 <= s <= 5.0:
            za_shirina += 6
        elif 5.0 < s:
            za_shirina += 8

        price_1_km += za_shirina

        # За высоту
        za_visota = 0
        total_height = float(get_one_param_db('total_height', chat_id))
        if 4.51 <= total_height <= 5.0:
            za_visota += 2
        elif 5.0 <= total_height:
            za_visota += 4

        price_1_km += za_visota

        # За длину
        za_dlina = 0
        total_lenght = float(get_one_param_db('total_lenght', chat_id))
        if total_lenght > 30:
            za_dlina += 4
        elif total_lenght > 25:
            za_dlina += 2

        price_1_km += za_dlina

        # За вес
        za_ves = 0
        weight = float(get_one_param_db('weight', chat_id))
        if 33 <= weight <= 44:
            za_ves += 2
        elif 45 <= weight <= 69:
            za_ves += 10
        elif 70 < weight:
            za_ves += 15

        price_1_km += za_ves

        info_excel = {"ФИО водителя": info_json['fio'],
                      "Номер водителя": info_json['phone'],
                      "Тягач": f"{truck[0]} {truck[1]} {truck[2]}",
                      "Полуприцеп": f"{trailer[0]}",
                      "Откуда - Куда": info_json['from_where'],
                      "Старт поездки": info_json['time_start_transit'],
                      "Конец поездки": info_json['time_end_transit'],
                      "Конец разгрузки": info_json['time_end_unload'],
                      "Тип поездки": info_json['type_drive'],
                      "Наименование груза": info_json['name_gruz'],
                      "Длина груза": info_json['d'],
                      "Ширина груза": info_json['s'],
                      "Высота груза": info_json['v'],
                      "Масса груза": info_json['weight'],
                      "Общая длина": info_json['total_lenght'],
                      "Общая высота": info_json['total_height'],
                      "Одометр начало": info_json['start_mileage'],
                      "Одометр конец": info_json['end_mileage'],
                      "Координаты старта": info_json['dot_start'],
                      "Координаты финиша": info_json['dot_end'],
                      "Заработал:": "",
                      "За км": f"{price_1_km * (raz_km)}",
                      "За плечо": plecho,
                      "Надбавки": ""
                      }

        all_price = int(info_excel['За км']) + int(info_excel['За плечо'])

        data = read_order()

        nadbavki_string = ''
        nadbavki_digit = 0

        dop_razhod_road_string = ''
        dop_razhod_road_digit = 0

        dop_razhod_razgruz_string = ''
        dop_razhod_razgruz_digit = 0

        if id_driver in data.keys():
            for key in data[id_driver].keys():
                if 'dop' in key:
                    info_excel[key.replace("dop ", "")] = data[id_driver][key]
                    all_price += int(data[id_driver][key])

                    info_excel[key.replace("dop ", "")] = data[id_driver][key]
                    nadbavki_string += f'{key.replace("dop ", "")} = {data[id_driver][key]}\n'
                    nadbavki_digit += int(data[id_driver][key])

        info_excel["Расходы"] = ""
        for key in info_json.keys():
            if '2dop' in key:
                # Разгрузка
                info_excel[key.replace("2dop ", "")] = info_json[key]
                all_price += int(info_json[key])
                dop_razhod_razgruz_string += f'{key.replace("2dop ", "")} = {info_json[key]}\n'
                dop_razhod_razgruz_digit += int(info_json[key])
            elif '1dop' in key:
                # Доп условия
                info_excel[key.replace("1dop ", "")] = info_json[key]
                all_price += int(info_json[key])
                dop_razhod_road_string += f'{key.replace("1dop ", "")} = {info_json[key]}\n'
                dop_razhod_road_digit += int(info_json[key])
            elif 'dop' in key:
                # Надбавки
                info_excel[key.replace("dop ", "")] = info_json[key]
                nadbavki_string += f'{key.replace("dop ", "")} = {info_json[key]}\n'
                nadbavki_digit += int(info_json[key])
                all_price += int(info_json[key])

        info_excel["Итого"] = all_price


        df1 = pd.DataFrame([info_excel]).transpose()

        if 'info.xlsx' not in os.listdir(f'drive/{id_driver}/{time_start_period}'):
            with pd.ExcelWriter(f'drive/{id_driver}/{time_start_period}/{current_dir}/info.xlsx', mode='w') as writer:
                try:
                    df1.to_excel(writer, sheet_name=f'Итог {current_dir}', index=True)
                except Exception as e:
                    print(e)
        else:
            # TODO сделать проверку, чтобы один раз только
            with pd.ExcelWriter(f'drive/{id_driver}/{time_start_period}/{current_dir}/info.xlsx', mode='a') as writer:
                try:
                    df1.to_excel(writer, sheet_name=f'Итог {current_dir}', index=True)
                except Exception as e:
                    print(e)

        check = f"""Ваш чек\n\n1) За километраж = {info_excel['За км']}\n1 км = {price_1_km}\nИз них:\nЗа высоту: {za_visota}\nЗа длину: {za_dlina}\nЗа ширину: {za_shirina}\nЗа вес: {za_ves}\n\n2)Надбвака за плечо: {plecho}\n\n3)Надбавки:\n{nadbavki_string}\n4)Доп. расходы в пути:\n{dop_razhod_road_string}\n5)Доп. расходы при разгрузке:\n{dop_razhod_razgruz_string}\n\nРасходы: {dop_razhod_road_digit + dop_razhod_razgruz_digit}\n\nЗаработано: {info_excel['За км'] + nadbavki_digit + plecho}"""

        data = read_order()
        if id_driver in data.keys():
            del data[id_driver]
            write_order(data)
        ex_update(f"UPDATE users SET stage = 'end_poezdka', active = 0, count_osi = 1, count_ttn = 1, count_doc = 1, porog = 0 WHERE telegram_id = {chat_id}")
        
        await bot.send_message(chat_id, check, parse_mode='html')

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Начать перевозку')
        markup.add('Закончить период')
        markup.add('Между поездками')

        await bot.send_message(chat_id, 'Выберите чем будете заниматься дальше', reply_markup=markup)
        # TODO добавить отдых и тд
       
    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')


@dp.message_handler(content_types='document')
async def file_handler(message):
    chat_id = message.chat.id
    stage = ex_get_stage(chat_id)
    # time_start_period = get_one_param_db('time_start_period', chat_id)
    if stage == 'pred_drivers_edit':
        if document := message.document:
            id_driver = get_one_param_db("d", chat_id)
            period = get_one_param_db("s", chat_id)
            poezdka = get_one_param_db("v", chat_id)
            await document.download(destination_file=f"drive/{id_driver}/{period}/{poezdka}/edit_info.xlsx")
            ex_update(f"UPDATE users SET stage = 'end_edit_pred_drivers' WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Вернуться в меню")
            await bot.send_message(chat_id, 'Отлично, вы изменили excel файл', reply_markup=markup)
        else:
            await bot.send_message(chat_id, 'С файлом что-то не так')
    if stage == 'select_where_order':
        help_id_truck = get_one_param_db('help_id_truck', chat_id)
        if document := message.document:
            await document.download(destination_file=f"excel/{help_id_truck}.xlsx")
            # Чтение данных из Excel файла
            df = pd.read_excel(f"excel/{help_id_truck}.xlsx", header=None, names=['key', 'value'])

            # Преобразование DataFrame в словарь
            dict_data = dict(zip(df['key'], df['value']))

            new_data = {}
            for key, value in dict_data.items():
                if str(key) != 'nan' and str(value) != 'nan':
                    # if key in  , , ,
                    #                }:
                    if key == 'Откуда - Куда':
                        new_data[f'from_where_to_where'] = value
                    elif key == 'Имя груза':
                        new_data[f'name_gruz'] = value
                    elif key == 'Длина груза':
                        new_data[f'dhv'] = f'{value} {dict_data["Ширина груза"]} {dict_data["Высота груза"]}'
                    elif key == 'Вес груза':
                        new_data[f'weight'] = value
                    elif key == 'Ширина груза' or key == 'Высота груза':
                        pass
                    else:
                        new_data[f'dop {key}'] = value

            data = read_order()
            data[str(help_id_truck)] = new_data
            write_order(data)
            os.remove(f"excel/{help_id_truck}.xlsx")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Вернуться в меню')
            await bot.send_message(chat_id, "Заявка успешно создана", reply_markup=markup)
        else:
            await bot.send_message(chat_id, 'С файлом что-то не так')


    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')


@dp.message_handler(content_types='location')
async def location_handler(message):
    chat_id = message.chat.id
    stage = ex_get_stage(chat_id)
    geo = f"{message['location']['latitude']} {message['location']['longitude']}"
    if stage == 'dot_start1':
        ex_update(f"UPDATE users SET stage = 'dot_start2', dot_start = '{geo}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        porog = get_one_param_db('porog', chat_id)
        if porog == 0:
            id_driver = str(get_one_param_db('id', chat_id))
            data = read_order()
            if id_driver in data.keys():
                markup.add(data[id_driver]['name_gruz'])
            markup.add('Вернуться к вводу координат')
            await bot.send_message(chat_id, "Введите <b>название груза</b>", reply_markup=markup, parse_mode='html')
        else:
            ex_update(f"UPDATE users SET stage = 'end_photo_download1' WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Закончить добавление')
            await bot.send_message(chat_id, 'Отправьте фото нагрузки на оси', reply_markup=markup)
    elif stage == 'get_koor_finish':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться к вводу координат финиша')
        ex_update(f"UPDATE users SET stage = 'end_mileage_km', dot_end = '{geo}' WHERE telegram_id = {chat_id}")
        await bot.send_message(chat_id, 'Введите данные с одометра одним число без пробелов', reply_markup=markup)
    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')



executor.start_polling(dp, skip_updates=True)
