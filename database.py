# database.py
import psycopg2
from psycopg2.extras import RealDictCursor

from config import DB_CONFIG


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_dict_cursor_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn, conn.cursor(cursor_factory=RealDictCursor)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create tables
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            birth_year DATE,
            age INTEGER
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS books (
            book_id SERIAL PRIMARY KEY,
            title VARCHAR NOT NULL,
            title_without_series VARCHAR,
            mod_title VARCHAR,
            isbn VARCHAR,
            language_code VARCHAR,
            publication_year DATE,
            rating_count INTEGER DEFAULT 0,
            average_rating FLOAT DEFAULT 0,
            authors TEXT[],
            cover_image_url VARCHAR
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_book_ratings (
            user_id INTEGER REFERENCES users(user_id),
            book_id INTEGER REFERENCES books(book_id),
            rated_date DATE DEFAULT CURRENT_DATE,
            PRIMARY KEY (user_id, book_id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS listed_books (
            user_id INTEGER REFERENCES users(user_id),
            book_id INTEGER REFERENCES books(book_id),
            listed_date DATE DEFAULT CURRENT_DATE,
            PRIMARY KEY (user_id, book_id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS requested_books (
            user_id INTEGER REFERENCES users(user_id),
            book_id INTEGER REFERENCES books(book_id),
            requested_date DATE DEFAULT CURRENT_DATE,
            PRIMARY KEY (user_id, book_id)
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()