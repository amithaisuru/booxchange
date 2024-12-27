from datetime import date

import bcrypt
import streamlit as st

from database import get_db_connection


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def register_user(name, birth_year, password):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        age = date.today().year - birth_year.year
        hashed_password = hash_password(password)
        cur.execute(
            'INSERT INTO users (name, birth_year, password_encrypted, age) VALUES (%s, %s, %s, %s) RETURNING user_id',
            (name, birth_year, hashed_password, age)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        return user_id
    except Exception as e:
        st.error(f"Registration failed: {str(e)}")
        return None
    finally:
        cur.close()
        conn.close()

def login_user(name, password):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT user_id, password_encrypted FROM users WHERE name = %s', (name,))
        result = cur.fetchone()
        if result and verify_password(password, result[1]):
            return result[0]
        return None
    finally:
        cur.close()
        conn.close()