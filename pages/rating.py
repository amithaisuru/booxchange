# pages/rating.py
def add_or_update_rating(user_id, book_id, rating):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Add rating to user_book_ratings
        cur.execute('''
            INSERT INTO user_book_ratings (user_id, book_id, rated_date)
            VALUES (%s, %s, CURRENT_DATE)
            ON CONFLICT (user_id, book_id) 
            DO UPDATE SET rated_date = CURRENT_DATE
        ''', (user_id, book_id))
        
        # Update book's average rating and rating count
        cur.execute('''
            UPDATE books
            SET rating_count = rating_count + 1,
                average_rating = (
                    SELECT AVG(rating)
                    FROM user_book_ratings
                    WHERE book_id = %s
                )
            WHERE book_id = %s
        ''', (book_id, book_id))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding rating: {str(e)}")
        return False
    finally:
        cur.close()
        conn.close()

# Add this to the book display components (in recommendations.py, trending.py, etc.)
def add_rating_widget(book):
    rating = st.slider(
        "Rate this book",
        min_value=1,
        max_value=5,
        value=3,
        key=f"rating_{book['book_id']}"
    )
    
    if st.button("Submit Rating", key=f"submit_rating_{book['book_id']}"):
        if add_or_update_rating(st.session_state.user_id, book['book_id'], rating):
            st.success("Rating submitted successfully!")
            st.rerun()