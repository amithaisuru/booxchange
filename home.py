import streamlit as st

from database import get_db, init_db
from models import ListedBook
from pages.books import listed_books_page
from pages.login import login_page
from pages.messages import messages_page
from pages.recommendations import display_recommendations
from pages.wall import display_wall
from trending import get_trending_books_simple


def display_trending():
    st.title("Trending Books")

    trending_books = get_trending_books_simple(limit=10, days=7)

    if not trending_books:
        st.info("No trending books available at this time.")
    else:
        with get_db() as db:  # Open a database session to fetch listing details
            for i, book in enumerate(trending_books):
                # Fetch the most recent listing for this book (assuming one listing per book for simplicity)
                listed_book = (
                    db.query(ListedBook)
                    .filter(ListedBook.book_id == book.book_id)
                    .order_by(ListedBook.listed_date.desc())
                    .first()
                )
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if book.cover_image_url:
                        st.image(book.cover_image_url, width=100)
                    else:
                        st.write("No cover")
                with col2:
                    # Button to go to book details page
                    if listed_book:  # Ensure there's a listing
                        if st.button(f"{book.title}", key=f"trend_{book.book_id}_{i}"):
                            st.session_state.selected_book = {
                                'list_id': listed_book.list_id,
                                'book_id': book.book_id,
                                'user_id': listed_book.user_id
                            }
                            st.switch_page("pages/book_details.py")
                    else:
                        st.subheader(book.title)  # Fallback if no listing exists
                    
                    st.write(f"Average Rating: {book.average_rating:.1f}")
                    st.write(f"Rating Count: {book.rating_count}")
                    st.write("---")


def main():
    st.set_page_config(page_title="Booxchange", layout="wide")
    
    # Initialize database
    init_db()
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    # Sidebar navigation
    if st.session_state.user_id is None:
        page = st.sidebar.radio(
            "Navigation",
            ["Home", "Login/Register"]
        )
        
        if page == "Home":
            display_wall()
        elif page == "Login/Register":
            login_page()
    else:
        st.sidebar.write(f"Welcome back!")
        
        page = st.sidebar.radio(
            "Navigation",
            ["Wall", "Trending", "Recommendations", "My Books", "Messages"]
        )
        
        if page == "Wall":
            display_wall()
        elif page == "Trending":
            display_trending()
        elif page == "Recommendations":
            display_recommendations()
        elif page == "My Books":
            listed_books_page()
        elif page == "Messages":
            messages_page()
            
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.rerun()


if __name__ == "__main__":
    main()