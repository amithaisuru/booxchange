from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import Book, ListedBook, RequestedBook, UserBookRating


def get_trending_books(db: Session, limit: int = 10, days: int = 7):
    """
    Fetch trending books based on recent ratings, rating count, and average rating,
    limited to books currently listed in ListedBook.
    
    Args:
        db (Session): Database session
        limit (int): Number of books to return
        days (int): Time window in days for recent activity
    
    Returns:
        list: List of Book objects sorted by trending score
    """
    # Define the time window
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Subquery for recent ratings count per book
    recent_ratings = (
        db.query(UserBookRating.book_id, func.count(UserBookRating.rating).label("recent_rating_count"))
        .filter(UserBookRating.rated_date >= cutoff_date)
        .group_by(UserBookRating.book_id)
        .subquery()
    )

    # Main query: Start with listed books and join with recent activity
    books = (
        db.query(Book)
        .join(ListedBook, Book.book_id == ListedBook.book_id)  # Only books in ListedBook
        .outerjoin(recent_ratings, Book.book_id == recent_ratings.c.book_id)
        .distinct(Book.book_id)  # Ensure each book appears once
        .all()
    )

    # Calculate trending score for each listed book
    trending_books = []
    for book in books:
        recent_rating_count = db.query(recent_ratings.c.recent_rating_count).filter(recent_ratings.c.book_id == book.book_id).scalar() or 0
        rating_count = book.rating_count or 0
        average_rating = book.average_rating or 0.0

        # Trending score formula (adjusted weights without recent requests)
        score = (
            (0.5 * recent_rating_count) +  # Recent ratings (50% weight)
            (0.3 * rating_count) +         # Total rating count (30% weight)
            (0.2 * average_rating)         # Average rating (20% weight)
        )
        trending_books.append((book, score))

    # Sort by score and limit to top N
    trending_books.sort(key=lambda x: x[1], reverse=True)
    return [book for book, _ in trending_books[:limit]]


def get_trending_books_simple(limit: int = 10, days: int = 7):
    """
    Wrapper function to simplify calling get_trending_books with a database session.
    
    Args:
        limit (int): Number of books to return
        days (int): Time window in days for recent activity
    
    Returns:
        list: List of trending Book objects
    """
    with get_db() as db:
        return get_trending_books(db, limit, days)