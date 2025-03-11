# pages/recommendations.py
import streamlit as st

from database import get_db_connection, get_dict_cursor_connection


def get_recommended_books(user_id):
    conn, cur = get_dict_cursor_connection()
    try:
        cur.execute('''
            SELECT b.* FROM books b
            WHERE b.average_rating >= 4.0
            AND b.book_id NOT IN (
                SELECT book_id FROM listed_books WHERE user_id = %s
            )
            LIMIT 10
        ''', (user_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def recommendations_page():
    st.title("Recommended Books")
    if 'user_id' not in st.session_state:
        st.warning("Please login first")
        return
    
    recommendations = get_recommended_books(st.session_state.user_id)
    
    for book in recommendations:
        col1, col2 = st.columns([1, 3])
        with col1:
            if book['cover_image_url']:
                st.image(book['cover_image_url'], width=100)
        with col2:
            st.subheader(book['title'])
            st.write(f"Authors: {', '.join(book['authors'])}")
            st.write(f"Rating: {book['average_rating']:.2f} ({book['rating_count']} ratings)")