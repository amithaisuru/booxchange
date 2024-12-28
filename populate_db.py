import pandas as pd
from sqlalchemy import create_engine

from models import DATABASE_URL


# Convert the authors column to the correct format
def format_authors(authors):
    if pd.isna(authors):
        return None
    return '{' + ','.join(authors.split(',')) + '}'

def populate_books():
    # Create a database engine
    engine = create_engine(DATABASE_URL)

    # Define the paths to your CSV files
    books_csv = "C:\\Users\\Amitha\\uni\\6th semester\\data management project\\book_recommendastion\\main\\final_datasets\\search_engine\\book_data.csv"

    # Read the CSV files into DataFrames
    books_df = pd.read_csv(books_csv)

    # Generate the mod_title column
    books_df['mod_title'] = books_df['title'].str.replace(r'[^a-zA-Z\s]', '', regex=True)
    books_df['mod_title'] = books_df['mod_title'].str.replace(r'\s+', ' ', regex=True)

    books_df = books_df.rename(columns={'ratings_count': 'rating_count'})
    books_df = books_df.rename(columns={'image_url': 'cover_image_url'})
    books_df['authors'] = books_df['authors'].apply(format_authors)

    #convert publication year to datetime
    books_df['publication_year'] = pd.to_datetime(books_df['publication_year'], errors='coerce')

    # Insert the data into the database
    books_df.to_sql('books', engine, if_exists='append', index=False)


    print("Data has been successfully inserted into the database.")

if __name__ == "__main__":
    populate_books()