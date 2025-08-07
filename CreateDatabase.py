import sqlite3

conn = sqlite3.connect('Databases/Posts.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS Posts (id INTEGER PRIMARY KEY, owner TEXT, users_to TEXT, content TEXT)')
# cursor.execute('DELETE FROM Posts')
conn.commit()
conn.close()