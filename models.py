import os
import re
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, validates

load_dotenv()

# Database Configuration
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Bayesian Rating Trigger Function
BAYESIAN_TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION update_bayesian_rating()
RETURNS TRIGGER AS $$
DECLARE
    global_avg FLOAT := 0.0;
    total_ratings INTEGER := 0;
    sum_ratings INTEGER := 0;
    m CONSTANT INTEGER := 5;
BEGIN
    -- Calculate global average for Bayesian formula
    SELECT AVG(rating), SUM(rating)
    INTO global_avg, total_ratings
    FROM user_book_ratings
    WHERE rating IS NOT NULL;

    IF global_avg IS NULL THEN
        global_avg := 0.0;
    END IF;

    -- INSERT: Add new rating to sum
    IF TG_OP = 'INSERT' THEN
        SELECT SUM(rating)
        INTO sum_ratings
        FROM user_book_ratings
        WHERE book_id = NEW.book_id;

        UPDATE books
        SET rating_count = COALESCE(sum_ratings, 0),
            average_rating = CASE
                WHEN sum_ratings > 0 THEN
                    ((m * global_avg) + COALESCE(sum_ratings, 0)) / (m + (SELECT COUNT(*) FROM user_book_ratings WHERE book_id = NEW.book_id))
                ELSE
                    0.0
                END
        WHERE book_id = NEW.book_id;

        RAISE NOTICE 'INSERT: Book %, Rating Count = %, Avg = %', NEW.book_id, COALESCE(sum_ratings, 0), (SELECT average_rating FROM books WHERE book_id = NEW.book_id);

    -- UPDATE: Adjust rating_count by the difference
    ELSIF TG_OP = 'UPDATE' THEN
        IF NEW.rating != OLD.rating THEN
            SELECT SUM(rating)
            INTO sum_ratings
            FROM user_book_ratings
            WHERE book_id = NEW.book_id;

            UPDATE books
            SET rating_count = COALESCE(sum_ratings, 0),
                average_rating = CASE
                    WHEN sum_ratings > 0 THEN
                        ((m * global_avg) + COALESCE(sum_ratings, 0)) / (m + (SELECT COUNT(*) FROM user_book_ratings WHERE book_id = NEW.book_id))
                    ELSE
                        0.0
                    END
            WHERE book_id = NEW.book_id;

            RAISE NOTICE 'UPDATE: Book %, Old Rating = %, New Rating = %, Rating Count = %, Avg = %', 
                         NEW.book_id, OLD.rating, NEW.rating, COALESCE(sum_ratings, 0), (SELECT average_rating FROM books WHERE book_id = NEW.book_id);
        END IF;

    -- DELETE: Subtract removed rating from sum
    ELSIF TG_OP = 'DELETE' THEN
        SELECT SUM(rating)
        INTO sum_ratings
        FROM user_book_ratings
        WHERE book_id = OLD.book_id;

        UPDATE books
        SET rating_count = COALESCE(sum_ratings, 0),
            average_rating = CASE
                WHEN sum_ratings > 0 THEN
                    ((m * global_avg) + COALESCE(sum_ratings, 0)) / (m + (SELECT COUNT(*) FROM user_book_ratings WHERE book_id = OLD.book_id))
                ELSE
                    0.0
                END
        WHERE book_id = OLD.book_id;

        RAISE NOTICE 'DELETE: Book %, Removed Rating = %, Rating Count = %, Avg = %', 
                     OLD.book_id, OLD.rating, COALESCE(sum_ratings, 0), (SELECT average_rating FROM books WHERE book_id = OLD.book_id);
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Recreate the trigger
DROP TRIGGER IF EXISTS trigger_update_bayesian_rating ON user_book_ratings;
CREATE TRIGGER trigger_update_bayesian_rating
AFTER INSERT OR UPDATE OR DELETE ON user_book_ratings
FOR EACH ROW EXECUTE FUNCTION update_bayesian_rating();
"""

# Function to initialize triggers
def init_triggers():
    with engine.connect() as connection:
        connection.execute(text(BAYESIAN_TRIGGER_FUNCTION))
        connection.commit()

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
    average_rating = Column(Float, default=0.0)  # Updated by trigger
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
    list_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    book_id = Column(Integer, ForeignKey("books.book_id"), primary_key=True)
    listed_date = Column(DateTime, default=lambda: datetime.now(datetime.UTC))

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

class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user1_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    messages = relationship("Message", back_populates="conversation")
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.conversation_id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User")
