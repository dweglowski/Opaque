import sqlite3


def clear_database(database_name):
    conn = sqlite3.connect(f'Databases/{database_name}.db')
    cursor = conn.cursor()

    cursor.execute(f'DELETE FROM {database_name}')

    conn.commit()
    conn.close()

clear_database('Posts')
clear_database('Logins')
clear_database('Profiles')
clear_database('Connections')
clear_database('Messages')
clear_database('Analytics')
clear_database('CryptographyKeys')