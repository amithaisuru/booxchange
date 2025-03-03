from datetime import datetime

import bcrypt
from sqlalchemy import func
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
    db_book = Book(**book_data)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def get_book(db: Session, book_id: int):
    return db.query(Book).filter(Book.book_id == book_id).first()

def list_book(db: Session, user_id: int, book_id: int):
    db_listed_book = ListedBook(
        user_id=user_id,
        book_id=book_id,
        listed_date=datetime.utcnow()
    )
    db.add(db_listed_book)
    db.commit()
    db.refresh(db_listed_book)
    return db_listed_book

def get_user_listed_books(db: Session, user_id: int):
    return (
        db.query(Book)
        .join(ListedBook)
        .filter(ListedBook.user_id == user_id)
        .all()
    )

def add_book_rating(db: Session, user_id: int, book_id: int):
    db_rating = UserBookRating(
        user_id=user_id,
        book_id=book_id,
        rated_date=datetime.utcnow()
    )
    db.add(db_rating)
    db.commit()
    db.refresh(db_rating)
    return db_rating

def get_trending_books(db: Session, limit: int = 10):
    return (
        db.query(Book)
        .order_by(Book.rating_count.desc(), Book.average_rating.desc())
        .limit(limit)
        .all()
    )


    