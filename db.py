import sqlite3

connection = sqlite3.connect('base.db')
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS trucks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_auto TEXT,
    number TEXT,
    status INTEGER DEFAULT 0
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT,
    stage TEXT,
    fio TEXT,
    phone TEXT,
    id_truck BIGINT,
    from_where TEXT,
    type_drive TEXT,
    start_mileage BIGINT,
    dot_start TEXT,
    dhv TEXT
)""")


cursor.execute("""INSERT INTO trucks(name_auto, number) VALUES ('Первый трак', 'y222yy77')""")


connection.commit()
connection.close()
