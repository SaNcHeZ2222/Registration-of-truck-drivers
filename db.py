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
    d TEXT DEFAULT 0,
    s TEXT DEFAULT 0,
    v TEXT DEFAULT 0,
    weight TEXT DEFAULT 0,
    count_photo_download INTEGER DEFAULT 0,
    dot_end TEXT,
    end_mileage BIGINT,
    empty_race INTEGER DEFAULT 0,
    active int DEFAULT 0,
    help_id_truck TEXT,
    name_dop_razhod TEXT,
    price_dop_razhod TEXT,
    name_gruz TEXT,
    total_lenght TEXT DEFAULT 0,
    total_height TEXT DEFAULT 0,
    mega_dop_name TEXT,
    count_osi INTEGER DEFAULT 1,
    count_ttn INTEGER DEFAULT 1,
    count_doc INTEGER DEFAULT 1,
    porog INTEGER DEFAULT 0,
    remont_day TEXT,
    remont_price TEXT,
    weekend_day TEXT,
    weekend_price TEXT,
    waiting_loading_day TEXT,
    waiting_loading_price TEXT
)""")

cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Volvo', 'Желтый', 'С203УВ178')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Scania', 'Белый', 'М103ВА98')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('DAF', 'Оранжевый', 'Е126ТВ178')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Renault', 'Белый', 'Р112ОМ198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('DAF', 'Белый', 'В011ВР198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('DAF', 'Белый', 'А215КО198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Mercedes', 'Белый', 'В560МВ198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Renault', 'Белый', 'Р344АХ198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Iveco', 'Белый', 'М631РС198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Volvo', 'Красный', 'К019ВС198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Renault', 'Белый', 'В745УУ198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Volvo', 'Желтый', 'К171ХВ82')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Volvo', 'Красный', 'Х504ТУ178')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Volvo', 'Оранжевый', 'К855НА198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Volvo', 'Красный', 'В504ВН198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Volvo', 'Красный', 'Х586ТУ178')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Volvo', 'Красный', 'В654УМ198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Renault', 'Белый', 'Р027ТР198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Sitrac', 'Желтый', 'Р033УТ198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Sitrac', 'Синий', 'Н917ВС198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Sitrac', 'Белый', 'Н540ВХ198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Sitrac', 'Синий', 'Н079ВХ198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('MAN', 'Желтый', 'Е024ВУ198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Sitrac', 'Синий', 'С090АТ198')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('MAN', 'Белый', 'К043АК147')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Scania', 'Красный', 'О759ЕТ196')")
cursor.execute("INSERT INTO trucks(name_auto, number, color) VALUES ('Scania', '', 'О713КА196')")

cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВК895378', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('АТ046247', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВН713378', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВУ055178', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВУ185278', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВУ079578', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВР647378', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВУ446478', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВХ430778', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВР900878', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВР650178', '14')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВХ145478', '14')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВУ079478', '14')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВХ147378', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВХ848878', '14')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВУ179478', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВУ502678', '14')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВХ430878', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВР045178', '14')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВВ918978', '14')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВР681878', '14')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВХ363878', '14')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВВ118778', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВХ848978', '14')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВА919078', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ВН210778', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ЕА208366', '12')")
cursor.execute("INSERT INTO trailer(number_trailer, price_1_km) VALUES ('ЕА273866', '12')")


# TODO Масса груза ->  цена на км
# TODO Длина и высота автопоезда -> надбавка

# TODO сделать добавление водителей в список


# TODO Простой - сколько дней и с какого числа по какое - простой стоит 1200 пойдёт в общую excel периода
# TODO Ремонт тоже самое



connection.commit()
connection.close()
