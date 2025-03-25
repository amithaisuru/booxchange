# main.py
import streamlit as st

from database import init_db
from pages.books import listed_books_page
from pages.login import login_page
from pages.messages import messages_page
from pages.recommendations import display_recommendations  # Import the new function
from pages.wall import display_wall


def display_trending():
    st.title("Trending Books")
    st.write("Books that are popular right now")
    st.info("This page will display trending books based on user activity.")


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