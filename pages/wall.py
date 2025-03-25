import streamlit as st
from sqlalchemy import desc

from database import get_db
from models import (
    Book,
    City,
    District,
    DistrictCity,
    ListedBook,
    Province,
    ProvinceDistrict,
    User,
)
from utils import search


def get_provinces():
    """Fetch all provinces from the database."""
    with get_db() as db:
        provinces = db.query(Province).order_by(Province.name).all()
        return {province.name: province.province_id for province in provinces}


def get_districts(province_id=None):
    """Fetch districts, optionally filtered by province."""
    with get_db() as db:
        query = db.query(District).join(ProvinceDistrict).filter(ProvinceDistrict.district_id == District.district_id)
        if province_id:
            query = query.filter(ProvinceDistrict.province_id == province_id)
        districts = query.order_by(District.name).all()
        return {district.name: district.district_id for district in districts}


def get_cities(district_id=None):
    """Fetch cities, optionally filtered by district."""
    with get_db() as db:
        query = db.query(City).join(DistrictCity).filter(DistrictCity.city_id == City.city_id)
        if district_id:
            query = query.filter(DistrictCity.district_id == district_id)
        cities = query.order_by(City.name).all()
        return {city.name: city.city_id for city in cities}


def display_wall():
    st.title("Booxchange - Book Wall")
    st.write("Discover books shared by the community")

    # Initialize session state for pagination, search, and location filters
    if 'wall_offset' not in st.session_state:
        st.session_state.wall_offset = 0
    if 'displayed_books' not in st.session_state:
        st.session_state.displayed_books = []
    if 'total_loaded' not in st.session_state:
        st.session_state.total_loaded = 0
    if 'render_count' not in st.session_state:
        st.session_state.render_count = 0
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    if 'selected_province_id' not in st.session_state:
        st.session_state.selected_province_id = None
    if 'selected_district_id' not in st.session_state:
        st.session_state.selected_district_id = None
    if 'selected_city_id' not in st.session_state:
        # Default to user's city/district/province if logged in
        if 'user_id' in st.session_state and st.session_state.user_id:
            with get_db() as db:
                user = db.query(User).filter(User.user_id == st.session_state.user_id).first()
                if user:
                    st.session_state.selected_city_id = user.city_id
                    district_city = db.query(DistrictCity).filter(DistrictCity.city_id == user.city_id).first()
                    if district_city:
                        st.session_state.selected_district_id = district_city.district_id
                        province_district = db.query(ProvinceDistrict).filter(ProvinceDistrict.district_id == district_city.district_id).first()
                        if province_district:
                            st.session_state.selected_province_id = province_district.province_id
        else:
            st.session_state.selected_city_id = None

    # Fetch location options
    province_options = get_provinces()
    province_names = ["All Provinces"] + list(province_options.keys())
    
    district_options = get_districts(st.session_state.selected_province_id)
    district_names = ["All Districts"] + list(district_options.keys())
    
    city_options = get_cities(st.session_state.selected_district_id)
    city_names = ["All Cities"] + list(city_options.keys())

    # Location filter dropdowns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_province_name = st.selectbox(
            "Filter by Province",
            options=province_names,
            index=province_names.index("All Provinces") if st.session_state.selected_province_id is None else list(province_options.keys()).index(
                next(name for name, pid in province_options.items() if pid == st.session_state.selected_province_id)) + 1,
            key="province_filter"
        )
        new_province_id = province_options.get(selected_province_name) if selected_province_name != "All Provinces" else None
        if new_province_id != st.session_state.selected_province_id:
            st.session_state.selected_province_id = new_province_id
            st.session_state.selected_district_id = None  # Reset district when province changes
            st.session_state.selected_city_id = None     # Reset city when province changes

    with col2:
        selected_district_name = st.selectbox(
            "Filter by District",
            options=district_names,
            index=district_names.index("All Districts") if st.session_state.selected_district_id is None else list(district_options.keys()).index(
                next(name for name, did in district_options.items() if did == st.session_state.selected_district_id)) + 1,
            key="district_filter"
        )
        new_district_id = district_options.get(selected_district_name) if selected_district_name != "All Districts" else None
        if new_district_id != st.session_state.selected_district_id:
            st.session_state.selected_district_id = new_district_id
            st.session_state.selected_city_id = None  # Reset city when district changes

    with col3:
        selected_city_name = st.selectbox(
            "Filter by City",
            options=city_names,
            index=city_names.index("All Cities") if st.session_state.selected_city_id is None else list(city_options.keys()).index(
                next(name for name, cid in city_options.items() if cid == st.session_state.selected_city_id)) + 1,
            key="city_filter"
        )
        st.session_state.selected_city_id = city_options.get(selected_city_name) if selected_city_name != "All Cities" else None

    # Search bar
    search_input = st.text_input("Search for a book", value=st.session_state.search_query, key="search_input")

    def load_books(offset, limit=20, search_query=None, province_id=None, district_id=None, city_id=None):
        with get_db() as db:
            query = (
                db.query(ListedBook, Book, User, City)
                .join(Book, ListedBook.book_id == Book.book_id)
                .join(User, ListedBook.user_id == User.user_id)
                .join(City, User.city_id == City.city_id)
                .join(DistrictCity, City.city_id == DistrictCity.city_id)
                .join(District, DistrictCity.district_id == District.district_id)
                .join(ProvinceDistrict, District.district_id == ProvinceDistrict.district_id)
                .join(Province, ProvinceDistrict.province_id == Province.province_id)
            )

            # Apply location filters
            if city_id:
                query = query.filter(User.city_id == city_id)
            elif district_id:
                query = query.filter(DistrictCity.district_id == district_id)
            elif province_id:
                query = query.filter(ProvinceDistrict.province_id == province_id)

            # Apply search filter if provided
            if search_query:
                matched_book_ids = search(search_query)
                query = query.filter(ListedBook.book_id.in_(matched_book_ids))
            else:
                query = query.order_by(desc(ListedBook.listed_date))

            books = query.offset(offset).limit(limit).all()
            return books

    def load_next_batch():
        new_books = load_books(
            st.session_state.wall_offset,
            search_query=st.session_state.search_query if st.session_state.search_query else None,
            province_id=st.session_state.selected_province_id,
            district_id=st.session_state.selected_district_id,
            city_id=st.session_state.selected_city_id
        )
        if new_books:
            st.session_state.displayed_books.extend(new_books)
            st.session_state.wall_offset += 20
            st.session_state.total_loaded += len(new_books)

            if st.session_state.total_loaded > 40:
                excess = st.session_state.total_loaded - 40
                st.session_state.displayed_books = st.session_state.displayed_books[excess:]
                st.session_state.total_loaded = 40

    # Handle search or location filter change
    if search_input != st.session_state.search_query:
        st.session_state.search_query = search_input
        st.session_state.wall_offset = 0
        st.session_state.displayed_books = []
        st.session_state.total_loaded = 0
        load_next_batch()

    # Initial load or filter change
    if (not st.session_state.displayed_books or
        'last_filters' not in st.session_state or
        st.session_state.last_filters != (st.session_state.selected_province_id, st.session_state.selected_district_id, st.session_state.selected_city_id)):
        st.session_state.wall_offset = 0
        st.session_state.displayed_books = []
        st.session_state.total_loaded = 0
        load_next_batch()
        st.session_state.last_filters = (st.session_state.selected_province_id, st.session_state.selected_district_id, st.session_state.selected_city_id)

    # Display filters applied
    filters_applied = []
    if st.session_state.search_query:
        filters_applied.append(f"Search: '{st.session_state.search_query}'")
    if st.session_state.selected_province_id:
        province_name = next(name for name, pid in province_options.items() if pid == st.session_state.selected_province_id)
        filters_applied.append(f"Province: {province_name}")
    if st.session_state.selected_district_id:
        district_name = next(name for name, did in district_options.items() if did == st.session_state.selected_district_id)
        filters_applied.append(f"District: {district_name}")
    if st.session_state.selected_city_id:
        city_name = next(name for name, cid in city_options.items() if cid == st.session_state.selected_city_id)
        filters_applied.append(f"City: {city_name}")
    if filters_applied:
        st.write(f"Showing results for: {' and '.join(filters_applied)}")

    if not st.session_state.displayed_books:
        st.write("No matching listed books found.")
    else:
        for i, (listed_book, book, user, city) in enumerate(st.session_state.displayed_books):
            col1, col2 = st.columns([1, 3])

            with col1:
                if book.cover_image_url:
                    st.image(book.cover_image_url, width=100)
                else:
                    st.write("No cover")

            with col2:
                unique_key = f"book_{st.session_state.render_count}_{i}_{listed_book.list_id}"
                if st.button(f"{book.title}", key=unique_key):
                    st.session_state.selected_book = {
                        'list_id': listed_book.list_id,
                        'book_id': book.book_id,
                        'user_id': user.user_id
                    }
                    st.switch_page("pages/book_details.py")

                st.write(f"Rating: {book.average_rating}")
                st.write(f"Posted: {listed_book.listed_date}")
                st.write(f"Location: {city.name}")
                st.write("---")

    # Load more button
    if st.button("Load More", key="load_more_button"):
        load_next_batch()
        st.session_state.render_count += 1
        st.rerun()

    # Infinite scroll simulation
    with st.empty():
        if st.session_state.total_loaded >= 20 and not st.session_state.search_query and not any([st.session_state.selected_province_id, st.session_state.selected_district_id, st.session_state.selected_city_id]):
            st.write("Scroll to load more...")

if __name__ == "__main__":
    display_wall()