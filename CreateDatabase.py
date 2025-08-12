import sqlite3

# conn = sqlite3.connect('Databases/Posts.db')
# conn = sqlite3.connect('Databases/Logins.db')
conn = sqlite3.connect('Databases/Profiles.db')
cursor = conn.cursor()
# cursor.execute('CREATE TABLE IF NOT EXISTS Posts (id INTEGER PRIMARY KEY, owner TEXT, users_to TEXT, content TEXT)')
# cursor.execute('DELETE FROM Posts')
# cursor.execute('CREATE TABLE IF NOT EXISTS Logins (username TEXT PRIMARY KEY, password_hash TEXT, password_salt TEXT)')
# cursor.execute('DELETE FROM Logins')
# cursor.execute('CREATE TABLE IF NOT EXISTS Profiles (username TEXT PRIMARY KEY, displayname TEXT, bio TEXT, photoid TEXT)')
# cursor.execute('DELETE FROM Profiles')
conn.commit()
conn.close()