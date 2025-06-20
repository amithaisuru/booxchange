from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

from crud import (
    create_book,
    get_book_details,
    get_user_listed_books,
    list_book,
    remove_listed_book,
)
from database import get_db
from models import Book
from utils import search


def search_book_by_isbn(db, isbn):
    """Search for a book in the database by ISBN."""
    return db.query(Book).filter(Book.isbn == isbn).first()

def listed_books_page():
    if 'user_id' not in st.session_state:
        st.warning("Please login first")
        return
        
    st.title("My Books")
    
    # Initialize session state for search results and selected book
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'selected_book' not in st.session_state:
        st.session_state.selected_book = None
    if 'isbn_search_result' not in st.session_state:
        st.session_state.isbn_search_result = None
    
    with get_db() as db:
        # Add new book section
        with st.expander("Add New Book", expanded=False):
            # ISBN Search option
            st.subheader("Add book from the library")
            isbn_query = st.text_input("Enter ISBN to search")
            
            if st.button("Search by ISBN") and isbn_query:
                book = search_book_by_isbn(db, isbn_query)
                if book:
                    st.session_state.isbn_search_result = book
                    st.session_state.search_results = None
                    st.session_state.selected_book = None
                else:
                    st.session_state.isbn_search_result = None
                    st.error("No book found with this ISBN.")
            
            # Display ISBN search result
            if st.session_state.isbn_search_result:
                book = st.session_state.isbn_search_result
                st.subheader("ISBN Search Result")
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if book.cover_image_url:
                        st.image(book.cover_image_url, width=100)
                    else:
                        st.write("No cover available")
                
                with col2:
                    st.write(f"**{book.title}**")
                    if hasattr(book, 'authors') and book.authors:
                        authors = book.authors if isinstance(book.authors, list) else [book.authors]
                        st.write(f"By: {', '.join(str(author) for author in authors)}")
                    st.write(f"ISBN: {book.isbn}")
                
                if st.button("List This Book", key="list_isbn_book"):
                    try:
                        list_book(db, st.session_state.user_id, book.book_id)
                        st.success("Book listed successfully!")
                        st.session_state.isbn_search_result = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error listing book: {str(e)}")
                
                if st.button("Clear ISBN Search", key="clear_isbn_search"):
                    st.session_state.isbn_search_result = None
                    st.rerun()

            # General Search option
            search_query = st.text_input("Enter Title to search")
            
            if st.button("Search by Title") and search_query:
                book_ids = search(search_query)
                books = [get_book_details(db, book_id) for book_id in book_ids if get_book_details(db, book_id)]
                st.session_state.search_results = books
                st.session_state.selected_book = None
                st.session_state.isbn_search_result = None
            
            # Display general search results
            if st.session_state.search_results:
                st.subheader("Search Results")
                for i, book in enumerate(st.session_state.search_results):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        if book.cover_image_url:
                            st.image(book.cover_image_url, width=80)
                    
                    with col2:
                        st.write(f"**{book.title}**")
                        st.write(f"ISBN: {book.isbn}")
                        if hasattr(book, 'authors') and book.authors:
                            authors = book.authors if isinstance(book.authors, list) else [book.authors]
                            st.write(f"By: {', '.join(str(author) for author in authors)}")
                    
                    with col3:
                        if st.button("Select", key=f"select_{i}"):
                            st.session_state.selected_book = book
            
            # Manual entry form with ISBN check
            if not st.session_state.selected_book and not st.session_state.isbn_search_result:
                st.subheader("Or add book manually")
                with st.form("add_book_form"):
                    title = st.text_input("Book Title (required)")
                    isbn = st.text_input("ISBN (optional)")
                    authors = st.text_input("Authors (comma-separated, optional)")
                    pub_year = st.date_input("Publication Year (optional)", value=None, min_value=datetime(1000, 1, 1), max_value=datetime.now())
                    
                    if st.form_submit_button("Add Book"):
                        if not title:
                            st.error("Book title is required")
                        else:
                            # Check if ISBN exists if provided
                            if isbn:
                                existing_book = search_book_by_isbn(db, isbn)
                                if existing_book:
                                    st.error(f"A book with ISBN {isbn} already exists in the database. Please use 'Search by ISBN' to list it.")
                                    return
                            
                            # Prepare book data
                            book_data = {
                                "title": title,
                                "isbn": isbn if isbn else None,
                                "authors": authors.split(',') if authors else [],
                                "publication_year": pub_year if pub_year else None,
                                "rating_count": 0,  # Default value
                                "average_rating": 0.0  # Default value
                            }
                            try:
                                # Add new book to the books table
                                new_book = create_book(db, book_data)
                                # List the book for the user
                                list_book(db, st.session_state.user_id, new_book.book_id)
                                st.success("Book added and listed successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error adding book: {str(e)}")
                                db.rollback()  # Rollback the session on error
                                return
            
            # If a book is selected from general search, show confirmation
            elif st.session_state.selected_book:
                st.subheader("Selected Book")
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if st.session_state.selected_book.cover_image_url:
                        st.image(st.session_state.selected_book.cover_image_url, width=100)
                
                with col2:
                    st.write(f"**{st.session_state.selected_book.title}**")
                    if hasattr(st.session_state.selected_book, 'authors') and st.session_state.selected_book.authors:
                        authors = st.session_state.selected_book.authors if isinstance(st.session_state.selected_book.authors, list) else [st.session_state.selected_book.authors]
                        st.write(f"By: {', '.join(str(author) for author in authors)}")
                
                if st.button("Confirm and List This Book"):
                    try:
                        list_book(db, st.session_state.user_id, st.session_state.selected_book.book_id)
                        st.success("Book listed successfully!")
                        st.session_state.search_results = None
                        st.session_state.selected_book = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error listing book: {str(e)}")
                
                if st.button("Cancel"):
                    st.session_state.selected_book = None
                    st.rerun()
        
        # Display existing books
        st.subheader("My Listings")
        try:
            books = get_user_listed_books(db, st.session_state.user_id)
        except Exception as e:
            st.error(f"Error fetching listed books: {str(e)}")
            db.rollback()  # Rollback the session if an error occurs
            books = []

        if not books:
            st.info("You haven't listed any books yet.")
        else:
            for book in books:
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    if book.cover_image_url:
                        st.image(book.cover_image_url, width=100)
                    else:
                        st.write("No cover available")
                with col2:
                    st.subheader(book.title)
                    if hasattr(book, 'authors') and book.authors:
                        authors = book.authors if isinstance(book.authors, list) else [book.authors]
                        st.write(f"Authors: {', '.join(str(author) for author in authors)}")
                with col3:
                    if st.button("Remove", key=f"remove_{book.book_id}"):
                        if remove_listed_book(db, st.session_state.user_id, book.book_id):
                            st.success("Book removed successfully!")
                        else:
                            st.error("Error removing book")
                        st.rerun()

if __name__ == "__main__":
    listed_books_page()