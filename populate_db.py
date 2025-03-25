import bcrypt
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from crud import list_book
from models import DATABASE_URL, Book, User


# Convert the authors column to the correct format
def format_authors(authors):
    if pd.isna(authors):
        return None
    return '{' + ','.join(authors.split(',')) + '}'

def populate_books():
    # Create a database engine
    engine = create_engine(DATABASE_URL)

    # Define the paths to your CSV files
    books_csv = "C:\\Users\\Amitha\\uni\\6th semester\\data management project\\book_recommendastion\\main\\final_datasets\\book_data.csv"

    # Read the CSV files into DataFrames
    books_df = pd.read_csv(books_csv)

    # Generate the mod_title column
    books_df['mod_title'] = books_df['title'].str.replace(r'[^a-zA-Z\s]', '', regex=True)
    books_df['mod_title'] = books_df['mod_title'].str.replace(r'\s+', ' ', regex=True)
    books_df['mod_title'] = books_df['mod_title'].str.lower()

    books_df = books_df.rename(columns={'ratings_count': 'rating_count'})
    books_df = books_df.rename(columns={'image_url': 'cover_image_url'})
    books_df['authors'] = books_df['authors'].apply(format_authors)

    #convert publication year to datetime
    books_df['publication_year'] = pd.to_datetime(books_df['publication_year'], errors='coerce')

    # Insert the data into the database
    books_df.to_sql('books', engine, if_exists='append', index=False)


    print("Data has been successfully inserted into the database.")

def populate_cities():
    # Create a database engine
    engine = create_engine(DATABASE_URL)

    # Define the paths to your CSV files
    cities_csv = "C:\\Users\\Amitha\\uni\\6th semester\\data management project\\book_recommendastion\\main\\final_datasets\\city.csv"

    # Read the CSV files into DataFrames
    cities_df = pd.read_csv(cities_csv)

    # Insert the data into the database
    cities_df.to_sql('city', engine, if_exists='append', index=False)

    print("Data has been successfully inserted into the database.")

def populate_provinces():
    # Create a database engine
    engine = create_engine(DATABASE_URL)

    # Define the paths to your CSV files
    provinces_csv = "C:\\Users\\Amitha\\uni\\6th semester\\data management project\\book_recommendastion\\main\\final_datasets\\province.csv"

    # Read the CSV files into DataFrames
    provinces_df = pd.read_csv(provinces_csv)

    # Insert the data into the database
    provinces_df.to_sql('province', engine, if_exists='append', index=False)

    print("Data has been successfully inserted into the database.")

def populate_districts():
    # Create a database engine
    engine = create_engine(DATABASE_URL)

    # Define the paths to your CSV files
    districts_csv = "C:\\Users\\Amitha\\uni\\6th semester\\data management project\\book_recommendastion\\main\\final_datasets\\district.csv"

    # Read the CSV files into DataFrames
    districts_df = pd.read_csv(districts_csv)

    # Insert the data into the database
    districts_df.to_sql('district', engine, if_exists='append', index=False)

    print("Data has been successfully inserted into the database.")

def populate_users():
    # Create a database engine
    engine = create_engine(DATABASE_URL)

    # Define the paths to your CSV files
    users_csv = "C:\\Users\\Amitha\\uni\\6th semester\\data management project\\book_recommendastion\\main\\final_datasets\\user_data.csv"
    password = "password"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    

    # Read the CSV files into DataFrames
    user_df = pd.read_csv(users_csv)
    
    user_df['password_encrypted'] = hashed_password.decode('utf-8')


    # Insert the data into the database
    user_df.to_sql('users', engine, if_exists='append', index=False)

    print("Data has been successfully inserted into the database.")

def populate_province_district():
    # Create a database engine
    engine = create_engine(DATABASE_URL)

    # Define the paths to your CSV files
    province_district_csv = "C:\\Users\\Amitha\\uni\\6th semester\\data management project\\book_recommendastion\\main\\final_datasets\\province_district.csv"

    # Read the CSV files into DataFrames
    province_district_df = pd.read_csv(province_district_csv)

    # Insert the data into the database
    province_district_df.to_sql('province_district', engine, if_exists='append', index=False)

    print("Data has been successfully inserted into the database.")

def populate_district_city():
    # Create a database engine
    engine = create_engine(DATABASE_URL)

    # Define the paths to your CSV files
    district_city_csv = "C:\\Users\\Amitha\\uni\\6th semester\\data management project\\book_recommendastion\\main\\final_datasets\\district_city.csv"

    # Read the CSV files into DataFrames
    district_city_df = pd.read_csv(district_city_csv)

    # Insert the data into the database
    district_city_df.to_sql('district_city', engine, if_exists='append', index=False)

    print("Data has been successfully inserted into the database.")

def populate_user_book_ratings():
    # Create a database engine
    engine = create_engine(DATABASE_URL)

    # Define the paths to your CSV files
    user_book_rating_csv = "C:\\Users\\Amitha\\uni\\6th semester\\data management project\\book_recommendastion\\main\\datasets\\cleaned_datasets\\modified_interactions_with_rDates.csv"

    # Read the CSV files into DataFrames
    user_book_rating_df = pd.read_csv(user_book_rating_csv, nrows=100000)

    # Insert the data into the database
    user_book_rating_df.to_sql('user_book_ratings', engine, if_exists='append', index=False)

    print("Data has been successfully inserted into the database.")

def populate_listed_books():
    # Create a database engine
    engine = create_engine(DATABASE_URL)
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all user_ids and book_ids from the database
        user_ids = [user.user_id for user in session.query(User).all()]
        book_ids = [book.book_id for book in session.query(Book).all()]
        
        if not user_ids or not book_ids:
            print("Error: No users or books found in the database")
            return
        
        # Number of listings to create (you can adjust this number)
        num_listings = min(100, len(user_ids) * len(book_ids) // 2)  # Create reasonable amount of listings
        
        import random

        # Create random listings
        created_listings = set()  # To avoid duplicates
        for _ in range(num_listings):
            user_id = random.choice(user_ids)
            book_id = random.choice(book_ids)
            
            # Check for duplicates since user_id and book_id form a composite key
            if (user_id, book_id) not in created_listings:
                try:
                    # Use the list_book function from crud.py
                    list_book(session, user_id, book_id)
                    created_listings.add((user_id, book_id))
                except Exception as e:
                    print(f"Error listing book {book_id} for user {user_id}: {str(e)}")
                    session.rollback()
                    continue
        
        # Commit all changes
        session.commit()
        print(f"Successfully created {len(created_listings)} book listings in the database.")
        
    except Exception as e:
        print(f"Error in populate_listed_books: {str(e)}")
        session.rollback()
        
    finally:
        session.close()

if __name__ == "__main__":
    # populate_books()
    # populate_cities()
    # populate_provinces()
    # populate_districts()
    # populate_province_district()
    # populate_district_city()
    # populate_users()
    # populate_listed_books()
    populate_user_book_ratings()