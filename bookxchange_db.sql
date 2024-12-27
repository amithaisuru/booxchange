-- Create the database
CREATE DATABASE bookxchange_db;

-- Connect to the database
\c bookxchange_db;

-- Create table: users
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    birth_year DATE NOT NULL,
    password_encrypted VARCHAR NOT NULL,
    age INT NOT NULL
);

-- Create table: books
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    title_without_series VARCHAR,
    mod_title VARCHAR NOT NULL,
    isbn VARCHAR,
    language_code VARCHAR,
    publication_year DATE,
    rating_count INT,
    average_rating FLOAT,
    authors TEXT[],
    cover_image_url VARCHAR
);

-- Create table: user_book_ratings
CREATE TABLE user_book_ratings (
    user_id INT REFERENCES users(user_id),
    book_id INT REFERENCES books(book_id),
    rating INT NOT NULL,
    rated_date DATE,
    PRIMARY KEY (user_id, book_id)
);

-- Create table: listed_books
CREATE TABLE listed_books (
    user_id INT REFERENCES users(user_id),
    book_id INT REFERENCES books(book_id),
    listed_date DATE NOT NULL,
    PRIMARY KEY (user_id, book_id)
);

-- Create table: requested_books
CREATE TABLE requested_books (
    user_id INT REFERENCES users(user_id),
    book_id INT REFERENCES books(book_id),
    requested_date DATE NOT NULL,
    PRIMARY KEY (user_id, book_id)
);
