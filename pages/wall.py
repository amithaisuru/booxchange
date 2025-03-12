import streamlit as st
from sqlalchemy import desc

from database import get_db
from models import Book, City, ListedBook, User


def display_wall():
    st.title("Booxchange - Book Wall")
    st.write("Discover books shared by the community")

    # Initialize session state for pagination
    if 'wall_offset' not in st.session_state:
        st.session_state.wall_offset = 0
    if 'displayed_books' not in st.session_state:
        st.session_state.displayed_books = []
    if 'total_loaded' not in st.session_state:
        st.session_state.total_loaded = 0

    def load_books(offset, limit=20):
        with get_db() as db:
            # Query latest books with user and city information
            books = (
                db.query(ListedBook, Book, User, City)
                .join(Book, ListedBook.book_id == Book.book_id)
                .join(User, ListedBook.user_id == User.user_id)
                .join(City, User.city_id == City.city_id)
                .order_by(desc(ListedBook.listed_date))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return books

    # Load initial batch or next batch
    def load_next_batch():
        new_books = load_books(st.session_state.wall_offset)
        if new_books:
            st.session_state.displayed_books.extend(new_books)
            st.session_state.wall_offset += 20
            st.session_state.total_loaded += len(new_books)
            
            # Memory management: remove top books when we have more than 40 loaded
            if st.session_state.total_loaded > 40:
                excess = st.session_state.total_loaded - 40
                st.session_state.displayed_books = st.session_state.displayed_books[excess:]
                st.session_state.total_loaded = 40

    # Initial load
    if not st.session_state.displayed_books:
        load_next_batch()

    # Display books in a grid
    for i, (listed_book, book, user, city) in enumerate(st.session_state.displayed_books):
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if book.cover_image_url:
                st.image(book.cover_image_url, width=100)
            else:
                st.write("No cover")
                
        with col2:
            if st.button(f"{book.title}", key=f"book_{listed_book.list_id}"):
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

    # Load more button/scroll trigger
    if st.button("Load More"):
        load_next_batch()
        st.rerun()

    # Infinite scroll simulation
    with st.empty():
        if st.session_state.total_loaded >= 20:  # Only show if there's potential for more
            st.write("Scroll to load more...")

if __name__ == "__main__":
    display_wall()