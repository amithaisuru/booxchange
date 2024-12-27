from datetime import datetime

import streamlit as st

from crud import create_book, get_user_listed_books, list_book
from database import get_db


def listed_books_page():
    if 'user_id' not in st.session_state:
        st.warning("Please login first")
        return
        
    st.title("My Listed Books")
    
    with get_db() as db:
        books = get_user_listed_books(db, st.session_state.user_id)
        
        # Add new book section
        with st.expander("Add New Book"):
            with st.form("add_book_form"):
                title = st.text_input("Book Title")
                isbn = st.text_input("ISBN")
                authors = st.text_input("Authors (comma-separated)")
                pub_year = st.date_input("Publication Year")
                
                if st.form_submit_button("Add Book"):
                    book_data = {
                        "title": title,
                        "isbn": isbn,
                        "authors": authors.split(','),
                        "publication_year": pub_year
                    }
                    try:
                        new_book = create_book(db, book_data)
                        list_book(db, st.session_state.user_id, new_book.book_id)
                        st.success("Book added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding book: {str(e)}")
        
        # Display existing books
        for book in books:
            col1, col2, col3 = st.columns([2, 3, 1])
            with col1:
                if book.cover_image_url:
                    st.image(book.cover_image_url, width=100)
            with col2:
                st.subheader(book.title)
                st.write(f"Authors: {', '.join(book.authors)}")
            with col3:
                if st.button("Remove", key=f"remove_{book.book_id}"):
                    # Implement remove functionality
                    pass