# main.py
import streamlit as st

from database import init_db
from pages.listed_books import listed_books_page
from pages.login import login_page
from pages.messages import messages_page
from pages.recommendations import recommendations_page
from pages.trending import trending_page


def main():
    st.set_page_config(page_title="Book Sharing Platform", layout="wide")
    
    # Initialize database
    init_db()
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    # Sidebar navigation
    if st.session_state.user_id is None:
        login_page()
    else:
        page = st.sidebar.selectbox(
            "Navigation",
            ["Recommendations", "Trending Books", "My Listed Books", "Messages"]
        )
        if page == "My Listed Books":
                listed_books_page()
        elif page == "Messages":
            messages_page()       
        elif page == "Recommendations":
            recommendations_page()
        elif page == "Trending Books":
            trending_page()
        elif page == "My Listed Books":
            st.title("My Listed Books")
            # Implement listed books page
        elif page == "Messages":
            st.title("Messages")
            # Implement messaging page
        
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.rerun()

if __name__ == "__main__":
    main()