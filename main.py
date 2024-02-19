from aiogram import *
import sqlite3
from other_func import *

token = '6354386644:AAGAlxB1oPyLvuuxPsb8TfP7FO_M7X1rf1U'

bot = Bot(token)
dp = Dispatcher(bot)

admin = [703194398]


@dp.message_handler(commands='start')
async def start_message(message: types.Message):
    chat_id = message.chat.id

    # connection = sqlite3.connect('my_database.db', check_same_thread=True)
    # cursor = connection.cursor()

    # all_chat = {i[0] for i in cursor.execute('SELECT telegram_id FROM users')}

    # connection.commit()
    # connection.close()
    # if "first_name" in message['from']:
    #     first_name = message['from']['first_name']
    # else:
    #     first_name = None

    # if chat_id not in all_chat:

    #     if 'username' in message['from']:
    #         username = message['from']['username']
    #         connection = sqlite3.connect(
    #             'my_database.db', check_same_thread=True)
    #         cursor = connection.cursor()

    #         cursor.execute(f"INSERT INTO users(telegram_id, stage, username, first_name) VALUES ({chat_id}, 'main', '@{username}', '{first_name}')")

    #         connection.commit()
    #         connection.close()
    #     else:
    #         connection = sqlite3.connect(
    #             'my_database.db', check_same_thread=True)
    #         cursor = connection.cursor()

    #         cursor.execute(f"INSERT INTO users(telegram_id, stage, first_name) VALUES ({chat_id}, 'main', '{first_name}')")

    #         connection.commit()
    #         connection.close()
            
    #     connection = sqlite3.connect('my_database.db', check_same_thread=True)
    #     cursor = connection.cursor()

    #     all_id = max({i[0] for i in cursor.execute('SELECT id FROM users')})
    #     for i in admin:
    #         await bot.send_message(i, f'Новый пользователь с номером: {all_id}')

    #     connection.commit()
    #     connection.close()
    # else:
    #     ex_update(f"UPDATE users SET stage = 'main' WHERE telegram_id = {chat_id}")

        

    # markup = get_start_markup()
    # text = message['from']['first_name'] + open('messages/start_message.txt', 'r').read()
    # await bot.send_message(chat_id, text, reply_markup=markup)


@dp.message_handler(content_types='text')
async def text_handler(message: types.Message):
    chat_id = message.chat.id

    stage = ex_get_stage(chat_id)
    
executor.start_polling(dp, skip_updates=True)
