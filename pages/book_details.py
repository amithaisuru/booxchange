import streamlit as st

from crud import get_book_details, get_user, get_user_book_rating, rate_book
from database import get_db
from messaging import (
    get_or_create_conversation,  # Import the function to handle conversations
)
from models import ListedBook


def display_book_details():
    st.title("Book Details")

    if 'selected_book' not in st.session_state:
        st.error("No book selected")
        return
    
    # Check if user is logged in
    if 'user_id' not in st.session_state:
        st.warning("Please log in to rate books or message users")
        logged_in = False
    else:
        logged_in = True
        current_user_id = st.session_state.user_id

    selected = st.session_state.selected_book
    list_id = selected['list_id']
    book_id = selected['book_id']
    user_id = selected['user_id']  # This is the book lister's user ID

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
            st.write(f"ISBN: {book.isbn or 'Not available'}")
            st.write(f"Posted by: {user.user_name}")
            st.write(f"Posted on: {listed_book.listed_date}")
            st.write(f"Book ID: {book_id}")
            if book.authors:
                authors = book.authors if isinstance(book.authors, list) else [book.authors]
                st.write(f"Authors: {', '.join(str(author) for author in authors)}")
            # Display current rating information
            st.write(f"Average Rating: {book.average_rating:.1f}/5 ({book.rating_count} ratings)")
            
            # Message button (modified)
            if logged_in and current_user_id != user.user_id:  # Only show if logged in and not the same user
                if st.button("Message User", key=f"msg_{list_id}"):
                    # Create or get existing conversation
                    conversation = get_or_create_conversation(db, current_user_id, user.user_id)
                    st.session_state.selected_conversation = conversation.conversation_id
                    st.switch_page("pages/messages.py")  # Navigate to messages page
            elif not logged_in:
                st.write("Log in to message the user.")
            elif current_user_id == user.user_id:
                st.write("This is your listing.")
        
        # Add rating functionality for logged-in users
        st.subheader("Rate this book")
        
        if not logged_in:
            st.info("Please log in to rate this book")
        else:
            # Check if user has already rated this book
            existing_rating = get_user_book_rating(db, current_user_id, book_id)
            
            if existing_rating:
                st.write(f"Your current rating: {existing_rating.rating}/5")
                st.write("You can update your rating below:")
            else:
                st.write("Click to rate this book from 1 to 5 stars")
            
            def update_user_rating(rating_value):
                rate_book(db, current_user_id, book_id, rating_value)
                if existing_rating:
                    st.success(f"Your rating has been updated to {rating_value}/5!")
                else:
                    st.success(f"Thank you for rating this book {rating_value}/5!")
                st.rerun()
            
            with st.container():
                cols = st.columns([1, 1, 1, 1, 1])
                for i in range(5):
                    with cols[i]:
                        if st.button(str(i + 1), key=f"rate_{i+1}", use_container_width=True):
                            update_user_rating(i + 1)
        
        # Back button
        if st.button("Back to Wall"):
            del st.session_state.selected_book
            st.switch_page("pages/wall.py")

if __name__ == "__main__":
    display_book_details()