# pages/trending.py
import streamlit as st

from database import get_db_connection, get_dict_cursor_connection


def get_trending_books():
    conn, cur = get_dict_cursor_connection()
    try:
        cur.execute('''
            SELECT * FROM books
            ORDER BY (rating_count * average_rating) DESC
            LIMIT 10
        ''')
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def trending_page():
    st.title("Trending Books")
    
    trending_books = get_trending_books()
    
    for book in trending_books:
        col1, col2 = st.columns([1, 3])
        with col1:
            if book['cover_image_url']:
                st.image(book['cover_image_url'], width=100)
        with col2:
            st.subheader(book['title'])
            st.write(f"Authors: {', '.join(book['authors'])}")
            st.write(f"Rating: {book['average_rating']:.2f} ({book['rating_count']} ratings)")