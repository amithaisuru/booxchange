import streamlit as st

from crud import get_book_details, get_user
from database import get_db
from models import ListedBook


def display_book_details():
    st.title("Book Details")

    if 'selected_book' not in st.session_state:
        st.error("No book selected")
        return

    selected = st.session_state.selected_book
    list_id = selected['list_id']
    book_id = selected['book_id']
    user_id = selected['user_id']

    with get_db() as db:
        # Get book details
        book = get_book_details(db, book_id)
        user = get_user(db, user_id)
        listed_book = db.query(ListedBook).filter(ListedBook.list_id == list_id).first()

        if not all([book, user, listed_book]):
            st.error("Book information not found")
            return

        # Display book information
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if book.cover_image_url:
                st.image(book.cover_image_url, width=200)
            else:
                st.write("No cover available")
                
        with col2:
            st.header(book.title)
            if book.authors:
                authors = book.authors if isinstance(book.authors, list) else [book.authors]
                st.write(f"Authors: {', '.join(str(author) for author in authors)}")
            st.write(f"ISBN: {book.isbn or 'Not available'}")
            st.write(f"Posted on: {listed_book.listed_date}")
            st.write(f"Posted by: {user.user_name}")
            
            # Message button
            if st.button("Message User"):
                # Placeholder for messaging functionality
                st.session_state.message_target = user.user_id
                st.success(f"Opening message to {user.user_name} (Functionality TBD)")
        
        # Back button
        if st.button("Back to Wall"):
            del st.session_state.selected_book
            st.switch_page("pages/wall.py")

if __name__ == "__main__":
    display_book_details()