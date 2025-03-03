import os
import re
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
from sqlalchemy.orm import relationship, sessionmaker, validates

load_dotenv()

# Database Configuration
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    user_name = Column(String, nullable=False, unique=True, index=True)
    birth_year = Column(Date, nullable=False)
    password_encrypted = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    city_id = Column(Integer, ForeignKey('city.city_id'), nullable=False)

    # Relationships
    ratings = relationship("UserBookRating", back_populates="user")
    listed_books = relationship("ListedBook", back_populates="user")
    requested_books = relationship("RequestedBook", back_populates="user")
    city = relationship("City", back_populates="users")

    # Validation
    @validates("user_name")
    def validate_user_name(self, key, value):
        if not re.match(r"^[^\s,]+$", value):
            raise ValueError("user_name must be a single word without spaces or commas.")
        return value

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
    authors = Column(ARRAY(Integer))
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

class Province(Base):
    __tablename__ = 'province'
    
    province_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Relationships
    districts = relationship("ProvinceDistrict", back_populates="province")

class District(Base):
    __tablename__ = 'district'
    
    district_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Relationships
    provinces = relationship("ProvinceDistrict", back_populates="district")
    cities = relationship("DistrictCity", back_populates="district")

class City(Base):
    __tablename__ = 'city'
    
    city_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="city")
    districts = relationship("DistrictCity", back_populates="city")

class ProvinceDistrict(Base):
    __tablename__ = 'province_district'
    
    province_id = Column(Integer, ForeignKey('province.province_id'), primary_key=True)
    district_id = Column(Integer, ForeignKey('district.district_id'), primary_key=True)
    
    # Relationships
    province = relationship("Province", back_populates="districts")
    district = relationship("District", back_populates="provinces")

class DistrictCity(Base):
    __tablename__ = 'district_city'
    
    district_id = Column(Integer, ForeignKey('district.district_id'), primary_key=True)
    city_id = Column(Integer, ForeignKey('city.city_id'), primary_key=True)
    
    # Relationships
    district = relationship("District", back_populates="cities")
    city = relationship("City", back_populates="districts")