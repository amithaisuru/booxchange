# pages/recommendations.py
import streamlit as st
from sqlalchemy import desc

from collaborative_filter import get_recommendations
from database import get_db
from models import Book, City, ListedBook, User


def display_recommendations():
    st.title("Recomended For You")

    if 'user_id' not in st.session_state or st.session_state.user_id is None:
        st.warning("Please login to see your recommendations")
        return

    # Fetch all recommended book IDs once
    recommended_book_ids = get_recommendations(st.session_state.user_id)
    if not recommended_book_ids:
        st.info("No recommendations available at this time.")
        return

    # Section 1: Compact list of all recommended books
    st.subheader("All Recommended Books")
    with st.expander("View all recommendations", expanded=False):
        with get_db() as db:
            all_recs = (
                db.query(Book)
                .filter(Book.book_id.in_(recommended_book_ids))
                .all()
            )
            if not all_recs:
                st.write("No books found for these recommendations.")
            else:
                # Process books in groups of 3
                for i in range(0, len(all_recs), 3):
                    row_books = all_recs[i:i + 3]  # Get up to 3 books for this row
                    cols = st.columns(3)  # Create 3 columns
                    for idx, book in enumerate(row_books):
                        with cols[idx]:
                            if book.cover_image_url:
                                st.image(book.cover_image_url, width=50)
                            else:
                                st.write("No cover")
                            st.write(book.title)

    # Section 2: Detailed list of listed recommended books with pagination
    st.subheader("Available in the Community")

    # Initialize session state for pagination
    if 'rec_offset' not in st.session_state:
        st.session_state.rec_offset = 0
    if 'displayed_recs' not in st.session_state:
        st.session_state.displayed_recs = []
    if 'total_recs_loaded' not in st.session_state:
        st.session_state.total_recs_loaded = 0

    def load_recommendations(offset, limit=20):
        with get_db() as db:
            recs = (
                db.query(ListedBook, Book, User, City)
                .join(Book, ListedBook.book_id == Book.book_id)
                .join(User, ListedBook.user_id == User.user_id)
                .join(City, User.city_id == City.city_id)
                .filter(ListedBook.book_id.in_(recommended_book_ids))
                .order_by(desc(ListedBook.listed_date))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return recs

    # Load initial batch or next batch
    def load_next_batch():
        new_recs = load_recommendations(st.session_state.rec_offset)
        if new_recs:
            st.session_state.displayed_recs.extend(new_recs)
            st.session_state.rec_offset += len(new_recs)
            st.session_state.total_recs_loaded += len(new_recs)

            # Memory management: keep only the most recent 40 books
            if st.session_state.total_recs_loaded > 40:
                excess = st.session_state.total_recs_loaded - 40
                st.session_state.displayed_recs = st.session_state.displayed_recs[excess:]
                st.session_state.total_recs_loaded = 40

    # Initial load
    if not st.session_state.displayed_recs:
        load_next_batch()

    # Display listed recommended books in a grid
    if not st.session_state.displayed_recs:
        st.info("No recommended books currently listed by the community.")
    else:
        for i, (listed_book, book, user, city) in enumerate(st.session_state.displayed_recs):
            col1, col2 = st.columns([1, 3])

            with col1:
                if book.cover_image_url:
                    st.image(book.cover_image_url, width=100)  # Larger cover image for listed books
                else:
                    st.write("No cover")

            with col2:
                if st.button(f"{book.title}", key=f"rec_{listed_book.list_id}_{i}"):
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
    if st.button("Load More"):
        load_next_batch()
        st.rerun()

    # Infinite scroll simulation
    with st.empty():
        if st.session_state.total_recs_loaded >= 20:
            st.write("Scroll to load more...")


if __name__ == "__main__":
    display_recommendations()