import sqlite3

conn = sqlite3.connect('audio_player.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    genre TEXT UNIQUE NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Audio_Library (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        genre INTEGER,
        duration INTEGER NOT NULL,
        image_path TEXT,
        audio_path TEXT NOT NULL
)
''')

conn.commit()
conn.close()
