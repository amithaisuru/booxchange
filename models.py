import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    ARRAY,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

load_dotenv()

# Database Configuration
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_name = Column(String, nullable=False, unique=True, index=True)
    birth_year = Column(Date, nullable=False)
    password_encrypted = Column(String, nullable=False)
    age = Column(Integer, nullable=False)

    # Relationships
    ratings = relationship("UserBookRating", back_populates="user")
    listed_books = relationship("ListedBook", back_populates="user")
    requested_books = relationship("RequestedBook", back_populates="user")

class Book(Base):
    __tablename__ = "books"

    book_id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    title_without_series = Column(String)
    mod_title = Column(String)
    isbn = Column(String)
    language_code = Column(String)
    publication_year = Column(Date)
    rating_count = Column(Integer, default=0)
    average_rating = Column(Float, default=0.0)
    authors = Column(ARRAY(Text))
    cover_image_url = Column(String)

    # Relationships
    ratings = relationship("UserBookRating", back_populates="book")
    listed = relationship("ListedBook", back_populates="book")
    requested = relationship("RequestedBook", back_populates="book")

class UserBookRating(Base):
    __tablename__ = "user_book_ratings"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    book_id = Column(Integer, ForeignKey("books.book_id"), primary_key=True)
    rating = Column(Integer)
    rated_date = Column(Date, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="ratings")
    book = relationship("Book", back_populates="ratings")

class ListedBook(Base):
    __tablename__ = "listed_books"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    book_id = Column(Integer, ForeignKey("books.book_id"), primary_key=True)
    listed_date = Column(Date, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="listed_books")
    book = relationship("Book", back_populates="listed")

class RequestedBook(Base):
    __tablename__ = "requested_books"

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    book_id = Column(Integer, ForeignKey("books.book_id"), primary_key=True)
    requested_date = Column(Date, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="requested_books")
    book = relationship("Book", back_populates="requested")
