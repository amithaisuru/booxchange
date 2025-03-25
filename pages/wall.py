import streamlit as st
from sqlalchemy import desc

from database import get_db
from models import Book, City, ListedBook, User
from utils import search  # Import the search function


def display_wall():
    st.title("Booxchange - Book Wall")
    st.write("Discover books shared by the community")

    # Initialize session state for pagination and search
    if 'wall_offset' not in st.session_state:
        st.session_state.wall_offset = 0
    if 'displayed_books' not in st.session_state:
        st.session_state.displayed_books = []
    if 'total_loaded' not in st.session_state:
        st.session_state.total_loaded = 0
    if 'render_count' not in st.session_state:
        st.session_state.render_count = 0
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""

    # Search bar
    search_input = st.text_input("Search for a book", value=st.session_state.search_query, key="search_input")
    
    def load_books(offset, limit=20, search_query=None):
        with get_db() as db:
            query = (
                db.query(ListedBook, Book, User, City)
                .join(Book, ListedBook.book_id == Book.book_id)
                .join(User, ListedBook.user_id == User.user_id)
                .join(City, User.city_id == City.city_id)
            )
            
            if search_query:
                # Get book IDs from search function
                matched_book_ids = search(search_query)
                # Filter to only listed books
                query = query.filter(ListedBook.book_id.in_(matched_book_ids))
            else:
                query = query.order_by(desc(ListedBook.listed_date))
            
            books = query.offset(offset).limit(limit).all()
            return books

    def load_next_batch():
        new_books = load_books(
            st.session_state.wall_offset,
            search_query=st.session_state.search_query if st.session_state.search_query else None
        )
        if new_books:
            st.session_state.displayed_books.extend(new_books)
            st.session_state.wall_offset += 20
            st.session_state.total_loaded += len(new_books)
            
            if st.session_state.total_loaded > 40:
                excess = st.session_state.total_loaded - 40
                st.session_state.displayed_books = st.session_state.displayed_books[excess:]
                st.session_state.total_loaded = 40

    # Handle search submission
    if search_input != st.session_state.search_query:
        st.session_state.search_query = search_input
        st.session_state.wall_offset = 0
        st.session_state.displayed_books = []
        st.session_state.total_loaded = 0
        load_next_batch()

    # Initial load if no books are displayed yet
    if not st.session_state.displayed_books:
        load_next_batch()

    # Display search results or all books
    if st.session_state.search_query:
        st.write(f"Showing results for: '{st.session_state.search_query}'")
    if not st.session_state.displayed_books:
        st.write("No matching listed books found.")
    else:
        for i, (listed_book, book, user, city) in enumerate(st.session_state.displayed_books):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if book.cover_image_url:
                    st.image(book.cover_image_url, width=100)
                else:
                    st.write("No cover")
                    
            with col2:
                unique_key = f"book_{st.session_state.render_count}_{i}_{listed_book.list_id}"
                if st.button(f"{book.title}", key=unique_key):
                    st.session_state.selected_book = {
                        'list_id': listed_book.list_id,
                        'book_id': book.book_id,
                        'user_id': user.user_id
                    }
                    st.switch_page("pages/book_details.py")
                    
                st.write(f"Rating: {book.average_rating}")
                st.write(f"Posted: {listed_book.listed_date}")
                st.write(f"Location: {city.name}")
                st.write("---")

    # Load more button
    if st.button("Load More", key="load_more_button"):
        load_next_batch()
        st.session_state.render_count += 1
        st.rerun()

    # Infinite scroll simulation
    with st.empty():
        if st.session_state.total_loaded >= 20 and not st.session_state.search_query:
            st.write("Scroll to load more...")

if __name__ == "__main__":
    display_wall()