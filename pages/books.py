import re
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity

from crud import (
    create_book,
    get_book_details,
    get_user_listed_books,
    list_book,
    remove_listed_book,
)
from database import get_db


def search(query):
    vectorizer = pd.read_pickle("pkl_files/vectorizer_searchengine.pkl")
    titles = pd.read_pickle("pkl_files/book_titles.pkl")
    processed_query = re.sub("[^a-zA-Z0-9 ]", "", query.lower())
    query_vect = vectorizer.transform([processed_query])
    tfidf = vectorizer.fit_transform(titles["mod_title"])
    similarity_vect = cosine_similarity(query_vect, tfidf).flatten()
    indices = np.argpartition(similarity_vect, -20)[-20:]
    top_book_titles = titles.iloc[indices]
    return top_book_titles["book_id"].values #use a suitable return type

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
    
    with get_db() as db:
        # Add new book section
        with st.expander("Add New Book", expanded=True):
            # Search option
            st.subheader("Search for a book")
            search_query = st.text_input("Enter book title to search")
            
            if st.button("Search") and search_query:
                # Get search results using the search function
                book_ids = search(search_query)
                
                # Fetch book details for each ID
                books = []
                for book_id in book_ids:
                    book = get_book_details(db, book_id)
                    if book:
                        books.append(book)
                
                st.session_state.search_results = books
                st.session_state.selected_book = None  # Reset selected book
            
            # Display search results
            if st.session_state.search_results:
                st.subheader("Search Results")
                for i, book in enumerate(st.session_state.search_results):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        if book.cover_image_url:
                            st.image(book.cover_image_url, width=80)
                    
                    with col2:
                        st.write(f"**{book.title}**")
                        if hasattr(book, 'authors') and book.authors:
                            authors = book.authors if isinstance(book.authors, list) else [book.authors]
                            st.write(f"By: {', '.join(str(author) for author in authors)}")
                    
                    with col3:
                        if st.button("Select", key=f"select_{i}"):
                            st.session_state.selected_book = book
            
            # Display manual entry form if no book is selected
            if not st.session_state.selected_book:
                st.subheader("Or add book manually")
                with st.form("add_book_form"):
                    title = st.text_input("Book Title")
                    isbn = st.text_input("ISBN")
                    authors = st.text_input("Authors (comma-separated)")
                    pub_year = st.date_input("Publication Year")
                    
                    if st.form_submit_button("Add Book"):
                        if title:  # Basic validation
                            book_data = {
                                "title": title,
                                "isbn": isbn,
                                "authors": authors.split(',') if authors else [],
                                "publication_year": pub_year
                            }
                            try:
                                new_book = create_book(db, book_data)
                                list_book(db, st.session_state.user_id, new_book.book_id)
                                st.success("Book added successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error adding book: {str(e)}")
                        else:
                            st.error("Book title is required")
            
            # If a book is selected, show confirmation
            else:
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
                        # Reset the states
                        st.session_state.search_results = None
                        st.session_state.selected_book = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error listing book: {str(e)}")
                
                if st.button("Cancel"):
                    st.session_state.selected_book = None
                    st.rerun()
        
        # Display existing books
        st.subheader("My Listed Books")
        books = get_user_listed_books(db, st.session_state.user_id)
        
        if not books:
            st.info("You haven't listed any books yet.")
        
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
                    # Implement remove functionality
                    if remove_listed_book(db, st.session_state.user_id, book.book_id):
                        st.success("Book removed successfully!")
                    else:
                        st.error("Error removing book")
                    st.rerun()