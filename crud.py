from datetime import datetime

import bcrypt
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Book, ListedBook, RequestedBook, User, UserBookRating


def create_user(db: Session, name: str, user_name: str, birth_year: datetime, password: str, city_id: int):
    max_id = db.query(func.max(User.user_id)).scalar() or 0
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    age = datetime.now().year - birth_year.year
    db_user = User(
        user_id = max_id + 1,
        name=name,
        user_name=user_name,
        birth_year=birth_year,
        password_encrypted=hashed_password.decode('utf-8'),
        age=age,
        city_id=city_id
    )

    print(name, user_name, birth_year, hashed_password, age, city_id)

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError as e:
        db.rollback()
        if "Key (user_name)" in str(e.orig):
            print("user already exists")
        else:
            print(f"error creating user: {str(e.orig)}")
        return None

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.user_id == user_id).first()

def get_user_by_name(db: Session, user_name: str):
    return db.query(User).filter(User.name == user_name).first()

def verify_user(db: Session, name: str, password: str):
    user = get_user_by_name(db, name)
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password_encrypted.encode('utf-8')):
        return user
    return None

def create_book(db: Session, book_data: dict):
    # Get the maximum book_id from the books table, default to 0 if table is empty
    max_id = db.query(func.max(Book.book_id)).scalar() or 0
    new_book_id = max_id + 1
    
    # Create the book object with the new book_id
    db_book = Book(
        book_id=new_book_id,  # Explicitly set the book_id
        **book_data
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def get_book(db: Session, book_id: int):
    return db.query(Book).filter(Book.book_id == book_id).first()

def list_book(db: Session, user_id: int, book_id: int):
    list_id = db.query(func.max(ListedBook.list_id)).scalar() or 0
    db_listed_book = ListedBook(
        list_id=list_id + 1,
        user_id=user_id,
        book_id=book_id,
        listed_date=datetime.utcnow()
    )
    db.add(db_listed_book)
    db.commit()
    db.refresh(db_listed_book)
    return db_listed_book

def remove_listed_book(db: Session, user_id: int, book_id: int):
    db_listed_book = db.query(ListedBook).filter(
        ListedBook.user_id == user_id, ListedBook.book_id == book_id
    ).first()
    db.delete(db_listed_book)
    db.commit()
    return True

def get_user_listed_books(db: Session, user_id: int):
    return (
        db.query(Book)
        .join(ListedBook)
        .filter(ListedBook.user_id == user_id)
        .all()
    )

def rate_book(db: Session, user_id: int, book_id: int, rating: int):
    """
    Rate a book or update an existing rating. This function:
    1. Checks if the user has already rated this book
    2. Updates or inserts into the user_book_ratings table
    3. The trigger will handle updating rating_count and average_rating
    
    Args:
        db (Session): Database session
        user_id (int): ID of the user giving the rating
        book_id (int): ID of the book being rated
        rating (int): Rating value (1-5)
        
    Returns:
        UserBookRating: The created or updated rating record
    """
    # Validate book existence
    book = get_book_details(db, book_id)
    if not book:
        return None
    
    # Check if the user has already rated this book
    existing_rating = db.query(UserBookRating).filter(
        UserBookRating.user_id == user_id,
        UserBookRating.book_id == book_id
    ).first()
    
    now = datetime.utcnow()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating
        existing_rating.rated_date = now
        db.commit()
        db.refresh(existing_rating)
        return existing_rating
    else:
        # Create new rating
        db_rating = UserBookRating(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            rated_date=now
        )
        db.add(db_rating)
        db.commit()
        db.refresh(db_rating)
        return db_rating

def remove_rating(db: Session, user_id: int, book_id: int):
    """
    Remove a user's rating for a specific book.
    
    Args:
        db (Session): Database session
        user_id (int): ID of the user
        book_id (int): ID of the book
        
    Returns:
        bool: True if rating was removed, False otherwise
    """
    rating = db.query(UserBookRating).filter(
        UserBookRating.user_id == user_id,
        UserBookRating.book_id == book_id
    ).first()
    if rating:
        db.delete(rating)
        db.commit()
        return True
    return False

def get_trending_books(db: Session, limit: int = 10):
    return (
        db.query(Book)
        .order_by(Book.rating_count.desc(), Book.average_rating.desc())
        .limit(limit)
        .all()
    )

def get_book_details(db: Session, book_id: int):
    return db.query(Book).filter(Book.book_id == book_id).first()

def get_user_book_rating(db: Session, user_id: int, book_id: int):
    """
    Get a user's rating for a specific book
    
    Args:
        db (Session): Database session
        user_id (int): ID of the user
        book_id (int): ID of the book
        
    Returns:
        UserBookRating or None: The user's rating record if it exists
    """
    return db.query(UserBookRating).filter(
        UserBookRating.user_id == user_id,
        UserBookRating.book_id == book_id
    ).first()