from datetime import date

import streamlit as st

from crud import create_user, verify_user
from database import get_db


def login_page():
    st.title("Book Sharing Platform")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.header("Login")
        name = st.text_input("Name", key="login_name")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            with get_db() as db:
                user = verify_user(db, name, password)
                if user:
                    st.session_state.user_id = user.user_id
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    
    with tab2:
        st.header("Register")
        new_name = st.text_input("Name", key="reg_name")
        birth_year = st.date_input("Birth Year", min_value=date(1900, 1, 1))
        password = st.text_input("Password", type="password", key="reg_password")
        
        if st.button("Register"):
            with get_db() as db:
                try:
                    create_user(db, new_name, birth_year, password)
                    st.success("Registration successful! Please login.")
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")