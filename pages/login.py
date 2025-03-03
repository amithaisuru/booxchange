from datetime import date

import streamlit as st
from sqlalchemy import text

from crud import create_user, verify_user
from database import get_db


def get_cities_from_db():
    with get_db() as db:
        cities = db.execute(text("SELECT name FROM city")).fetchall()
        return [city.name for city in cities]
    
def get_city_id(city_name):
    with get_db() as db:
        city = db.execute(text("SELECT city_id FROM city WHERE name = :name"), {"name": city_name}).fetchone()
        return city.city_id if city else None

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
        name = st.text_input("Name", key="reg_name")
        user_name = st.text_input("User Name", key="reg_user_name")
        birth_year = st.date_input("Birth Year", min_value=date(1900, 1, 1))
        password = st.text_input("Password", type="password", key="reg_password")
        city = st.selectbox("City", get_cities_from_db())
        city_id = get_city_id(city)

        
        if st.button("Register"):
            with get_db() as db:
                try:
                    create_user(db, name, user_name, birth_year, password, city_id)
                    st.success("Registration successful! Please login.")
                except Exception as e:
                    st.error(f"Registration failed: {str(e)}")