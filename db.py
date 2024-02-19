import sqlite3

connection = sqlite3.connect('my_database.db')
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT,
    stage TEXT,
    pole1 TEXT,
    pole2 TEXT,
    pole3 TEXT,
    pole4 TEXT,
    pole5 TEXT,
    first_name TEXT,
    username TEXT,
    phone TEXT
)""")


connection.commit()
connection.close()
