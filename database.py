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
            birth_year DATE NOT NULL,
            password_encrypted VARCHAR NOT NULL,
            age INT NOT NULL
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS books (
            book_id SERIAL PRIMARY KEY,
            title VARCHAR NOT NULL,
            title_without_series VARCHAR,
            mod_title VARCHAR NOT NULL,
            isbn VARCHAR,
            language_code VARCHAR,
            publication_year DATE,
            rating_count INT,
            average_rating FLOAT,
            authors TEXT[],
            cover_image_url VARCHAR
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_book_ratings (
            user_id INT REFERENCES users(user_id),
            book_id INT REFERENCES books(book_id),
            rating INT NOT NULL,
            rated_date DATE,
            PRIMARY KEY (user_id, book_id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS listed_books (
            user_id INT REFERENCES users(user_id),
            book_id INT REFERENCES books(book_id),
            listed_date DATE NOT NULL,
            PRIMARY KEY (user_id, book_id)
        )
    ''')
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS requested_books (
            user_id INT REFERENCES users(user_id),
            book_id INT REFERENCES books(book_id),
            requested_date DATE NOT NULL,
            PRIMARY KEY (user_id, book_id)
        )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()