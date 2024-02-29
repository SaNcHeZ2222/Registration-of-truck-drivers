import sqlite3

connection = sqlite3.connect('base.db')
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_auto TEXT,
    number TEXT,
    status INTEGER DEFAULT 0,
    price_1_km INTEGER DEFAULT 0,
    weight_avto BIGINT DEFAULT 0
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT,
    stage TEXT,
    fio TEXT,
    phone TEXT,
    id_truck BIGINT,
    from_where TEXT,
    time_start_period TEXT DEFAULT NULL,
    current_dir TEXT,
    type_drive TEXT,
    start_mileage BIGINT,
    dot_start TEXT,
    d TEXT,
    s TEXT,
    v TEXT,
    weight TEXT,
    count_photo_download INTEGER DEFAULT 0,
    dot_end TEXT,
    end_mileage BIGINT,
    empty_race INTEGER DEFAULT 0
)""")

# Уточнить у Фила, вес участвует в подсчёте формул?
cursor.execute("""INSERT INTO trucks(name_auto, number, price_1_km, weight_avto) VALUES ('Первый трак', 'y222yy77', 12, 33)""")

# print(*cursor.execute('SELECT time_start_period FROM users WHERE telegram_id = 703194398'))


connection.commit()
connection.close()