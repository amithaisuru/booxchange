import streamlit as st

from database import init_db
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
        for i, book in enumerate(trending_books):
            col1, col2 = st.columns([1, 3])
            with col1:
                if book.cover_image_url:
                    st.image(book.cover_image_url, width=100)
                else:
                    st.write("No cover")
            with col2:
                st.subheader(book.title)
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