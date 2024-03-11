import zipfile
from other_func import *
from config import token
import os
import datetime
import json
import pandas
import shutil

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
        # TODO сделать проверку на номер, что админ тоже зарегался
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
    # TODO сделать проверку, что можешь что-то сделать | phone != NULL
    # if chat_id: 
    #     return
    # Регистрация
    # TODO сделать удаление заявки
    # TODO сделать просмотр заявки
    
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
        list_dir_period = os.listdir(f'drive/{id_driver}')
        for i in list_dir_period:
            markup.add(i)
        markup.add('Вернуться в меню')
        ex_update(f'UPDATE users SET stage = "pred_drivers_period", d = "{id_driver}" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, 'Выберите период', reply_markup=markup)
    elif stage == 'pred_drivers_period':
        period = text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        id_driver = get_one_param_db('d', chat_id)
        list_dir_poezdka = os.listdir(f'drive/{id_driver}/{period}')
        for i in list_dir_poezdka:
            markup.add(i)
        markup.add('Вернуться в меню')
        ex_update(f'UPDATE users SET stage = "pred_drivers_poezdka", s = "{period}" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, 'Выберите поездку', reply_markup=markup)
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
        markup.add('Добавить условия')
        markup.add('Удалить условия')
        # markup.add('Премия дополнительная: 5000')
        # markup.add('Добавить своё условие')
        
        await bot.send_message(chat_id, 'Добавьте условия или удалите', reply_markup=markup)
    elif stage == 'dop_uslovia' and text == 'Добавить условия':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Премия дополнительная: 5000')
        markup.add('Добавить своё условие')
        markup.add('Закончить добавку условий')
        ex_update(f'UPDATE users SET stage = "dop_uslovia_add" WHERE telegram_id = {chat_id}')
        await bot.send_message(chat_id, 'Нажмите на условия, чтобы добавить', reply_markup=markup)
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
    elif stage == 'dop_uslovia_add':
        if text == 'Добавить своё условие':
            ex_update(f'UPDATE users SET stage = "dop_uslovia_add_new" WHERE telegram_id = {chat_id}')
            await bot.send_message(chat_id, "Напишите новое название условия")
        else:
            if text == 'Закончить добавку условий':
                ex_update(f'UPDATE users SET stage = "main" WHERE telegram_id = {chat_id}')
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add('Создать заявку')
                markup.add('Активные поездки')
                markup.add('Предыдущие поездки')
                markup.add('Вопросы')
                await bot.send_message(chat_id, 'Вы завершили добавку условий', reply_markup=markup)
            else:
                id_driver = get_one_param_db('active', chat_id)
                active_session = sorted(os.listdir(f'drive/{id_driver}'), reverse=True)[0]
                active_dir = sorted(os.listdir(f'drive/{id_driver}/{active_session}'), key=lambda x: os.path.getctime(f'drive/{id_driver}/{active_session}'), reverse=True)[0]
                data = read_json_file(id_driver, active_session, active_dir)
                data[f"dop {text.split(':')[0]}"] = text.split(':')[1]
                write_json_file(id_driver, active_session, active_dir, data)
                await bot.send_message(chat_id, f'Вы добавили {text}')
        # TODO сделать оптравку текущих
    elif chat_id in admin and (stage == 'main' or stage == 'start_registration' or stage == 'end_registration') and text == 'Создать заявку':
        
        connection = sqlite3.connect('base.db', check_same_thread=True)
        cursor = connection.cursor()

        all_id_drivers = {f'{i[0]} {i[1]}' for i in cursor.execute('SELECT id, fio FROM users')}

        connection.commit()
        connection.close()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in all_id_drivers:
            markup.add(i)
        #  {id: {parametrs}}
        # TODO убрать 
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
        await bot.send_message(chat_id, 'Введите откуда - куда должен поехать водитель', reply_markup=markup)
    elif stage == 'select_where_order':
        id_help = get_one_param_db('help_id_truck', chat_id)
        data = read_order()

        data[id_help]['from_where_to_where'] = text

        write_order(data)

        ex_update(f'UPDATE users SET stage = "select_where_order1" WHERE telegram_id = {chat_id}')
        
        await bot.send_message(chat_id, 'Введите координаты или нажмите 0\nПример: 55.2331 28.2221')
        # TODO сделать обработку нуля 
        # TODO сделать финиш
    elif stage == 'select_where_order1':
        id_help = get_one_param_db('help_id_truck', chat_id)
        data = read_order()

        data[id_help]['coordinates'] =  text

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
            markup = types.ReplyKeyboardRemove()
            await bot.send_message(chat_id, 'Вы завершили создание заявки', reply_markup=markup)
        else:
            id_help = get_one_param_db('help_id_truck', chat_id)

            data = read_order()
            
            data[id_help][f'dop {text}'] = int(text.split(':')[-1])
            
            write_order(data)
            await bot.send_message(chat_id, f'Вы добавили {text}')

    # Главное меню и выбор авто
    elif ((stage == 'end_registration' or stage == 'main') and text == 'Выбрать авто') or (stage == 'new_period' and text == 'Начать период') or (stage == 'go_per' and text == "Вернуться к выбору авто"):
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
            markup.add("Вернуться к выбору авто")
            await bot.send_message(chat_id, f'Вы выбрили: {text}', reply_markup=markup)
        else:
            # TODO кнопка поддержки
            await bot.send_message(chat_id, 'Нет такого авто в списке, напиши в тех поддержку')
    # Начать поездку
    elif (stage == 'go_per' and text == 'Начать период') or (text == 'Начать перевозку' and stage == 'end_poezdka') or (text == 'Вернуться к пункту "Откуда - Куда"' and stage == 'type_drive1'):
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
        await bot.send_message(chat_id, "Выберите откуда - куда или напишите", reply_markup=markup)
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
        # markup.add("Заявка от логиста, пока не работает кнопка")
        markup.add('Вернуться к пункту "Откуда - Куда"')
        await bot.send_message(chat_id, 'Выберите тип поездки', reply_markup=markup)
        # TODO Порожний перегон
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
        # TODO Сделать проверка на ввод числа, если не так, то заново просить вписать
        # TODO сделать порожний перегон
    elif stage == 'start_mileage' or (text == 'Вернуться к вводу координат' and stage == 'd'):
        if text.isdigit() or text == 'Вернуться к вводу координат':
            if text != 'Вернуться к вводу координат':
                ex_update(f"UPDATE users SET stage = 'dot_start1', start_mileage = {int(text)} WHERE telegram_id = {chat_id}")
            else:
                ex_update(f"UPDATE users SET stage = 'dot_start1' WHERE telegram_id = {chat_id}")
            id_driver = str(get_one_param_db('id', chat_id))
            data = read_order()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            if id_driver in data.keys() and data[id_driver]['from_where_to_where'] != '0':
                markup.add(data[id_driver]['from_where_to_where'])
            markup.add('Вернуться к вводу данных с одометра')
            await bot.send_message(chat_id, 'Введите координаты (из яндекс карт) или нажмите на кнопку подсказки от логиста', reply_markup=markup)

        else:
            await bot.send_message(chat_id, "Вы ввели число некоректно, попробуйте ещё раз")
    elif stage == 'dot_start1' or (text == 'Вернуться к вводу длины' and stage == 's'):
        if text != 'Вернуться к вводу длины':
            ex_update(f"UPDATE users SET stage = 'd', dot_start = '{text}' WHERE telegram_id = {chat_id}")
        else:
            ex_update(f"UPDATE users SET stage = 'd' WHERE telegram_id = {chat_id}")
        id_driver = str(get_one_param_db('id', chat_id))
        data = read_order()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        if id_driver in data.keys():
            markup.add(data[id_driver]['dhv'].split()[0])
        markup.add('Вернуться к вводу координат')
        await bot.send_message(chat_id, "Введите <b>длину</b> в метрах и сантиметры через точку, например 11 метров 25 см будет 11.25", reply_markup=markup, parse_mode='html')
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
        await bot.send_message(chat_id, "Введите <b>ширину</b> в метрах и сантиметры через точку, например 11 метров 25 см будет 11.25", reply_markup=markup, parse_mode='html')
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
        await bot.send_message(chat_id, "Введите <b>высоту</b> в метрах и сантиметры через точку, например 11 метров 25 см будет 11.25", reply_markup=markup, parse_mode='html')
    elif stage == 'v' or (text == 'Вернуться к вводу веса' and stage == 'photo_gruz'):
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
        await bot.send_message(chat_id, "Введите вес в тоннах через точку, например 12т512кг ->12.512 или нажмите на кнопку от логиста", reply_markup=markup)
    elif stage == 'weight':
        # TODO сделать проверку на ввод веса в тоннах через точку
        ex_update(f"UPDATE users SET stage = 'photo_gruz', weight = '{text}' WHERE telegram_id = {chat_id}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Вернуться к вводу веса')
        await bot.send_message(chat_id, "<b>Внимание вернуться к отправке фото нельзя, выбирайте фото внимательно!\n\n</b>Отправьте одним альбомом 4 фотографии груза", reply_markup=markup, parse_mode='html')
        # TODO сделать вернуться к вводу фото, нах не надо
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
    elif (stage == 'in_transit' and text == 'ПРИБЫЛ НА МЕСТО РАЗГРУЗКИ') or (text == 'Вернуться к вводу координат финиша' and stage == 'end_mileage_km'):
        if (text != 'Вернуться к вводу координат финиша'):
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
        # TODO надо ли делать подсказку
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
            ex_update(f"UPDATE users SET stage = 'info_unload', end_mileage = {text} WHERE telegram_id = {chat_id}")
            markup.add('Пропустить')
            await bot.send_message(chat_id, 'Отправьте данные о разгурке', reply_markup=markup)
            # TODO какие нах данные? хахахахах
        else:
            await bot.send_message(chat_id, 'Вы ввели число неправильно, введите число без пробелов и точек', reply_markup=markup)
    elif stage == 'info_unload':
        if text != 'Пропустить':
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
        id_driver = str(get_one_param_db('id', chat_id))
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
        id_driver = str(get_id_driver(chat_id))
        data = read_json_file(id_driver, time_start_period, current_dir)
        data1 = {**data, **all_data}
        write_json_file(id_driver, time_start_period, current_dir, data1)
        # TODO переименовать строки короче
        pandas.DataFrame(data1, index=[0]).transpose().to_excel(f'drive/{id_driver}/{time_start_period}/{current_dir}/info.xlsx')
        all_price = 0
        id_truck = get_id_truck(chat_id)
        price_1_km = get_one_param_truks('price_1_km', int(id_truck))
        one_krit = ''
        if price_1_km == 12:
            one_krit = 'Площадка 0,9 до 4х осей или Корыто до 3 осей -> <b>12 руб за 1 км</b>'
        elif price_1_km == 14:
            one_krit = '5, 6, 7 оснвые + корыто от 4 осей -> <b>14 руб за 1 км</b>'
        # TODO добавить изменение числа суточных через excel
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
        dop = ''
        data = read_order()

        two_krit = f'Надбавка за плечо -> <b>{all_price}</b>'

        flag_dop = 0
        if id_driver in data.keys():
            for key in data[id_driver].keys():
                if 'dop' in key:
                    flag_dop = 1
                    dop += f'{key.replace("dop ", "")}; '
                    all_price += data[id_driver][key]
        for key in data1.keys():
            if 'dop' in key:
                flag_dop = 1
                dop += f'{key.replace("dop ", "")} = {data1[key]}\n'
                all_price += int(data1[key])
        
        # TODO сделать заявку только неактивному пользователю
        # TODO сделать возврат к предыдущему шагу 
        # TODO сделать активный пользователь или нет
        # TODO добавить дополнительно денег

        total = price_1_km * raz_km + all_price

        if flag_dop and one_krit:
            s = f'1) {one_krit} = <b>{price_1_km * raz_km}</b>\n2) {two_krit}\n3) Дополнительный надбавки от логиста: \n<b>{dop}</b>\n\nИтоговая сумма без дополнительных условий: <b>{total}</b>'
        elif one_krit:
            s = f'1) {one_krit} = <b>{price_1_km * raz_km}</b>\n2) {two_krit}\n\nИтоговая сумма без дополнительных условий: <b>{total}</b>'
        elif flag_dop:
            s = f'1) Цена за поездку (дорога) = <b>{price_1_km * raz_km}</b>\n2) {two_krit}\n3) Дополнительный надбавки от логиста: \n<b>{dop}</b>\n\nИтоговая сумма без дополнительных условий: <b>{total}</b>'
        else:
            s = f'1) Цена за поездку (дорога) = <b>{price_1_km * raz_km}</b>\n2) {two_krit}\n\nИтоговая сумма без дополнительных условий: <b>{total}</b>'
        data = read_order()
        if id_driver in data.keys():
            del data[id_driver]
            write_order(data)
        ex_update(f"UPDATE users SET stage = 'end_poezdka', active = 0 WHERE telegram_id = {chat_id}")
        
        await bot.send_message(chat_id, f'Ваш чек\n{s}', parse_mode='html')
        await bot.send_message(chat_id, 'Выберите что будете заниматься дальше', reply_markup=markup)
        # TODO добавить отдых и тд
       
    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')


#
@dp.message_handler(content_types='document')
async def file_handler(message):
    chat_id = message.chat.id
    stage = ex_get_stage(chat_id)
    time_start_period = get_one_param_db('time_start_period', chat_id)
    if stage == 'pred_drivers_edit':
        if document := message.document:
            id_driver = get_one_param_db("d", chat_id)
            period = get_one_param_db("s", chat_id)
            poezdka = get_one_param_db("v", chat_id)
            await document.download(destination_file=f"drive/{id_driver}/{period}/{poezdka}/edit_info.xlsx")
            ex_update(f"UPDATE users SET stage = 'end_edit_pred_drivers' WHERE telegram_id = {chat_id}")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('')
            await bot.send_message(chat_id, 'Отлично, вы изменили excel файл', reply_markup=markup)
    else:
        await bot.send_message(chat_id, 'Не знаю что ответить')


# @dp.message_handler(content_types='location')
# async def location_handler(message):
#     print(message)
    # TODO сделать локацию


executor.start_polling(dp, skip_updates=True)
