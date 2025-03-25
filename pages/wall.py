import streamlit as st
from sqlalchemy import desc

from database import get_db
from models import Book, City, ListedBook, User
from utils import search  # Import the search function


def get_cities():
    """Fetch all cities from the database for the dropdown."""
    with get_db() as db:
        cities = db.query(City).order_by(City.name).all()
        return {city.name: city.city_id for city in cities}


def display_wall():
    st.title("Booxchange - Book Wall")
    st.write("Discover books shared by the community")

    # Initialize session state for pagination, search, and location filter
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
    if 'selected_city_id' not in st.session_state:
        # Default to user's city if logged in, otherwise None
        if 'user_id' in st.session_state and st.session_state.user_id:
            with get_db() as db:
                user = db.query(User).filter(User.user_id == st.session_state.user_id).first()
                st.session_state.selected_city_id = user.city_id if user else None
        else:
            st.session_state.selected_city_id = None

    # Fetch available cities for the dropdown
    city_options = get_cities()
    city_names = ["All Cities"] + list(city_options.keys())

    # Location filter dropdown
    selected_city_name = st.selectbox(
        "Filter by City",
        options=city_names,
        index=city_names.index("All Cities") if st.session_state.selected_city_id is None else list(city_options.keys()).index(
            next(name for name, cid in city_options.items() if cid == st.session_state.selected_city_id)) + 1
    )
    st.session_state.selected_city_id = city_options.get(selected_city_name) if selected_city_name != "All Cities" else None

    # Search bar
    search_input = st.text_input("Search for a book", value=st.session_state.search_query, key="search_input")

    def load_books(offset, limit=20, search_query=None, city_id=None):
        with get_db() as db:
            query = (
                db.query(ListedBook, Book, User, City)
                .join(Book, ListedBook.book_id == Book.book_id)
                .join(User, ListedBook.user_id == User.user_id)
                .join(City, User.city_id == City.city_id)
            )

            # Apply city filter if selected
            if city_id:
                query = query.filter(User.city_id == city_id)

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

    # Handle search or city filter change
    if search_input != st.session_state.search_query:
        st.session_state.search_query = search_input
        st.session_state.wall_offset = 0
        st.session_state.displayed_books = []
        st.session_state.total_loaded = 0
        load_next_batch()

    # Initial load if no books are displayed yet or filter changes
    if not st.session_state.displayed_books or 'last_city_id' not in st.session_state or st.session_state.last_city_id != st.session_state.selected_city_id:
        st.session_state.wall_offset = 0
        st.session_state.displayed_books = []
        st.session_state.total_loaded = 0
        load_next_batch()
        st.session_state.last_city_id = st.session_state.selected_city_id

    # Display filters applied
    if st.session_state.search_query or st.session_state.selected_city_id:
        filters_applied = []
        if st.session_state.search_query:
            filters_applied.append(f"Search: '{st.session_state.search_query}'")
        if st.session_state.selected_city_id:
            city_name = next(name for name, cid in city_options.items() if cid == st.session_state.selected_city_id)
            filters_applied.append(f"City: {city_name}")
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
        if st.session_state.total_loaded >= 20 and not st.session_state.search_query and not st.session_state.selected_city_id:
            st.write("Scroll to load more...")

if __name__ == "__main__":
    display_wall()