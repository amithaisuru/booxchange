import streamlit as st

from database import init_db
from pages.books import listed_books_page
from pages.login import login_page
from pages.wall import display_wall


def display_trending():
    st.title("Trending Books")
    st.write("Books that are popular right now")
    
    # Query books that are trending (most listed or most requested)
    # with get_db() as db:
    #     trending_books = get_trending_books(db, limit=10)
    
    # Placeholder
    st.info("This page will display trending books based on user activity.")

def display_recommendations():
    st.title("Recommended for You")
    st.write("Books we think you might like")
    
    # Implement recommendation logic here
    # You could base it on user's listed books, ratings, etc.
    
    # Placeholder
    st.info("This page will show personalized book recommendations.")

def main():
    st.set_page_config(page_title="Booxchange", layout="wide")
    
    # Initialize database
    init_db()
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    # Sidebar navigation
    if st.session_state.user_id is None:
        # Pre-login navigation options
        page = st.sidebar.radio(
            "Navigation",
            ["Home", "Login/Register"]
        )
        
        if page == "Home":
            display_wall()
        elif page == "Login/Register":
            login_page()
    else:
        # Post-login navigation options
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
            
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.rerun()

if __name__ == "__main__":
    main()