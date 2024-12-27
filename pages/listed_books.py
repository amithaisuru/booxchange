# pages/listed_books.py
from datetime import datetime

import streamlit as st

from database import get_db_connection, get_dict_cursor_connection


def get_user_listed_books(user_id):
    conn, cur = get_dict_cursor_connection()
    try:
        cur.execute('''
            SELECT b.*, l.listed_date 
            FROM books b
            JOIN listed_books l ON b.book_id = l.book_id
            WHERE l.user_id = %s
            ORDER BY l.listed_date DESC
        ''', (user_id,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def add_listed_book(user_id, book_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO listed_books (user_id, book_id, listed_date)
            VALUES (%s, %s, CURRENT_DATE)
            ON CONFLICT (user_id, book_id) DO NOTHING
        ''', (user_id, book_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding book: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()

def remove_listed_book(user_id, book_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            DELETE FROM listed_books
            WHERE user_id = %s AND book_id = %s
        ''', (user_id, book_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error removing book: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()

def listed_books_page():
    st.title("My Listed Books")
    
    if 'user_id' not in st.session_state:
        st.warning("Please login first")
        return
    
    # Add new book section
    with st.expander("Add New Book"):
        title = st.text_input("Book Title")
        isbn = st.text_input("ISBN")
        authors = st.text_input("Authors (comma-separated)")
        pub_year = st.date_input("Publication Year")
        book_id = st.text_input("Book ID")
        
        if st.button("Add Book"):
            conn = get_db_connection()
            cur = conn.cursor()
            try:
                # First insert into books table
                cur.execute('''
                    INSERT INTO books (book_id, title, isbn, authors, publication_year)
                    VALUES (%s, %s, %s, %s)
                    RETURNING book_id
                ''', (title, isbn, authors.split(','), pub_year))
                book_id = cur.fetchone()[0]
                
                # Then add to listed_books
                if add_listed_book(st.session_state.user_id, book_id):
                    st.success("Book added successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                cur.close()
                conn.close()
    
    # Display existing books
    books = get_user_listed_books(st.session_state.user_id)
    for book in books:
        col1, col2, col3 = st.columns([2, 3, 1])
        with col1:
            if book['cover_image_url']:
                st.image(book['cover_image_url'], width=100)
        with col2:
            st.subheader(book['title'])
            st.write(f"Authors: {', '.join(book['authors'])}")
            st.write(f"Listed on: {book['listed_date']}")
        with col3:
            if st.button("Remove", key=f"remove_{book['book_id']}"):
                if remove_listed_book(st.session_state.user_id, book['book_id']):
                    st.success("Book removed successfully!")
                    st.rerun()