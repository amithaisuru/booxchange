import streamlit as st

from database import init_db
from pages.books import listed_books_page
from pages.login import login_page


def main():
    st.set_page_config(page_title="Book Sharing Platform", layout="wide")
    
    # Initialize database
    init_db()
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if st.session_state.user_id is None:
        login_page()
    else:
        page = st.sidebar.selectbox(
            "Navigation",
            ["My Listed Books", "Trending Books", "Messages"]
        )
        
        if page == "My Listed Books":
            listed_books_page()
        elif page == "Trending Books":
            st.title("Trending Books")
            # Implement trending books page
        elif page == "Messages":
            st.title("Messages")
            # Implement messages page
            
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.rerun()

if __name__ == "__main__":
    main()