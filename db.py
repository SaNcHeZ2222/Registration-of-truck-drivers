import sqlite3

connection = sqlite3.connect('base.db')
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_auto TEXT,
    number TEXT,
    status INTEGER DEFAULT 0,
    color TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS trailer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number_trailer TEXT,
    price_1_km INTEGER DEFAULT 0
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT,
    stage TEXT,
    fio TEXT,
    phone TEXT,
    id_truck BIGINT,
    id_trailer BIGINT, 
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
    empty_race INTEGER DEFAULT 0,
    active int DEFAULT 0,
    help_id_truck TEXT,
    name_dop_razhod TEXT,
    price_dop_razhod TEXT,
    name_gruz TEXT,
    total_lenght TEXT,
    total_height TEXT
)""")

# Уточнить у Фила, вес участвует в подсчёте формул?
cursor.execute("""INSERT INTO trucks(name_auto, number, color) VALUES ('Первый трак', 'y222yy77', 'Серебристый')""")

cursor.execute("""INSERT INTO trucks(name_auto, number, color) VALUES ('Второй трак', 'а123аа164', 'Чёрный')""")

cursor.execute("""INSERT INTO trailer(number_trailer, price_1_km) VALUES ('35471648512846', '12')""")


# TODO Масса груза ->  цена на км
# TODO Длина и высота автопоезда -> надбавка

# print(*cursor.execute('SELECT time_start_period FROM users WHERE telegram_id = 703194398'))

# имя и цена

# TODO сделать добавление водителей в список

# -------------------------------------------------------
# Хз надо сделать

# TODO сделать возврат после прибытия на место разгрузки
# -------------------------------------------------------


# TODO Простой - сколько дней и с какого числа по какое - простой стоит 1200 пойдёт в общую excel периода
# TODO Ремонт тоже самое

# TODO общая excel все поездки туда все условия и общий прайс



# -------------------------------------------------
# TODO сделал, но не тестил

# TODO вместо форс-мажоров и тд, кнопка добавить статью расходов
# TODO имя груза перед параметрами груза
# TODO нужно выбирать не трак, а отдельно тягач полуприцеп



# гос номер

connection.commit()
connection.close()
